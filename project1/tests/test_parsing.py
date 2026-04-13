"""Tests for the parsing module."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import EventKind
from parsing import _parse_lines


class TestParseLines(unittest.TestCase):
    def test_basic_config(self):
        lines = [
            'LENGTH 500',
            'DEVICE 1',
            'DEVICE 2',
            'PROPAGATE 1 2 100',
            'ALERT 1 Fire 0',
        ]
        cfg = _parse_lines(lines)
        self.assertEqual(cfg.length, 500)
        self.assertIn(1, cfg.propagation)
        self.assertIn(2, cfg.propagation)
        self.assertEqual(cfg.propagation[1], [(2, 100)])
        self.assertEqual(len(cfg.initial_events), 1)
        self.assertEqual(cfg.initial_events[0].kind, EventKind.RAISE_ALERT)
        self.assertEqual(cfg.initial_events[0].device, 1)
        self.assertEqual(cfg.initial_events[0].description, 'Fire')
        self.assertEqual(cfg.initial_events[0].time, 0)

    def test_comments_and_blank_lines_ignored(self):
        lines = [
            '# This is a comment',
            '',
            'LENGTH 100',
            '   # indented comment',
            'DEVICE 1',
            '',
        ]
        cfg = _parse_lines(lines)
        self.assertEqual(cfg.length, 100)

    def test_cancel_event(self):
        lines = [
            'LENGTH 200',
            'DEVICE 1',
            'CANCEL 1 Fire 50',
        ]
        cfg = _parse_lines(lines)
        self.assertEqual(len(cfg.initial_events), 1)
        self.assertEqual(cfg.initial_events[0].kind, EventKind.RAISE_CANCEL)

    def test_missing_length_raises(self):
        lines = ['DEVICE 1']
        with self.assertRaises(ValueError):
            _parse_lines(lines)

    def test_multiple_propagation_targets(self):
        lines = [
            'LENGTH 100',
            'DEVICE 1',
            'DEVICE 2',
            'DEVICE 3',
            'PROPAGATE 1 2 50',
            'PROPAGATE 1 3 75',
        ]
        cfg = _parse_lines(lines)
        self.assertEqual(len(cfg.propagation[1]), 2)

    def test_device_with_no_propagation(self):
        lines = [
            'LENGTH 100',
            'DEVICE 5',
        ]
        cfg = _parse_lines(lines)
        self.assertEqual(cfg.propagation[5], [])


if __name__ == '__main__':
    unittest.main()
