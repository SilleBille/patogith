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
from .pagure import fetch_issues, fetch_pull_requests, PagureWorker
from .github import GithubWorker
from .bugzilla import BugzillaWorker
from github import GithubException

# Write your own milestone list here (lowercase)
MILESTONE_LIST = [
    "0.0 needs_triage",
    "ci test 1.0",
    "1.3.9",
    "1.3.10",
    "1.4.0",
    "1.4.1",
    "1.4.2",
    "1.4.3",
    "1.4.4",
    "1.4.5",
    "1.4 backlog",
    "2.0.0",
    "future",
    "legacy",
]

# Write your own nickname list here
NICKNAME_LIST = {
    "mreynolds": "mreynolds389",
    "lkrispen": "elkris",
    "tbordaz": "tbordaz",
    "firstyear": "Firstyear",
    "mhonek": "kenoh",
    "spichugi": "droideck",
    "vashirov": "vashirov",
    "nhosoi": "nhosoi",
    "rmeggins": "richm",
    "nkinder": "nkinder",
    "edewata": "edewata",
    "aborah": "aborah-sudo",
    "amsharma": "amsharma3",
    "ilias95": "ilstam",
    "simo": "simo5",
    "rcritten": "rcritten",
    "gparente": "germanparente",
}

# Write your own label list here
LABELS = {
    "fixed": "Closed: Fixed",
    "invalid": "Closed: Not a bug",
    "wontfix": "Closed: Won't fix",
    "duplicate": "Closed: Duplicate",
    "worksforme": "Closed: Works for me",
}
# Make sure to go over the links and modify it according to your needs
# - copy_issues() - change attachments list
# - update_bugzillas() - change Bugzilla link


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

    return [LABELS[issue["close_status"].lower()]]


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
    if "#" in content:
        i = 0
        while True:
            try:
                i = content.index("#", i)
                try:
                    # We want to replace only the references to other issues/PRs
                    int(content[i + 1])
                    content = content[:i] + content[i + 1:]
                except ValueError:
                    i = i + 1
            except (IndexError, ValueError):
                break
    content = content.replace("{{{", "```")
    content = content.replace("}}}", "```")
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
    return f"[{format_time(comment['date_created'])}](https://pagure.io/389-ds-base/issue/{issue['id']})"


def wait_for_rate_reset(log, reset_time):
    resetts = int(reset_time.timestamp()) + 2 * 60 * 60  # Time difference
    sleeptime = resetts - int(datetime.datetime.now().timestamp())
    log.info(f"Sleeping till {reset_time} + 10 seconds")
    if sleeptime > 0:
        time.sleep(sleeptime)
    time.sleep(10)


def validate_args(args):
    if args.github_repo:
        g_repo = args.github_repo
    else:
        g_repo = input("GitHub repo: ")

    if args.issues_file:
        issues_file = args.issues_file
    else:
        issues_file = input("Issue numbers file path: ")

    if args.pagure_repo:
        p_repo = args.pagure_repo
    else:
        p_repo = input("Pagure repo: ")

    return issues_file, g_repo, p_repo


def copy_issues(args, log):
    issues_file, g_repo, _, = validate_args(args)
    g_key = getpass.getpass("GitHub API Key: ")
    g = GithubWorker(g_repo, g_key, log)

    issue_jsons = sorted(
        fetch_pull_requests() + fetch_issues(), key=lambda b: int(b["id"])
    )
    for issue in issue_jsons:
        if g.rate_limit.core.remaining < 100:
            wait_for_rate_reset(log, g.rate_limit.core.reset)

        # It is a pull request
        if "branch" in issue:
            pr = issue

            is_closed = True  # Always close a PR
            params = {
                "title": f'PR - {pr["title"]}',
                "body": format_description_pr(pr),
                "labels": ["PR", pr["status"]],
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
                issue_gh = g.ensure_issue(params, comments_params, is_closed)
                with open(issues_file, "a+") as f:
                    f.write(f'pr:{pr["id"]}:{issue_gh.number}:\n')
                existent_comments = issue_gh.get_comments()
                pr_comment = {
                    "body": f"Patch\n[{pr['id']}.patch](https://fedorapeople.org/groups/389ds/github_attachments/{pr['id']}.patch)"
                }
                g.ensure_comment(issue_gh, existent_comments, pr_comment)
            except GithubException as e:
                if "blocked from content creation" in str(e):
                    wait_for_rate_reset(log, g.rate_limit.core.reset)

        # It is an issue
        else:
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
                        f"{format_comment_time(issue, c)}**\n\n{comment}"
                    }
                )
            comments_params = {"comments": comments}
            try:
                issue_gh = g.ensure_issue(params, comments_params, is_closed)
                bugs = get_bugs(issue)
                if bugs:
                    bz_numbers = ",".join([b.split("=")[1] for b in bugs])
                with open(issues_file, "a+") as f:
                    f.write(f'i:{issue["id"]}:{issue_gh.number}:{bz_numbers}\n')
            except GithubException as e:
                if "blocked from content creation" in str(e):
                    wait_for_rate_reset(log, g.rate_limit.core.reset)


def update_pagure_issues(args, log):
    issues_file, p_repo, _, = validate_args(args)
    p_key = getpass.getpass("Pagure API Key: ")
    p = PagureWorker(p_repo, p_key, log)

    with open(issues_file, "r") as f:
        for line in f.readlines():
            l_items = line.split(":")
            if len(l_items) > 1:
                if line.startswith("i"):
                    pg_issue_id = l_items[1]
                    gh_issue_id = l_items[2]
                    p.comment_on_issue(pg_issue_id, gh_issue_id)
                    p.close_issue(pg_issue_id, status="wontfix")
                elif line.startswith("pr"):
                    pg_pr_id = line.split(":")[0].replace("pr", "")
                    gh_issue_id = line.split(":")[1]
                    p.comment_on_pull_request(pg_pr_id, gh_issue_id)
                    p.close_pull_request(pg_issue_id)
                else:
                    log.warning(f"Line {line} has a wrong format and won't be updated")
            else:
                log.warning(f"Line {line} has a wrong format and won't be updated")


def update_bugzillas(args, log):
    issues_file, _, _, = validate_args(args)
    b_key = getpass.getpass("Bugzilla API Key: ")
    b = BugzillaWorker("bugzilla.redhat.com", b_key, log)
    # b = BugzillaWorker("partner-bugzilla.redhat.com", b_key, log)

    with open(issues_file, "r") as f:
        for line in f.readlines():
            bz_ids = []
            if line.startswith("i"):
                l_items = line.split(":")
                if len(l_items) > 1:
                    pg_issue_id = l_items[1]
                    gh_issue_id = l_items[2]
                if len(l_items) > 3:
                    bz_ids = l_items[3].split(",")
                for bz_id in bz_ids:
                    b.update_bugzilla(bz_id, pg_issue_id, gh_issue_id)


def close_unused_milestones(args, log):
    _, g_repo, _, = validate_args(args)
    g_key = getpass.getpass("GitHub API Key: ")
    g = GithubWorker(g_repo, g_key, log)
    for milestone in g.milestones:
        if milestone.title.lower() not in MILESTONE_LIST:
            g.close_milestone(milestone)
