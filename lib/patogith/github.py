# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

from github import Github


class GithubWorker:
    def __init__(self, repo, api_key):
        self.api = Github(api_key)
        self.repo = self.api.get_repo(repo)
        self.issues = self.repo.get_issues()
        self.milestones = self.repo.get_milestones()
        self.assignees = {"mreynolds": "marcus2376",
                          "mhonek": "kenoh",
                          "spichugi": "droideck",
                          "firstyear": "Firstyear",
                          "tbordaz": "tbordaz"}

    def _create_issue(self, params, comments_params, ensured_issue=None):
        if "milestone" in params:
            milestone_obj = self.ensure_milestone({'title': params['milestone']})
            params['milestone'] = milestone_obj
        if ensured_issue is not None:
            ensured_issue.edit(**params)
            issue = ensured_issue
        else:
            issue = self.repo.create_issue(**params)
        existent_comments = issue.get_comments()
        for comment in comments_params['comments']:
            self.ensure_comment(issue, existent_comments, comment)
        return issue

    def _create_milestone(self, params, ensured_milestone=None):
        if ensured_milestone is not None:
            ensured_milestone.edit(**params)
            return ensured_milestone
        else:
            return self.repo.create_milestone(**params)

    def _create_comment(self, issue, params, ensured_comment=None):
        if ensured_comment is not None:
            ensured_comment.edit(**params)
            return ensured_comment
        else:
            return issue.create_comment(**params)

    def find_issue(self, issue_name):
        try:
            return [issue for issue in self.issues if issue.title.lower() == issue_name.lower()][0]
        except IndexError:
            return None

    def find_milestone(self, ms_name):
        try:
            return [ms for ms in self.milestones if ms.title.lower() == ms_name.lower()][0]
        except IndexError:
            return None

    def find_comment(self, comments, comment_body):
        try:
            return [c for c in comments if c.body.lower() == comment_body.lower()][0]
        except IndexError:
            return None

    def create_issue(self, params, comments_params):
        return self._create_issue(params, comments_params)

    def create_milestone(self, params):
        return self._create_milestone(params)

    def create_comment(self, issue, params):
        return self._create_milestone(issue, params)

    def ensure_issue(self, params, comments_params):
        already_created_issue = self.find_issue(params['title'])
        return self._create_issue(params, comments_params, ensured_issue=already_created_issue)

    def ensure_milestone(self, params):
        already_created_milestone = self.find_milestone(params['title'])
        return self._create_milestone(params, ensured_milestone=already_created_milestone)

    def ensure_comment(self, issue, comments, params):
        already_created_comment = self.find_comment(comments, params['body'])
        return self._create_comment(issue, params, ensured_comment=already_created_comment)
