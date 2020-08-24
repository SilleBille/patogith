# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import json
import urllib.request
from os import listdir
from os.path import isfile, join

ISSUES_DIR = "tickets"
PRS_DIR = "requests"
REPO_NAME = "389-ds-base"


def run(args):
    issues = [f for f in listdir(ISSUES_DIR) if isfile(join(ISSUES_DIR, f))]
    prs = [f for f in listdir(PRS_DIR) if isfile(join(PRS_DIR, f))]

    issue_jsons = []
    for issue in issues:
        with open(join(ISSUES_DIR, issue)) as f:
            issue_jsons.append(json.loads(f.read()))

    pr_jsons = []
    for pr in prs:
        with open(join(PRS_DIR, pr)) as f:
            pr_jsons.append(json.loads(f.read()))

    print(pr_jsons[0]['id'])
    print(issue_jsons[0]['id'])
    with urllib.request.urlopen(f'https://www.pagure.io/{REPO_NAME}/pull-request/{pr_jsons[0]["id"]}.patch') as f:
        pr_patch = f.read().decode('utf-8')
    print(pr_patch)
