# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import time
import datetime
import getpass
from .pagure import fetch_issues, fetch_pull_requests
from .github import GithubWorker
from github import GithubException


NICKNAME_LIST = {
    "firstyear": "Firstyear",
    "lkrispen": "elkris",
    "mhonek": "kenoh",
    "mreynolds": "marcus2376",
    "spichugi": "droideck",
    "tbordaz": "tbordaz",
    "vashirov": "vashirov",
}


def get_bugs(issue):
    bugs = set()
    for field in issue["custom_fields"]:
        if field["name"] == "rhbz":
            bug = field["value"]
            if not bug or bug.strip() == "0":
                continue

            bug = bug.replace("https://bugzilla.redhat.com/show_bug.cgi?id=", "")
            bug = bug.replace(", ", " ")
            bug = bug.replace(",", " ")
            for id in filter(None, bug.split(" ")):
                bugs.add(f"https://bugzilla.redhat.com/show_bug.cgi?id={id}")
    return bugs


def get_closed_labels(issue, is_closed):
    if not is_closed or "close_status" not in issue or issue["close_status"] is None:
        return []

    labels = {
        "fixed": "Closed: Fixed",
        "invalid": "Closed: Not a bug",
        "wontfix": "Closed: Won't fix",
        "duplicate": "Closed: Duplicate",
        "worksforme": "Closed: Works for me",
    }
    return [labels[issue["close_status"].lower()]]


def get_labels(issue):
    labels = []
    for tag in issue["tags"]:
        labels.append(tag)

    return labels


def format_description_issue(issue):
    out = ""
    out += (
        f"Cloned from Pagure issue: https://pagure.io/389-ds-base/issue/{issue['id']}\n"
    )

    out += f"- Created at {format_time(issue['date_created'])} by {format_user(issue['user'])}\n"

    if issue["status"] == "Closed":
        if "closed_at" in issue and issue["closed_at"] is not None:
            out += f"- Closed at {format_time(issue['closed_at'])} as {issue['close_status']}\n"
        else:
            out += f"- Closed as {issue['close_status']}\n"

    if issue["assignee"]:
        out += f"- Assigned to {format_user(issue['assignee'])}\n"
    else:
        out += f"- Assigned to nobody\n"

    bugs = get_bugs(issue)
    if bugs:
        out += f"- Associated bugzillas\n"
        for bug in bugs:
            out += f"  - {bug}\n"

    out += "\n---\n\n"
    content = cleaup_references(issue["content"].strip())
    out += content

    return out


def format_description_pr(pr):
    out = ""
    out += f"Cloned from Pagure Pull-Request: https://pagure.io/389-ds-base/pull-request/{pr['id']}\n"

    out += (
        f"- Created at {format_time(pr['date_created'])} by {format_user(pr['user'])}\n"
    )

    if pr["status"] != "Open":
        out += f"- Merged at {format_time(pr['closed_at'])}\n"

    out += "\n---\n\n"
    try:
        content = cleaup_references(pr["initial_comment"].strip())
    except AttributeError:
        content = ""
    out += content

    return out


def cleaup_references(content):
    for nickname_pg, nickname_gh in NICKNAME_LIST.items():
        content = content.replace(nickname_pg, nickname_gh)
    content = content.replace(" #", " ")
    return content


def format_time(timestamp):
    dt = datetime.datetime.fromtimestamp(int(timestamp))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_user(user):
    if user["name"] in NICKNAME_LIST.keys():
        return f"[{user['name']}](https://pagure.io/user/{user['name']}) (@{NICKNAME_LIST[user['name']]})"
    else:
        return f"[{user['name']}](https://pagure.io/user/{user['name']})"


def format_comment_time(issue, comment):
    return f"[{format_time(comment['date_created'])}](https://pagure.io/389-ds-base/issue/{issue['id']}#comment-{comment['id']})"


def wait_for_rate_reset(log, reset_time):
    resetts = int(reset_time.timestamp()) + 2 * 60 * 60  # Time difference
    sleeptime = resetts - int(datetime.datetime.now().timestamp())
    log.info(f"Sleeping till {reset_time} + 10 seconds")
    if sleeptime > 0:
        time.sleep(sleeptime)
    time.sleep(10)


def run(args, log):
    if args.GITHUB_REPO:
        g_key = getpass.getpass("GitHub API Key: ")
        g = GithubWorker(args.GITHUB_REPO, g_key, log)
    pr_jsons = fetch_pull_requests()
    for pr in pr_jsons:
        if g.rate_limit.core.remaining < 100:
            wait_for_rate_reset(log, g.rate_limit.core.reset)
        is_closed = True  # Always close a PR
        params = {
            "title": f'PR - {pr["title"]}',
            "body": format_description_pr(pr),
            "labels": [pr["status"]],
        }
        comments = []
        for c in pr["comments"]:
            comment = cleaup_references(c["comment"])
            comment = comment.replace(
                "/389-ds-base/issue/raw/files/",
                "https://fedorapeople.org/groups/389ds/github_attachments/",
            )
            comments.append(
                {
                    "body": f"**Comment from {format_user(c['user'])} at "
                    f"{format_comment_time(pr, c)}**\n\n{comment}"
                }
            )
        comments_params = {"comments": comments}
        try:
            issue = g.ensure_issue(params, comments_params, is_closed)
            existent_comments = issue.get_comments()
            pr_comment = {
                "body": f"Patch\n[{pr['id']}.patch](https://fedorapeople.org/groups/389ds/github_attachments/{pr['id']}.patch)"
            }
            g.ensure_comment(issue, existent_comments, pr_comment)
        except GithubException as e:
            if "blocked from content creation" in str(e):
                wait_for_rate_reset(log, g.rate_limit.core.reset)

    issue_jsons = fetch_issues()
    for issue in issue_jsons:
        if g.rate_limit.core.remaining < 100:
            wait_for_rate_reset(log, g.rate_limit.core.reset)
        is_closed = "Closed" in issue["status"]
        params = {
            "title": issue["title"],
            "body": format_description_issue(issue),
            "labels": get_closed_labels(issue, is_closed) + get_labels(issue),
        }
        if issue["milestone"] and issue["milestone"].lower() != "n/a":
            params["milestone"] = issue["milestone"]
        comments = []
        for c in issue["comments"]:
            comment = cleaup_references(c["comment"])
            comment = comment.replace(
                "/389-ds-base/issue/raw/files/",
                "https://fedorapeople.org/groups/389ds/github_attachments/",
            )
            comments.append(
                {
                    "body": f"**Comment from {format_user(c['user'])} at "
                    f"{format_comment_time(issue, c)}**\n\n{comment})"
                }
            )
        comments_params = {"comments": comments}
        try:
            g.ensure_issue(params, comments_params, is_closed)
        except GithubException as e:
            print(e)
            import pdb

            pdb.set_trace()
            if "blocked from content creation" in str(e):
                wait_for_rate_reset(log, g.rate_limit.core.reset)
    # Do the same but for PR format and attach PR's patch
