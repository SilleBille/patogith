# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import bugzilla


class BugzillaWorker:
    def __init__(self, repo, api_key, log):
        self.api = bugzilla.Bugzilla(repo, api_key=api_key)
        self.log = log

    def update_bugzilla(self, bz_id, pg_issue_id, gh_issue_id):
        bug = self.api.getbug(bz_id)
        whiteboard = bug.devel_whiteboard.strip()
        if f"DS {pg_issue_id}" in whiteboard:
            whiteboard = whiteboard.replace(f"DS {pg_issue_id}", f"DS {gh_issue_id}")
        else:
            if whiteboard:
                whiteboard = whiteboard + f", DS {gh_issue_id}"
            else:
                whiteboard = f"DS {gh_issue_id}"
        print(f"{whiteboard}")

        update = self.api.build_update(devel_whiteboard=whiteboard)
        update["minor_update"] = True
        self.api.update_bugs([bz_id], update)
        param_dict = {
            "ext_bz_bug_id": f"389ds/389-ds-base/issues/{gh_issue_id}",
            "ext_type_id": 131,
        }
        params = {
            "bug_ids": [bz_id],
            "external_bugs": [param_dict],
            "minor_update": True,
        }
        self.api._backend.externalbugs_add(params)
