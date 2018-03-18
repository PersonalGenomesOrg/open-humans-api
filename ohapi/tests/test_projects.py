from unittest import TestCase
from ohapi.projects import OHProject
import vcr

parameter_defaults = {
    'MEMBER_DATA': {"data": [{"basename": 1}]},
    'TARGET_MEMBER_DIR': 'targetmemberdir',
    'MAX_SIZE': 'max_size',
}

try:
    from _config_params_api import params
    for param in params:
        parameter_defaults[param] = params[param]
except ImportError:
    pass

for param in parameter_defaults:
    locals()[param] = parameter_defaults[param]


FILTERSET = [('access_token', 'ACCESSTOKEN'), ('client_id', 'CLIENTID'),
             ('client_secret', 'CLIENTSECRET'), ('code', 'CODE'),
             ('refresh_token', 'REFRESHTOKEN'),
             ('invalid_access_token', 'INVALIDACCESSTOKEN')]

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_headers=[('Authorization', 'XXXXXXXX')],
                 filter_query_parameters=FILTERSET,
                 filter_post_data_parameters=FILTERSET)


class ProjectsTest(TestCase):

    def setUp(self):
        pass

    def test_get_member_file_data_member_data_none(self):
        response = OHProject._get_member_file_data(member_data=MEMBER_DATA)
        self.assertEqual(response, {1: {'basename': 1}})
