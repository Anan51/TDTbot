import git
import os

directory = os.path.split(os.path.realpath(__file__))[0]
own_repo = git.Repo(directory)


def update(repo=None):
    """Update TDTbot module with a git pull... to git good."""
    if repo is None:
        repo = own_repo
    elif hasattr(repo, 'lower'):
        if os.path.isdir(repo):
            repo = git.Repo(repo)
    repo.remote().pull()
