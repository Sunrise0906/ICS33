from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal
import collections
import heapq
import itertools


# ----------------------------
# Data models
# ----------------------------

EventKind = Literal["RAISE_ALERT", "RAISE_CANCEL", "RECV_ALERT", "RECV_CANCEL"]


@dataclass(frozen=True)
class Event:
    time: int
    kind: EventKind
    device: int          # who is raising/receiving the message
    desc: str            # alert/cancel description
    src: Optional[int] = None  # source device for received messages


@dataclass
class SimulationConfig:
    length: int
    propagate: dict[int, list[tuple[int, int]]]  # from -> [(to, delay), ...]
    initial_events: list[Event]


# ----------------------------
# I/O
# ----------------------------

def _read_input_file_path() -> Path:
    """Reads the input file path from standard input (no prompt)."""
    return Path(input())


def _parse_input_lines(lines: list[str]) -> SimulationConfig:
    length: Optional[int] = None
    devices: set[int] = set()
    propagate: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    initial: list[Event] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        tag = parts[0]

        if tag == "LENGTH":
            length = int(parts[1])

        elif tag == "DEVICE":
            devices.add(int(parts[1]))

        elif tag == "PROPAGATE":
            frm = int(parts[1])
            to = int(parts[2])
            delay = int(parts[3])
            propagate[frm].append((to, delay))

        elif tag == "ALERT":
            dev = int(parts[1])
            desc = parts[2]
            t = int(parts[3])
            initial.append(Event(t, "RAISE_ALERT", dev, desc))

        elif tag == "CANCEL":
            dev = int(parts[1])
            desc = parts[2]
            t = int(parts[3])
            initial.append(Event(t, "RAISE_CANCEL", dev, desc))

        else:
            # Per project assumptions, input will be valid;
            # keeping this for safety in development.
            raise ValueError(f"Unknown line: {line}")

    if length is None:
        raise ValueError("Missing LENGTH")

    # Ensure every device has a propagate list (even if empty)
    for d in devices:
        propagate.setdefault(d, [])

    return SimulationConfig(length=length, propagate=dict(propagate), initial_events=initial)


# ----------------------------
# Simulation core
# ----------------------------

def _run_simulation(cfg: SimulationConfig) -> list[str]:
    # Priority queue: (time, seq, Event)
    heap: list[tuple[int, int, Event]] = []
    seq = itertools.count()

    for ev in cfg.initial_events:
        heapq.heappush(heap, (ev.time, next(seq), ev))

    # cancel_time[device][desc] = first time that device learned cancellation
    cancel_time: dict[int, dict[str, int]] = {}

    def cancelled_before(device: int, desc: str, t: int) -> bool:
        prev = cancel_time.get(device, {}).get(desc)
        return prev is not None and prev < t   # strict < implements the n+1 rule

    def record_cancel(device: int, desc: str, t: int) -> None:
        d = cancel_time.setdefault(device, {})
        if desc not in d or t < d[desc]:
            d[desc] = t

    out: list[str] = []

    while heap:
        t, _, ev = heapq.heappop(heap)

        # Simulation ends at cfg.length; do not process events at/after that time.
        if t >= cfg.length:
            break

        if ev.kind == "RAISE_ALERT":
            # Originating an alert does NOT print a RECEIVED line.
            if cancelled_before(ev.device, ev.desc, t):
                continue

            for to, delay in cfg.propagate.get(ev.device, []):
                out.append(f"@{t}: #{ev.device} SENT ALERT TO #{to}: {ev.desc}")
                heapq.heappush(
                    heap,
                    (t + delay, next(seq), Event(t + delay, "RECV_ALERT", to, ev.desc, src=ev.device))
                )

        elif ev.kind == "RAISE_CANCEL":
            # Originating a cancellation: record it immediately.
            record_cancel(ev.device, ev.desc, t)
            if cancelled_before(ev.device, ev.desc, t):
                continue

            for to, delay in cfg.propagate.get(ev.device, []):
                out.append(f"@{t}: #{ev.device} SENT CANCELLATION TO #{to}: {ev.desc}")
                heapq.heappush(
                    heap,
                    (t + delay, next(seq), Event(t + delay, "RECV_CANCEL", to, ev.desc, src=ev.device))
                )

        elif ev.kind == "RECV_ALERT":
            out.append(f"@{t}: #{ev.device} RECEIVED ALERT FROM #{ev.src}: {ev.desc}")

            if cancelled_before(ev.device, ev.desc, t):
                continue

            for to, delay in cfg.propagate.get(ev.device, []):
                out.append(f"@{t}: #{ev.device} SENT ALERT TO #{to}: {ev.desc}")
                heapq.heappush(
                    heap,
                    (t + delay, next(seq), Event(t + delay, "RECV_ALERT", to, ev.desc, src=ev.device))
                )

        elif ev.kind == "RECV_CANCEL":
            out.append(f"@{t}: #{ev.device} RECEIVED CANCELLATION FROM #{ev.src}: {ev.desc}")

            already = cancelled_before(ev.device, ev.desc, t)
            record_cancel(ev.device, ev.desc, t)

            if already:
                continue

            for to, delay in cfg.propagate.get(ev.device, []):
                out.append(f"@{t}: #{ev.device} SENT CANCELLATION TO #{to}: {ev.desc}")
                heapq.heappush(
                    heap,
                    (t + delay, next(seq), Event(t + delay, "RECV_CANCEL", to, ev.desc, src=ev.device))
                )

        else:
            raise AssertionError(f"Unexpected event kind: {ev.kind}")

    out.append(f"@{cfg.length}: END")
    return out


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    input_file_path = _read_input_file_path()

    if not input_file_path.exists():
        print("FILE NOT FOUND")
        return

    lines = input_file_path.read_text(encoding="utf-8").splitlines()
    cfg = _parse_input_lines(lines)
    output_lines = _run_simulation(cfg)

    for line in output_lines:
        print(line)


if __name__ == "__main__":
    main()
