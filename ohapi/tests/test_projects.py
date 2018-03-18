from unittest import TestCase
from ohapi.projects import OHProject

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


class ProjectsTest(TestCase):

    def setUp(self):
        pass

    def test_get_member_file_data_member_data_none(self):
        response = OHProject._get_member_file_data(member_data=MEMBER_DATA)
        self.assertEqual(response, {1: {'basename': 1}})
