from collections import OrderedDict
import json
import logging
import os
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from humanfriendly import format_size, parse_size
import requests


MAX_FILE_DEFAULT = parse_size('128m')
OH_BASE_URL = os.getenv('OHAPI_OH_BASE_URL', 'https://www.openhumans.org/')


class SettingsError(Exception):
    pass


def oauth2_auth_url(redirect_uri=None, client_id=None, base_url=OH_BASE_URL):
    """
    Returns an OAuth2 authorization URL for a project, given Client ID. This
    function constructs an authorization URL for a user to follow.
    The user will be redirected to Authorize Open Humans data for our external
    application. An OAuth2 project on Open Humans is required for this to
    properly work. To learn more about Open Humans OAuth2 projects, go to:
    https://www.openhumans.org/direct-sharing/oauth2-features/

    :param redirect_uri: This field is set to `None` by default. However, if
        provided, it appends it in the URL returned.
    :param client_id: This field is also set to `None` by default however,
        is a mandatory field for the final URL to work. It uniquely identifies a
        given OAuth2 project.
    :param base_url: It is this URL `https://www.openhumans.org`
    """
    if not client_id:
        client_id = os.getenv('OHAPI_CLIENT_ID')
        if not client_id:
            raise SettingsError(
                "Client ID not provided! Provide client_id as a parameter, "
                "or set OHAPI_CLIENT_ID in your environment.")
    params = OrderedDict([
        ('client_id', client_id),
        ('response_type', 'code'),
    ])
    if redirect_uri:
        params['redirect_uri'] = redirect_uri

    auth_url = urlparse.urljoin(
        base_url, '/direct-sharing/projects/oauth2/authorize/?{}'.format(
            urlparse.urlencode(params)))

    return auth_url


def oauth2_token_exchange(client_id, client_secret, redirect_uri,
                          base_url=OH_BASE_URL, code=None, refresh_token=None):
    """
    Exchange code or refresh token for a new token and refresh token.
    """
    if not (code or refresh_token) or (code and refresh_token):
        raise ValueError("Either code or refresh_token must be specified.")
    if code:
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code,
        }
    elif refresh_token:
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
    token_url = urlparse.urljoin(base_url, '/oauth2/token/')
    req = requests.post(
        token_url, data=data,
        auth=requests.auth.HTTPBasicAuth(client_id, client_secret))
    data = req.json()
    return data


def get_page(url):
    """
    Get a single page of results.
    """
    response = requests.get(url)
    if not response.status_code == 200:
        err_msg = 'API response status code {}'.format(response.status_code)
        if 'detail' in response.json():
            err_msg = err_msg + ": {}".format(response.json()['detail'])
        raise Exception(err_msg)
    data = response.json()
    return data


def get_all_results(starting_page):
    """
    Given starting API query for Open Humans, iterate to get all results.
    """
    logging.info('Retrieving all results for {}'.format(starting_page))
    page = starting_page
    results = []

    while True:
        logging.debug('Getting data from: {}'.format(page))
        data = get_page(page)
        logging.debug('JSON data: {}'.format(data))
        results = results + data['results']

        if data['next']:
            page = data['next']
        else:
            break

    return results


def exchange_oauth2_member(access_token, base_url=OH_BASE_URL):
    url = urlparse.urljoin(
        base_url,
        '/api/direct-sharing/project/exchange-member/?{}'.format(
            urlparse.urlencode({'access_token': access_token})))
    member_data = get_page(url)
    logging.debug('JSON data: {}'.format(member_data))
    return member_data


def upload_file(target_filepath, metadata, access_token, base_url=OH_BASE_URL,
                remote_file_info=None, project_member_id=None,
                max_bytes=MAX_FILE_DEFAULT):
    """
    Upload a file.
    """
    filesize = os.stat(target_filepath).st_size
    if filesize > max_bytes:
        logging.info('Skipping {}, {} > {}'.format(
            target_filepath, format_size(filesize), format_size(max_bytes)))
        raise ValueError("Maximum file size exceeded")

    if remote_file_info:
        response = requests.get(remote_file_info['download_url'], stream=True)
        remote_size = int(response.headers['Content-Length'])
        if remote_size == filesize:
            logging.info('Skipping {}, remote exists with matching name and '
                         'file size'.format(target_filepath))
            raise ValueError("Remote exist with matching name and file size")

    url = urlparse.urljoin(
        base_url, '/api/direct-sharing/project/files/upload/?{}'.format(
            urlparse.urlencode({'access_token': access_token})))

    logging.info('Uploading {} ({})'.format(
        target_filepath, format_size(filesize)))

    if not(project_member_id):
        response = exchange_oauth2_member(access_token)
        project_member_id = response['project_member_id']

    return requests.post(url, files={'data_file': open(target_filepath, 'rb')},
                         data={'project_member_id': project_member_id,
                               'metadata': json.dumps(metadata)})

    logging.info('Upload complete: {}'.format(target_filepath))


def delete_file(access_token, project_member_id, base_url=OH_BASE_URL,
                file_basename=None, file_id=None, all_files=False):
    """
    Delete project member files by file_basename, file_id, or all_files.
    """
    url = urlparse.urljoin(
        base_url, '/api/direct-sharing/project/files/delete/?{}'.format(
            urlparse.urlencode({'access_token': access_token})))
    data = {'project_member_id': project_member_id}
    if file_basename and not (file_id or all_files):
        data['file_basename'] = file_basename
    elif file_id and not (file_basename or all_files):
        data['file_id'] = file_id
    elif all_files and not (file_id or file_basename):
        data['all_files'] = True
    else:
        raise ValueError(
            "One (and only one) of the following must be specified: "
            "file_basename, file_id, or all_files is set to True.")
    r = requests.post(url, data=data)
    return r


# Alternate names for the same functions.
def delete_files(*args, **kwargs):
    return delete_file(*args, **kwargs)


def message(subject, message, access_token, all_members=False,
            project_member_ids=None, base_url=OH_BASE_URL):
    """
    send messages.
    """
    url = urlparse.urljoin(
        base_url, '/api/direct-sharing/project/message/?{}'.format(
            urlparse.urlencode({'access_token': access_token})))
    if not(all_members) and not(project_member_ids):
        return requests.post(url, data={'subject': subject,
                                        'message': message})
    elif all_members and project_member_ids:
        raise ValueError(
            "One (and only one) of the following must be specified: "
            "project_members_id or all_members is set to True.")
    else:
        return requests.post(url, data={
                             'all_members': all_members,
                             'project_member_ids': project_member_ids,
                             'subject': subject,
                             'message': message})
