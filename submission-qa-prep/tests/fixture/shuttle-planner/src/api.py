"""Thin HTTP-ish handlers; a real server would wrap these."""
from . import jobs


def post_plans():
    jid = jobs.submit()
    jobs.run(jid)  # synchronous in this submission; see README
    return {"job_id": jid}


def get_job(jid):
    j = jobs.JOBS.get(jid)
    if j is None:
        return 404, {"error": "not found"}
    return 200, {"status": j["status"], "reason": j["reason"]}


def get_my_route(member_id):
    r = jobs.PUBLISHED.get(member_id)
    if r is None:
        return 404, {"error": "no published route"}
    vid, sch = r
    return 200, {"vehicle": vid, "schedule": sch}
