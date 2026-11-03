"""In-memory job store. The worker loop runs in the same process as the API."""
import itertools
import threading

from . import dataset, planner

JOBS = {}          # job_id -> dict(status, plan, dataset_version, reason)
PUBLISHED = {}     # member_id -> (vehicle_id, schedule)
_ids = itertools.count(1)
_lock = threading.Lock()


def submit():
    with _lock:
        jid = next(_ids)
        JOBS[jid] = {"status": "QUEUED", "plan": None, "dataset_version": None, "reason": None}
    return jid


def run(jid):
    ds = dataset.active()
    JOBS[jid].update(status="RUNNING", dataset_version=ds.version)
    try:
        routes, reason = planner.plan(ds)
    except Exception as e:  # noqa: BLE001 - surface any planner failure on the job
        JOBS[jid].update(status="FAILED", reason=str(e))
        return
    if dataset.active().version != ds.version:
        JOBS[jid].update(status="STALE", plan=routes, reason="dataset changed during run")
        return
    JOBS[jid].update(status="DONE", plan=routes, reason=reason)
    publish(ds, routes)


def publish(ds, routes):
    with _lock:
        PUBLISHED.clear()
        for vid, ms in routes.items():
            sch = planner.schedule(ds, ms)
            for m in ms:
                PUBLISHED[m] = (vid, sch)
