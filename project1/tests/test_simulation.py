"""Tests for the simulation engine."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Event, EventKind, SimulationConfig
from simulation import run


def _make_config(length, propagation, events_data):
    """Helper to build SimulationConfig from simplified event tuples.

    events_data: list of (time, kind_str, device, description)
        kind_str is 'ALERT' or 'CANCEL'
    """
    kind_map = {'ALERT': EventKind.RAISE_ALERT, 'CANCEL': EventKind.RAISE_CANCEL}
    events = [
        Event(time=t, seq=i, kind=kind_map[k], device=d, description=desc)
        for i, (t, k, d, desc) in enumerate(events_data)
    ]
    return SimulationConfig(length=length, propagation=propagation, initial_events=events)


class TestSimulation(unittest.TestCase):
    def test_empty_simulation(self):
        cfg = _make_config(100, {}, [])
        result = run(cfg)
        self.assertEqual(result, ['@100: END'])

    def test_single_alert_propagation(self):
        cfg = _make_config(
            length=500,
            propagation={1: [(2, 100)], 2: []},
            events_data=[(0, 'ALERT', 1, 'Fire')],
        )
        result = run(cfg)
        self.assertEqual(result, [
            '@0: #1 SENT ALERT TO #2: Fire',
            '@100: #2 RECEIVED ALERT FROM #1: Fire',
            '@500: END',
        ])

    def test_chain_propagation(self):
        cfg = _make_config(
            length=1000,
            propagation={1: [(2, 100)], 2: [(3, 50)], 3: []},
            events_data=[(0, 'ALERT', 1, 'Flood')],
        )
        result = run(cfg)
        self.assertIn('@0: #1 SENT ALERT TO #2: Flood', result)
        self.assertIn('@100: #2 RECEIVED ALERT FROM #1: Flood', result)
        self.assertIn('@100: #2 SENT ALERT TO #3: Flood', result)
        self.assertIn('@150: #3 RECEIVED ALERT FROM #2: Flood', result)

    def test_cancellation_suppresses_future_alerts(self):
        cfg = _make_config(
            length=500,
            propagation={1: [(2, 100)], 2: [(3, 100)], 3: []},
            events_data=[
                (0, 'ALERT', 1, 'X'),
                (0, 'CANCEL', 1, 'X'),
            ],
        )
        result = run(cfg)
        # Device 1 sends both alert and cancel to device 2
        self.assertIn('@0: #1 SENT ALERT TO #2: X', result)
        self.assertIn('@0: #1 SENT CANCELLATION TO #2: X', result)
        # Device 2 receives both at time 100
        self.assertIn('@100: #2 RECEIVED ALERT FROM #1: X', result)
        self.assertIn('@100: #2 RECEIVED CANCELLATION FROM #1: X', result)

    def test_n_plus_1_rule(self):
        """Alert and cancel arriving at the same device at the same time:
        alert should still be propagated (cancel only affects time n+1 onwards)."""
        cfg = _make_config(
            length=500,
            propagation={
                1: [(3, 100)],
                2: [(3, 100)],
                3: [(1, 50)],
            },
            events_data=[
                (0, 'ALERT', 1, 'Quake'),
                (0, 'CANCEL', 2, 'Quake'),
            ],
        )
        result = run(cfg)
        # Both arrive at device 3 at time 100
        self.assertIn('@100: #3 RECEIVED ALERT FROM #1: Quake', result)
        self.assertIn('@100: #3 RECEIVED CANCELLATION FROM #2: Quake', result)
        # Because cancel at time 100 only affects time 101+,
        # device 3 should still propagate the alert at time 100
        self.assertIn('@100: #3 SENT ALERT TO #1: Quake', result)

    def test_events_at_or_after_length_not_processed(self):
        cfg = _make_config(
            length=100,
            propagation={1: [(2, 100)], 2: []},
            events_data=[(0, 'ALERT', 1, 'Late')],
        )
        result = run(cfg)
        # Alert sent at time 0, received at time 100 which equals length -> not processed
        self.assertIn('@0: #1 SENT ALERT TO #2: Late', result)
        self.assertNotIn('@100: #2 RECEIVED ALERT FROM #1: Late', result)
        self.assertEqual(result[-1], '@100: END')

    def test_duplicate_cancel_not_repropagated(self):
        """If a device already learned a cancellation strictly before,
        receiving it again should not cause re-propagation."""
        cfg = _make_config(
            length=500,
            propagation={
                1: [(3, 50)],    # cancel arrives at 3 at time 50
                2: [(3, 100)],   # cancel arrives at 3 at time 100
                3: [(1, 10)],
            },
            events_data=[
                (0, 'CANCEL', 1, 'Dup'),
                (0, 'CANCEL', 2, 'Dup'),
            ],
        )
        result = run(cfg)
        # Device 3 receives first cancel at 50, second at 100
        # First should propagate, second should not (50 < 100)
        self.assertIn('@50: #3 SENT CANCELLATION TO #1: Dup', result)
        sent_count = sum(1 for line in result if '#3 SENT CANCELLATION' in line)
        self.assertEqual(sent_count, 1)

    def test_alert_suppressed_by_earlier_cancel(self):
        """An alert arriving after a cancel has been recorded should not propagate."""
        cfg = _make_config(
            length=500,
            propagation={
                1: [(3, 50)],   # cancel arrives at 3 at time 50
                2: [(3, 100)],  # alert arrives at 3 at time 100
                3: [(1, 10)],
            },
            events_data=[
                (0, 'CANCEL', 1, 'Storm'),
                (0, 'ALERT', 2, 'Storm'),
            ],
        )
        result = run(cfg)
        # Device 3 receives cancel at 50, alert at 100
        # Since 50 < 100, alert should NOT be propagated from device 3
        self.assertIn('@50: #3 RECEIVED CANCELLATION FROM #1: Storm', result)
        self.assertIn('@100: #3 RECEIVED ALERT FROM #2: Storm', result)
        # Device 3 should NOT send the alert
        self.assertNotIn('@100: #3 SENT ALERT TO #1: Storm', result)


if __name__ == '__main__':
    unittest.main()
