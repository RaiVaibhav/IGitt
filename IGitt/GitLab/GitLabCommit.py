"""
Contains the abstraction for a commit in GitLab.
"""
from urllib.parse import quote_plus

from IGitt import ElementDoesntExistError
from IGitt.GitHub.GitHubCommit import get_diff_index
from IGitt.GitLab import get, post, GitLabMixin
from IGitt.GitLab.GitLabRepository import GitLabRepository
from IGitt.Interfaces.Commit import Commit
from IGitt.Interfaces.CommitStatus import Status, CommitStatus

GL_STATE_TRANSLATION = {Status.RUNNING: 'running',
                        Status.CANCELED: 'canceled',
                        Status.FAILED: 'failed',
                        Status.PENDING: 'pending',
                        Status.SUCCESS: 'success'}
INV_GL_STATE_TRANSLATION = {val: key for key, val
                            in GL_STATE_TRANSLATION.items()}


class GitLabCommit(Commit, GitLabMixin):
    """
    Represents a commit on GitLab.
    """

    def __init__(self, oauth_token: str, repository: str, sha: (str, None),
                 branch: (str, None)=None):
        """
        Creates a new GitLabCommit object.

        :param oauth_token: A valid OAuth token for authentication.
        :param repository: The full repository name.
        :param sha: The full commit SHA, if None given provide a branch.
        :param branch: A branch name if SHA is unavailable. Note that lazy
                       loading won't work in that case.
        """
        assert sha or branch, "Either full SHA or branch name has to be given!"
        self._token = oauth_token
        self._repository = repository
        self._sha = sha
        self._branch = branch
        self._url = '/projects/{id}/repository/commits/{sha}'.format(
            id=quote_plus(repository), sha=sha if sha else branch)

    @property
    def sha(self):
        """
        Retrieves the SHA of the commit:

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '674498')
        >>> commit.sha
        '674498'

        :return: A string holding the SHA of the commit.
        """
        return self._sha if self._sha else self.data['id']

    @property
    def repository(self):
        """
        Retrieves the repository that holds this commit.

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '3fc4b86')
        >>> commit.repository.full_name
        'gitmate-test-user/test'

        :return: A usable Repository instance.
        """
        return GitLabRepository(self._token, self._repository)

    @property
    def parent(self):
        """
        Retrieves the parent commit. In case of a merge commit the first parent
        will be returned.

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '3fc4b86')
        >>> commit.parent.sha
        '674498fd415cfadc35c5eb28b8951e800f357c6f'

        :return: A Commit object.
        """
        return GitLabCommit(self._token, self._repository,
                            self.data['parent_ids'][0])

    def get_statuses(self) -> {CommitStatus}:
        """
        Retrieves the all commit statuses.

        :return: A (frozen)set of CommitStatus objects.
        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        # rebuild the url with full sha because gitlab doesn't work that way
        url = '/projects/{repo}/repository/commits/{sha}/statuses'.format(
            repo=quote_plus(self._repository), sha=self.sha)
        statuses = get(self._token, url)

        # Only the first of each context is the one we want
        result = set()
        contexts = set()
        for status in statuses:
            if status['name'] not in contexts:
                result.add(CommitStatus(
                    INV_GL_STATE_TRANSLATION[status['status']],
                    status['description'], status['name'],
                    status['target_url']))
                contexts.add(status['name'])

        return result

    def set_status(self, status: CommitStatus):
        """
        Adds the given status to the commit.

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '3fc4b860')
        >>> status = CommitStatus(Status.FAILED, 'Theres a problem',
        ...                       'gitmate/test')
        >>> commit.set_status(status)
        >>> commit.get_statuses().pop().description
        'Theres a problem'

        If a status with the same context already exists, it will be bluntly
        overridden:

        >>> status.status = Status.SUCCESS
        >>> status.description = "Theres no problem"
        >>> commit.set_status(status)
        >>> len(commit.get_statuses())
        1
        >>> commit.get_statuses().pop().description
        'Theres no problem'

        :param status: The CommitStatus to set to this commit.
        :raises RuntimeError: If something goes wrong (network, auth...).
        """
        data = {'state': GL_STATE_TRANSLATION[status.status],
                'target_url': status.url, 'description': status.description,
                'name': status.context}
        status_url = '/projects/{repo}/statuses/{sha}'.format(
            repo=quote_plus(self._repository), sha=self.sha)
        post(self._token, status_url, data)

    def get_patch_for_file(self, filename: str):
        r"""
        Retrieves the unified diff for the commit.

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '3fc4b86')
        >>> assert (commit.get_patch_for_file('README.md') ==
        ...         '--- a/README.md\n+++ b/README.md\n@@ -1,2 +1,4 @@\n '
        ...         '# test\n a test repo\n+\n+a tst pr\n')

        But only if it exists!

        >>> commit.get_patch_for_file('IDONTEXISTFILE')
        Traceback (most recent call last):
         ...
        IGitt.ElementDoesntExistError: The file does not exist.

        :param filename: The file to retrieve patch for.
        :return: A string containing the patch.
        :raises ElementDoesntExistError: If the given filename does not exist.
        """
        diff = get(self._token, self._url + '/diff')

        for patch in diff:
            if filename in (patch['new_path'], patch['old_path']):
                return patch['diff']

        raise ElementDoesntExistError('The file does not exist.')

    def comment(self, message: str, file: (str, None)=None,
                line: (int, None)=None, mr_number: int=None):
        """
        Places a comment on the commit.

        >>> from os import environ
        >>> commit = GitLabCommit(environ['GITLAB_TEST_TOKEN'],
        ...                       'gitmate-test-user/test', '3fc4b86')

        So this line places a comment on the bottom of the commit,
        not associated to any particular piece of code:

        >>> commit.comment("An issue is here!")

        However, we can also comment on a particular file and line, if that is
        included in the diff:

        >>> commit.comment("Here in line 4, there's a spelling mistake!",
        ...                'README.md', 4)

        If you supply the ``pr_number`` argument, the comment will appear in
        the review UI of that pull request:

        >>> commit.comment("Here in line 4, there's a spelling mistake!",
        ...                'README.md', 4, mr_number=7)

        Beat that! Of course, there's a lot of error handling. If you give the
        wrong file, the comment will appear below the commit with a note about
        the commit, file and line:

        >>> commit.comment("Oh, this'll end up below!!", 'READMENOT.md', 4)

        Also if the line isn't contained in the diff GitLab won't accept that
        and it'll also end up below - sorry!

        >>> commit.comment("Oh, this'll too end up below!!", 'README.md', 8)

        If you give a pull request, the comment will appear on the PR instead:

        >>> commit.comment("Oh, this'll too end up on the PR.",
        ...                'README.md', 8, mr_number=7)

        :param message: The body of the comment.
        :param file: The file to place the comment, relative to repo root.
        :param line: The line in the file in the comment or None.
        :param mr_number: The iid of a merge request if this should end up in
                          the discussions UI of the merge request.
        """
        data = {'note': message, 'line_type': 'new'}

        if file is not None and line is not None:
            try:
                patch = self.get_patch_for_file(file)
                index = get_diff_index(patch, line)
                if index:  # Else, fallback to comment below file
                    data['line'] = index
                    data['path'] = file
            except ElementDoesntExistError:
                pass  # Fallback to comment below the file

        if 'line' not in data:
            file_str = '' if file is None else ', file ' + file
            line_str = '' if line is None else ', line ' + str(line)
            data['note'] = ('Comment on ' + self.sha + file_str + line_str +
                            '.\n\n' + data['note'])

        if mr_number is None:  # comments directly on the commit
            post(self._token, self._url + '/comments', data)
        else:  # comments on the merge request
            data['body'] = data['note']  # because gitlab is stupid
            post(self._token,
                 '/projects/{id}/merge_requests/{mr_iid}/notes'.format(
                     id=quote_plus(self._repository), mr_iid=mr_number), data)