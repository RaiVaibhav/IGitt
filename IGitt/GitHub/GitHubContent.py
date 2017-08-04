"""
This contains the Content implementation for GitHub.
"""
from base64 import b64encode

from IGitt.GitHub import GitHubMixin, GitHubToken, get, delete, put
from IGitt.Interfaces.Content import Content


class GitHubContent(Content, GitHubMixin):
    """
    This class represents a content on GitHub
    """
    def __init__(self,  token: GitHubToken, repository: str, path: str):
        self._token = token
        self._repository = repository
        self._url = '/repos/' + repository + '/contents/' + path

    def get_content(self, ref='master'):
        data = {
            'path': self._url,
            'ref': ref
        }
        self.data = get(token=self._token, url=self._url, params=data)

    def delete(self, message: str, branch: (str, None)=None):

        if branch is None:
            branch = 'master'

        data = {
            'path': self._url,
            'message' : message,
            'sha': self.data['sha'],
            'branch': branch
        }
        delete(token=self._token, url=self._url, params=data)

    def update(self, message: str, content: str, branch: (str, None)=None):

        content = b64encode(content.encode()).decode('utf-8')

        if branch is None:
            branch = 'master'

        data = {
            'path': self._url,
            'message': message,
            'sha': self.data['sha'],
            'branch': branch,
            'content' : content
        }
        put(token=self._token, url=self._url, data=data)