import unittest
import os
import datetime

import vcr

from IGitt.GitHub.GitHubMergeRequest import GitHubMergeRequest

my_vcr = vcr.VCR(match_on=['method', 'scheme', 'host', 'port', 'path'],
                 filter_query_parameters=['access_token'],
                 filter_post_data_parameters=['access_token'])


class TestGitHubMergeRequest(unittest.TestCase):

    def setUp(self):
        self.mr = GitHubMergeRequest(os.environ.get('GITHUB_TEST_TOKEN', ''),
                                     'gitmate-test-user/test', 7)

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_base.yaml')
    def test_base(self):
        self.assertEqual(self.mr.base.sha,
                         '674498fd415cfadc35c5eb28b8951e800f357c6f')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_head.yaml')
    def test_head(self):
        self.assertEqual(self.mr.head.sha,
                         'f6d2b7c66372236a090a2a74df2e47f42a54456b')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_desc.yaml')
    def test_description(self):
        self.assertEqual(self.mr.description, '')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_title.yaml')
    def test_title(self):
        self.mr.title = 'changed title'
        self.assertEqual(self.mr.title, 'changed title')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_basebranchname.yaml')
    def test_base_branch_name(self):
        self.assertEqual(self.mr.base_branch_name, 'master')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_headbranchname.yaml')
    def test_head_branch_name(self):
        self.assertEqual(self.mr.head_branch_name, 'gitmate-test-user-patch-2')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_commits.yaml')
    def test_commits(self):
        self.assertEqual([commit.sha for commit in self.mr.commits],
                         ['f6d2b7c66372236a090a2a74df2e47f42a54456b'])

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_repository.yaml')
    def test_repository(self):
        self.assertEqual(self.mr.repository.full_name,
                         'gitmate-test-user/test')

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_diffstat.yaml')
    def test_diffstat(self):
        self.assertEqual(self.mr.diffstat, (2, 0))

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_time.yaml')
    def test_time(self):
        self.assertEqual(self.mr.created, datetime.datetime(
            2016, 1, 24, 19, 47, 19))
        self.assertEqual(self.mr.updated, datetime.datetime(
            2017, 6, 14, 10, 34, 40))

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_affected_files.yaml')
    def test_affected_files(self):
        self.assertEqual(self.mr.affected_files, {'README.md'})

    def test_number(self):
        self.assertEqual(self.mr.number, 7)

    @my_vcr.use_cassette('tests/GitHub/cassettes/github_merge_request_states.yaml')
    def test_change_state(self):
        self.mr.close()
        self.assertEqual(self.mr.state, 'closed')
        self.mr.reopen()
        self.assertEqual(self.mr.state, 'open')
