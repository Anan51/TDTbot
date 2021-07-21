import git
import os
import datetime
import humanize
import pytz

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


def git_log_items(repo=None, look_back=None):
    """Returns a list of formatted git log items. "repo" defaults to this one.
    "look_back" (datetime) defaults to 7 days ago"""
    if repo is None:
        repo = own_repo
    if look_back is None:
        look_back = datetime.timedelta(days=7)
    if isinstance(look_back, datetime.timedelta):
        now = pytz.utc.localize(datetime.datetime.utcnow())
        look_back = now - abs(look_back)
    # only print items from the last week
    items = [i for i in repo.iter_commits() if i.committed_datetime > look_back]

    def dt(i):
        """Format timestamp to human readable string"""
        return humanize.naturaltime(now - i.committed_datetime)

    fmt = "{:}: {:} <{:}> [{:}]"
    return [fmt.format(dt(i), i.message.strip(), i.author.name, i.hexsha[:7])
            for i in items]


def last_updated(repo=None):
    if repo is None:
        repo = own_repo
    return datetime.datetime.fromtimestamp(repo.head.committed_date)
