import os

_dir = os.path.split(os.path.realpath(__file__))[0]

defaults = {
    'channel': 'devoted_chat',
    'cmd_prefix':  '$',
    'config_file': os.path.join(_dir, 'tdt.rc'),
    'token_file':  os.path.join(_dir, 'token.txt'),
    'roast_file':  os.path.join(_dir, 'roasts.txt'),
    'nemeses':     'UnknownElectro#1397',
}


class Parameters(dict):
    def __init__(self, copy=None, config=None, token=None, roasts=None):
        super().__init__()
        if copy is not None:
            self.update(copy)
        self['roasts'] = []
        self.read_config(config)
        self.read_token(token)
        self.read_roasts(roasts)

    def __call__(self, key, default=None):
        return self.get(key, default)

    def dget(self, key, default=None):
        return self.get(key, defaults.get(key, default))

    def read_config(self, fn=None):
        if fn is None:
            fn = self.dget('config_file')
        if not fn:
            return
        try:
            with open(fn, 'r') as f:
                lines = filter(None, [i.split('#')[0].strip() for i in f.readlines()])
        except IOError:
            return
        self.update(dict([l.split('=') for l in lines]))

    def read_token(self, fn=None):
        if fn is None:
            fn = self.dget('token_file')
        try:
            with open(fn, 'r') as f:
                lines = filter(None, [i.split('#')[0].strip() for i in f.readlines()])
                lines = list(lines)
        except IOError:
            self['token'] = fn
            return self['token']
        if len(lines) != 1:
            raise ValueError('Token file not properly formatted.')
        self['token'] = lines[0]
        return self['token']

    def read_roasts(self, fn=None, add=True):
        if fn is None:
            fn = self.dget('roast_file')
        with open(fn, 'r') as f:
            lines = list(filter(None, [i.strip() for i in f.readlines()]))
        if add:
            self['roasts'].extend(lines)
        else:
            self['roasts'] = lines
        return self['roasts']


rc = Parameters(copy=defaults)
