"""Active dataset: members, vehicles, travel times. Swapped atomically by operators."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dataset:
    version: int
    members: dict          # member_id -> stop_id
    arrive_by: dict        # member_id -> minute of day
    vehicles: dict         # vehicle_id -> capacity
    travel: dict = field(default_factory=dict)  # (from_stop, to_stop) -> minutes (float)


_active = None


def activate(ds: Dataset) -> None:
    global _active
    _active = ds


def active() -> Dataset:
    if _active is None:
        raise RuntimeError("no active dataset")
    return _active
