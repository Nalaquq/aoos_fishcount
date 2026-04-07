"""Unit tests for LineCounter."""

import pytest
from aoos_fishcount.inference.counter import LineCounter


def test_no_count_before_history():
    counter = LineCounter(line_y=540)
    # Fewer than 3 history points — should not count
    assert counter.update(1, 100, 600) is False
    assert counter.update(1, 100, 580) is False
    assert counter.total == 0


def test_upstream_crossing_counted():
    counter = LineCounter(line_y=540)
    # Fish moves from y=600 → y=560 → y=520 (crosses line_y=540 going up)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    result = counter.update(1, 100, 520)
    assert result is True
    assert counter.total == 1


def test_same_track_counted_once():
    counter = LineCounter(line_y=540)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    counter.update(1, 100, 520)
    # Second crossing attempt for same track_id
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    result = counter.update(1, 100, 520)
    assert result is False
    assert counter.total == 1


def test_downstream_not_counted():
    counter = LineCounter(line_y=540)
    # Fish moves downward (y increasing) — downstream
    counter.update(1, 100, 400)
    counter.update(1, 100, 500)
    result = counter.update(1, 100, 600)
    assert result is False
    assert counter.total == 0


def test_reset():
    counter = LineCounter(line_y=540)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    counter.update(1, 100, 520)
    assert counter.total == 1
    counter.reset()
    assert counter.total == 0
