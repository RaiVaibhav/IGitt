import os

from IGitt.GitHub import GitHubToken
from IGitt.GitHub.GitHubOrganization import GitHubOrganization

from tests import IGittTestCase


class GitHubOrganizationTest(IGittTestCase):

    def setUp(self):
        self.token = GitHubToken(os.environ.get('GITHUB_TEST_TOKEN', ''))
        self.org = GitHubOrganization(self.token, 'gitmate-test-org')
        self.user = GitHubOrganization(self.token, 'gitmate-test-user')

    def test_billable_users(self):
        # sils, nkprince007, gitmate-test-user
        self.assertEqual(self.org.billable_users, 3)
        self.assertEqual(self.user.billable_users, 1) # gitmate-test-user

    def test_owners(self):
        self.assertEqual({o.username for o in self.org.owners},
                         {'nkprince007', 'sils'})
        self.assertEqual({m.username for m in self.org.masters},
                         {'nkprince007', 'sils'})
        self.assertEqual({o.username for o in self.user.owners},
                         {'gitmate-test-user'})
        self.assertEqual({m.username for m in self.user.masters},
                         {'gitmate-test-user'})

    def test_organization(self):
        self.assertEqual(self.org.url,
                         'https://api.github.com/orgs/gitmate-test-org')
        self.assertEqual(self.org.web_url,
                         'https://github.com/gitmate-test-org')
        self.assertEqual(self.user.url,
                         'https://api.github.com/orgs/gitmate-test-user')
        self.assertEqual(self.user.web_url,
                         'https://github.com/gitmate-test-user')

    def test_description(self):
        org = GitHubOrganization(self.token, 'github')
        self.assertEqual(org.description, 'How people build software.')
        self.assertEqual(self.org.description, '')

    def test_suborgs(self):
        self.assertEqual(self.org.suborgs, set())

    def test_repositories(self):
        self.assertEqual({r.full_name for r in self.org.repositories},
                         {'gitmate-test-org/test', 'gitmate-test-org/test-1'})
