#!/usr/bin/env python

"""
:copyright: (c) 2014 by Mike Taylor
:license: MIT, see LICENSE for more details.

Config class that can be accessed using attributes.
Has helper methods to load from etcd and json.

Can be initialized using a dictionary.
"""

import os, sys
import json
import etcd


# derived from https://stackoverflow.com/a/3031270
class Config(dict):
    marker = object()
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            self.fromDict(value)
        else:
            raise TypeError, 'expected dict'

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, Config):
            value = Config(value)
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict) and not isinstance(value, Config):
                    items.append(Config(item))
                else:
                    items.append(item)
            value = items
        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        found = self.get(key, Config.marker)
        if found is Config.marker:
            found = Config()
            dict.__setitem__(self, key, found)
        return found

    __setattr__ = __setitem__
    __getattr__ = __getitem__

    def fromDict(self, d):
        if isinstance(d, dict):
            for key in d:
                self.__setitem__(key, d[key])

    def _readEtcd(self, etcdClient, base, parent=None):
        result = {}
        if parent is None:
            n = len(base)
        else:
            n = len(parent) + 1

        items = etcdClient.read(base, recursive=False)
        for leaf in items.leaves:
            key = leaf.key[n:]
            if leaf.dir:
                value = self._readEtcd(etcdClient, leaf.key, leaf.key)
            else:
                value = leaf.value
            result[key] = value

        return result

    def fromEtcd(self, host='127.0.0.1', port=4001, base='/'):
        e = etcd.Client(host=host, port=port, allow_redirect=False, allow_reconnect=False)
        r = self._readEtcd(e, base)
        self.fromDict(r)

    def fromJson(self, configFilename):
        if os.path.exists(configFilename):
            with open(configFilename, 'r') as h:
                r = json.load(h)
                self.fromDict(r)
