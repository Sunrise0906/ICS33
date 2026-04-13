"""Data models for the alert propagation simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventKind(Enum):
    """The four types of events in the simulation."""
    RAISE_ALERT = 'RAISE_ALERT'
    RAISE_CANCEL = 'RAISE_CANCEL'
    RECV_ALERT = 'RECV_ALERT'
    RECV_CANCEL = 'RECV_CANCEL'


@dataclass(frozen=True, order=True)
class Event:
    """A single event in the simulation timeline.

    Events are ordered by (time, seq) so the heap always breaks ties
    deterministically using insertion order.
    """
    time: int
    seq: int
    kind: EventKind = field(compare=False)
    device: int = field(compare=False)
    description: str = field(compare=False)
    source: Optional[int] = field(default=None, compare=False)


@dataclass
class SimulationConfig:
    """Everything parsed from the input file that the simulation needs."""
    length: int
    propagation: dict[int, list[tuple[int, int]]]   # device -> [(target, delay)]
    initial_events: list[Event]
