import os
import vcr
import unittest
import ohapi.api as api

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes', 
                 filter_query_parameters=['access_token'])
class test_get_page(unittest.TestCase):

    def setUp(self):
        self.test_access_token = os.environ.get("access_token",'access_token')

    @my_vcr.use_cassette()
    def test_get_page_with_results(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
                'exchange-member/?access_token={}'.format(self.test_access_token))
        response = api.get_page(url)
        self.assertEqual(response['project_member_id'], 'PMI')
        self.assertEqual(response['message_permission'], True)
        self.assertEqual(response['data'], [])
        self.assertEqual(response['username'], 'test_user')
        self.assertEqual(response['sources_shared'], [])
        self.assertEqual(response['created'],'created_date_time')

    @my_vcr.use_cassette()
    def test_get_page_invalid_access_token(self):
        url = ('https://www.openhumans.org/api/direct-sharing/project/'
                'exchange-member/?access_token={}'.format("invalid_token"))
        self.assertRaises(Exception,api.get_page,url)  