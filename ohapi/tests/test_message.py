import os
import vcr
import unittest
import ohapi.api as api

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir='ohapi/cassettes',
                 filter_query_parameters=['access_token'])

class test_message(unittest.TestCase):
    TESTING_KWARGS_MESSAGE= {
        'subject': 'test_subject',
        'message': 'test_message',
        'access_token': 'access_token'
    }
    def setUp(self):
        pass
    
    @my_vcr.use_cassette()
    def test_message_valid_access_token(self):
        response = api.message(**self.TESTING_KWARGS_MESSAGE)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_expired_access_token(self):
        response = api.message(**self.TESTING_KWARGS_MESSAGE)
        assert response.json() == {"detail":"Expired token."}
    
    @my_vcr.use_cassette()
    def test_message_invalid_access_token(self):
        response = api.message(**self.TESTING_KWARGS_MESSAGE)
        assert response.json() == {"detail":"Invalid token."}
    
    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_none(self):
        response = api.message(all_members=True, **self.TESTING_KWARGS_MESSAGE)
        self.assertEqual(response.status_code, 200)

    @my_vcr.use_cassette()
    def test_message_all_members_true_project_member_id_not_none(self):
        self.assertRaises(Exception,api.message, all_members=True,
                          project_member_ids=['abcdef','sdf'],
                          **self.TESTING_KWARGS_MESSAGE)

    @my_vcr.use_cassette()
    def test_message_all_members_false_project_member_id_not_none_invalid_char(self):
        response = api.message(project_member_ids=['abcdef','test'],
                               **self.TESTING_KWARGS_MESSAGE)
        assert response.json() == {"errors":{"project_member_ids":
                ["Project member IDs are always 8 digits long."]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_project_member_id_not_none_invalid_digit(self):
        response = api.message(project_member_ids=['invalidPMI1',
                               'invalidPMI2'],
                               **self.TESTING_KWARGS_MESSAGE)
        assert response.json() == {"errors":{"project_member_ids":
                                  ["Invalid project member ID(s): invalidPMI2"]}}

    @my_vcr.use_cassette()
    def test_message_all_members_false_project_member_id_not_none_valid(self):
        response = api.message(project_member_ids=['validPMI1','validPMI1'],
                               **self.TESTING_KWARGS_MESSAGE)
        self.assertEqual(response.status_code, 200)
