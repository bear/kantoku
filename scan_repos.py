#!/usr/bin/env python

"""
:copyright: (c) 2014 by Mike Taylor
:license: MIT, see LICENSE for more details.

Given a list of GitHub organizations, verify...
  - web hooks for a repo are present
  - there are no duplicate web hooks
"""

from __future__ import print_function

import os, sys
import json
import argparse

from github import Github, Label
from bearlib.config import Config

#TODO add issue label validation 
#TODO add service hook validation

def info(msg):
    print(msg)

def error(msg):
    print(msg, file=sys.stderr)

def generateHookConfig(hookDefinition):
    result = {}

    for key in ('url', 'content_type', 'insecure_ssl', 'secret'):
        if key in hookDefinition:
            result[key] = hookDefinition[key]

    if 'content_type' not in result:
        result['content_type'] = 'json'
    if 'insecure_ssl' not in result:
        result['insecure_ssl'] = '0'

    return result

def checkHooks(org, repo, hookList, verifyOnly=False):
    hooks = []
    dupes = []
    for hItem in hookList:
        hooks.append(hItem.url)

    for hook in repo.get_hooks():
        if hook.name.lower() == 'web' and hook.config['url'] in hooks:
            hooks.remove(hook.config['url'])
        if hook.url in dupes:
            error('%s %s %s %s duplicate hook' % (org.name, repo.name, hook.name, hook.id))
        dupes.append(hook.url)

    if len(hooks) > 0:
        for hItem in hookList:
            if hItem.url in hooks:
                if verifyOnly:
                    error('%s %s %s missing web hook' % (org.name, repo.name, hItem.url))
                else:
                    c = generateHookConfig(hItem)
                    h = repo.create_hook('web', c, events=hItem.events, active=True)
                    info('%s %s %s created web hook' % (org.name, repo.name, hItem.url))

def checkLabels(org, repo, labelList, verifyOnly=False):
    labels = []
    dupes  = []
    for hLabel in labelList:
        labels.append(hLabel.name)

    for label in repo.get_labels():
            # info('%s %s %s labels wiped' % (org.name, repo.name, label.name))
            # label.delete()
        if label.name in labels:
            labels.remove(label.name)

    if len(labels) > 0:
        for hLabel in labelList:
            if hLabel.name in labels:
                if verifyOnly:
                    error('%s %s %s missing label' % (org.name, repo.name, hLabel.name))
                else:
                    h = repo.create_label(hLabel.name, hLabel.color)
                    info('%s %s %s created label' % (org.name, repo.name, hLabel.name))

#
# Configuration Example
#
# {
#     "auth_token": "github_auth_token",
#     "orgs": [ { "org": "AmpersandJS",
#                 "exclude_repos": [ "ubersicht" ],
#                 "hooks": [ { "url": "http://127.0.0.1:4242/github/callback",
#                              "events": ["*"]
#                            }
#                          ],
#                 "labels": []
#               }
#             ]
# }
#

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',  default='./kantoku.cfg')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--noop',    action='store_true')

    args = parser.parse_args()
    cfg  = Config()
    cfg.fromJson(args.config)

    if cfg.auth_token is None:
        error('Unable to load configuration file %s' % args.config)
    else:
        gh = Github(cfg.auth_token)

        for oItem in cfg.orgs:
            org = gh.get_organization(oItem.org)

            for repo in org.get_repos():
                if args.verbose:
                    info('%s %s' % (org.name, repo.name))

                if repo.name not in oItem.exclude_repos:
                    checkHooks(org, repo, oItem.hooks, verifyOnly=args.noop)
                    checkLabels(org, repo, oItem.labels, verifyOnly=args.noop)
