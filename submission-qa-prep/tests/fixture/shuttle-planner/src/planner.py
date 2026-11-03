"""Route planning: greedy baseline, then bounded local search."""
import math
import time

OFFICE = "OFFICE"
MAX_RIDE_MIN = 60


def leg_minutes(ds, a, b):
    # Each leg is rounded up on its own so per-stop times never run ahead of reality.
    return math.ceil(ds.travel[(a, b)])


def baseline(ds):
    """Fill each vehicle with the nearest unassigned members until capacity."""
    unassigned = sorted(ds.members, key=lambda m: ds.travel[(ds.members[m], OFFICE)])
    routes = {}
    for vid, cap in sorted(ds.vehicles.items()):
        routes[vid] = unassigned[:cap]
        unassigned = unassigned[cap:]
    if unassigned:
        raise ValueError(f"not enough seats for {len(unassigned)} members")
    return routes


def schedule(ds, members):
    """Return (stop, minute) list ending at OFFICE, latest feasible departure."""
    stops = [ds.members[m] for m in members] + [OFFICE]
    deadline = min(ds.arrive_by[m] for m in members) if members else 0
    times = [deadline]
    for a, b in reversed(list(zip(stops, stops[1:]))):
        times.insert(0, times[0] - leg_minutes(ds, a, b))
    return list(zip(stops, times))


def ride_minutes(ds, members):
    sch = schedule(ds, members)
    return sch[-1][1] - sch[0][1] if len(sch) > 1 else 0


def cost(ds, routes):
    return sum(ride_minutes(ds, ms) for ms in routes.values())


def validate_plan(ds, routes):
    errors = []
    for vid, ms in routes.items():
        if len(ms) > ds.vehicles[vid]:
            errors.append(f"{vid}: over capacity")
        if ride_minutes(ds, ms) > MAX_RIDE_MIN:
            errors.append(f"{vid}: ride over {MAX_RIDE_MIN} min")
    return errors


def improve(ds, routes, time_limit_sec=2.0, max_candidates=200):
    """Swap members between routes; keep a swap only if cost drops and rules hold."""
    best = {v: list(ms) for v, ms in routes.items()}
    best_cost = cost(ds, best)
    deadline = time.monotonic() + time_limit_sec
    tried = 0
    vids = list(best)
    for i, va in enumerate(vids):
        for vb in vids[i + 1:]:
            for ia in range(len(best[va])):
                for ib in range(len(best[vb])):
                    if time.monotonic() > deadline or tried >= max_candidates:
                        return best, "time_or_candidate_limit"
                    tried += 1
                    cand = {v: list(ms) for v, ms in best.items()}
                    cand[va][ia], cand[vb][ib] = cand[vb][ib], cand[va][ia]
                    if validate_plan(ds, cand):
                        continue
                    c = cost(ds, cand)
                    if c < best_cost:
                        best, best_cost = cand, c
    return best, "converged"


def plan(ds, time_limit_sec=2.0):
    routes = baseline(ds)
    routes, reason = improve(ds, routes, time_limit_sec=time_limit_sec)
    return routes, reason
