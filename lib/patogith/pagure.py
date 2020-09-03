# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import json
from os import listdir
from os.path import isfile, join
from libpagure import Pagure

ISSUES_DIR = "tickets"
PRS_DIR = "requests"


def fetch_issues():
    issues = [f for f in listdir(ISSUES_DIR) if isfile(join(ISSUES_DIR, f))]
    issue_jsons = []
    for issue in issues:
        with open(join(ISSUES_DIR, issue)) as f:
            issue_jsons.append(json.loads(f.read()))
    return issue_jsons


def fetch_pull_requests():
    prs = [f for f in listdir(PRS_DIR) if isfile(join(PRS_DIR, f))]
    pr_jsons = []
    for pr in prs:
        with open(join(PRS_DIR, pr)) as f:
            pr_jsons.append(json.loads(f.read()))
    return pr_jsons


class PagureWorker:
    def __init__(self, repo, api_key, log):
        self.api = Pagure(pagure_token=api_key, repo_to=repo)
        self.log = log

    def comment_on_issue(self, pg_issue_id, gh_issue_id):
        self.api.comment_issue(self.id, msg)

    def close_issue(self, status=None):
        if status is None:
            status = "Fixed"

        self.api.change_issue_status(self.id, "Closed", status)

    def comment_on_pull_request(self, pg_pr_id, gh_issue_id):
        pass
