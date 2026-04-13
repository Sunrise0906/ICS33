"""Parsing logic for simulation input files."""

from __future__ import annotations

import collections
from pathlib import Path

from models import Event, EventKind, SimulationConfig


def read_input_path() -> Path:
    """Read the input file path from stdin (no prompt)."""
    return Path(input())


def parse_file(path: Path) -> SimulationConfig:
    """Parse an input file and return a SimulationConfig."""
    lines = path.read_text(encoding='utf-8').splitlines()
    return _parse_lines(lines)


def _parse_lines(lines: list[str]) -> SimulationConfig:
    """Parse raw lines into a SimulationConfig.

    This is separated from parse_file so it can be tested independently
    without needing actual files on disk.
    """
    length: int | None = None
    devices: set[int] = set()
    propagation: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    initial_events: list[Event] = []
    seq = 0

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split()
        tag = parts[0]

        if tag == 'LENGTH':
            length = int(parts[1])
        elif tag == 'DEVICE':
            devices.add(int(parts[1]))
        elif tag == 'PROPAGATE':
            src, dst, delay = int(parts[1]), int(parts[2]), int(parts[3])
            propagation[src].append((dst, delay))
        elif tag == 'ALERT':
            dev, desc, t = int(parts[1]), parts[2], int(parts[3])
            initial_events.append(
                Event(time=t, seq=seq, kind=EventKind.RAISE_ALERT,
                      device=dev, description=desc)
            )
            seq += 1
        elif tag == 'CANCEL':
            dev, desc, t = int(parts[1]), parts[2], int(parts[3])
            initial_events.append(
                Event(time=t, seq=seq, kind=EventKind.RAISE_CANCEL,
                      device=dev, description=desc)
            )
            seq += 1

    if length is None:
        raise ValueError('LENGTH directive is required')

    for d in devices:
        propagation.setdefault(d, [])

    return SimulationConfig(
        length=length,
        propagation=dict(propagation),
        initial_events=initial_events,
    )
