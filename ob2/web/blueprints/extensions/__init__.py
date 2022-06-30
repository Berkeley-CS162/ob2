import apsw
import json
import logging
from flask import Blueprint, abort, request

import ob2.config as config
from ob2.database import DbCursor
from ob2.database.helpers import create_build
from ob2.dockergrader import dockergrader_queue, Job
from ob2.util.github_api import get_commit_message, get_diff_file_list
from ob2.util.hooks import apply_filters
from ob2.util.job_limiter import rate_limit_fail_build, should_limit_source
from ob2.mailer import create_email, mailer_queue
from ob2.util.time import parse_to_relative

blueprint = Blueprint("extensions", __name__, template_folder="templates")


@blueprint.route("/extensions/create", methods=["POST"])
def extensions():
    payload_bytes = request.get_data()
    if request.form.get("_csrf_token"):
        # You should not be able to use a CSRF token for this
        abort(400)
    try:
        payload = json.loads(payload_bytes)
        assert isinstance(payload, dict)

        sid = payload["sid"]
        days = int(payload["days"])
        login = payload["login"]
        assignment_name = payload["assignment"]
        approve_days = int(payload.get("approve_days", days))
        message = payload.get("message", "")

        assert isinstance(sid, str)
        assert isinstance(days, int)
        assert isinstance(login, str)
        assert isinstance(assignment_name, str)
        assert isinstance(approve_days, int)
        assert isinstance(message, str)

        if approve_days != message:
            message = (
                "Your original request was for %d days, but we've approved an extension for %d days. Please email us or post on Piazza if this is a concern. %s"
                % (days, approve_days, message)
            )

        message = message.strip()

        assignment = None
        for a in config.assignments:
            if a.name == assignment_name:
                assignment = a

        if assignment is None:
            return ("Assignment `%s` not found" % assignment_name, 400)

        with DbCursor() as c:
            c.execute("SELECT name, sid, email FROM users WHERE login = ?", [login])
            (name, db_sid, email) = c.fetchone()

            if sid != db_sid:
                return ("Student ID in request does not match database", 400)

            c.execute(
                "INSERT INTO extensions (user, assignment, days) VALUES (?, ?, ?)",
                [login, assignment_name, approve_days],
            )
            c.execute("SELECT last_insert_rowid()")
            (extension_id,) = c.fetchone()
            if config.mailer_enabled:
                assignment = assignment.student_view(c, login)
                due_date = parse_to_relative(assignment.due_date, 0, 0)
                email_payload = create_email(
                    "extension_confirm",
                    email,
                    "[CS 162] Extension Request Reviewed - %s" % assignment_name,
                    name=name,
                    days=approve_days,
                    assignment=assignment_name,
                    due_date=due_date,
                    message=message,
                )
                mailer_job = mailer_queue.create(c, "send", email_payload)
                mailer_queue.enqueue(mailer_job)

        res = {}
        res["status"] = "OK"
        res["id"] = extension_id

        return (res, 201)
    except Exception:
        logging.exception(
            "Error occurred while processing create extension request payload"
        )
        abort(500)
