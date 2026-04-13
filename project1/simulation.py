"""Core simulation engine for alert propagation."""

from __future__ import annotations

import heapq
import itertools

from models import Event, EventKind, SimulationConfig


def run(cfg: SimulationConfig) -> list[str]:
    """Run the simulation and return all output lines."""
    heap: list[Event] = []
    seq = itertools.count(
        max((e.seq for e in cfg.initial_events), default=-1) + 1
    )

    for ev in cfg.initial_events:
        heapq.heappush(heap, ev)

    # Tracks the earliest time each device learned about a cancellation.
    # cancel_learned[device][description] = time
    cancel_learned: dict[int, dict[str, int]] = {}

    output: list[str] = []

    def _is_cancelled_before(device: int, desc: str, time: int) -> bool:
        """Return True if `device` learned cancellation for `desc` strictly before `time`.

        This implements the "n+1 rule": a cancellation at time n only
        suppresses propagation of events arriving at time n+1 or later.
        """
        learned = cancel_learned.get(device, {}).get(desc)
        return learned is not None and learned < time

    def _record_cancel(device: int, desc: str, time: int) -> None:
        """Record when a device first learned about a cancellation."""
        device_cancels = cancel_learned.setdefault(device, {})
        if desc not in device_cancels or time < device_cancels[desc]:
            device_cancels[desc] = time

    def _propagate_alert(device: int, desc: str, time: int) -> None:
        """Send an alert from `device` to all its propagation targets."""
        for target, delay in cfg.propagation.get(device, []):
            output.append(f'@{time}: #{device} SENT ALERT TO #{target}: {desc}')
            heapq.heappush(heap, Event(
                time=time + delay, seq=next(seq),
                kind=EventKind.RECV_ALERT, device=target,
                description=desc, source=device,
            ))

    def _propagate_cancel(device: int, desc: str, time: int) -> None:
        """Send a cancellation from `device` to all its propagation targets."""
        for target, delay in cfg.propagation.get(device, []):
            output.append(f'@{time}: #{device} SENT CANCELLATION TO #{target}: {desc}')
            heapq.heappush(heap, Event(
                time=time + delay, seq=next(seq),
                kind=EventKind.RECV_CANCEL, device=target,
                description=desc, source=device,
            ))

    while heap:
        ev = heapq.heappop(heap)

        if ev.time >= cfg.length:
            break

        if ev.kind == EventKind.RAISE_ALERT:
            if not _is_cancelled_before(ev.device, ev.description, ev.time):
                _propagate_alert(ev.device, ev.description, ev.time)

        elif ev.kind == EventKind.RAISE_CANCEL:
            _record_cancel(ev.device, ev.description, ev.time)
            if not _is_cancelled_before(ev.device, ev.description, ev.time):
                _propagate_cancel(ev.device, ev.description, ev.time)

        elif ev.kind == EventKind.RECV_ALERT:
            output.append(
                f'@{ev.time}: #{ev.device} RECEIVED ALERT FROM #{ev.source}: {ev.description}'
            )
            if not _is_cancelled_before(ev.device, ev.description, ev.time):
                _propagate_alert(ev.device, ev.description, ev.time)

        elif ev.kind == EventKind.RECV_CANCEL:
            output.append(
                f'@{ev.time}: #{ev.device} RECEIVED CANCELLATION FROM #{ev.source}: {ev.description}'
            )
            already = _is_cancelled_before(ev.device, ev.description, ev.time)
            _record_cancel(ev.device, ev.description, ev.time)
            if not already:
                _propagate_cancel(ev.device, ev.description, ev.time)

    output.append(f'@{cfg.length}: END')
    return output
