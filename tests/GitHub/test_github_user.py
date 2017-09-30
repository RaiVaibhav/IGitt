import os

from IGitt.GitHub import GitHubToken
from IGitt.GitHub.GitHubUser import GitHubUser

from tests import IGittTestCase


class GitHubUserTest(IGittTestCase):

    def setUp(self):
        self.token = GitHubToken(os.environ.get('GITHUB_TEST_TOKEN', ''))
        self.sils = GitHubUser(self.token, 'sils')
        self.user = GitHubUser(self.token)

    def test_user_url(self):
        self.assertEqual(self.sils.url, 'https://api.github.com/users/sils')

    def test_user_id(self):
        self.assertEqual(self.sils.identifier, 5716520)
        self.assertEqual(self.user.identifier, 16681030)

    def test_username(self):
        self.assertEqual(self.sils.username, 'sils')
        self.assertEqual(self.user.username, 'gitmate-test-user')
