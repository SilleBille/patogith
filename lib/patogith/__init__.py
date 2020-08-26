# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import getpass
import urllib.request
from .pagure import fetch_issues, fetch_pull_requests
from .github import GithubWorker

REPO_NAME = "389-ds-base"


def run(args):
    if args.GITHUB_REPO:
        g_key = getpass.getpass()
        g = GithubWorker(args.GITHUB_REPO, g_key)
    issue_jsons = fetch_issues()
    for issue in issue_jsons:
        params = {'title': issue["title"],
                  # Add Opened by NAME at DATE
                  # Closed as STATUS
                  'body': issue["content"],
                  'assignee': issue["assignee"]["name"],
                  'milestone': issue["milestone"],
                  'labels': ['bug', 'easy']}
        comments = []
        for comment in issue["comments"]:
            # Add Added by NAME at DATE
            comments.append({'body': comment["comment"]})
        comments_params = {'comments': comments}
        g.ensure_issue(params, comments_params)
    # Do the same but for PR format and attach PR's patch
    pr_jsons = fetch_pull_requests()
