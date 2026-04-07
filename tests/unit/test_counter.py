"""Unit tests for LineCounter."""

import pytest
from aoos_fishcount.inference.counter import LineCounter


def test_no_count_before_history():
    counter = LineCounter(line_y=540)
    # Fewer than 3 history points — should not count
    assert counter.update(1, 100, 600) is None
    assert counter.update(1, 100, 580) is None
    assert counter.total == 0


def test_upstream_crossing_counted():
    counter = LineCounter(line_y=540)
    # Fish moves from y=600 → y=560 → y=520 (crosses line_y=540 going up)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    result = counter.update(1, 100, 520)
    assert result == "upstream"
    assert counter.upstream == 1
    assert counter.total == 1


def test_same_track_counted_once_upstream():
    counter = LineCounter(line_y=540)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    counter.update(1, 100, 520)
    # Second crossing attempt for same track_id
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    result = counter.update(1, 100, 520)
    assert result is None
    assert counter.upstream == 1


def test_downstream_crossing_counted():
    counter = LineCounter(line_y=540)
    # Fish moves downward (y increasing) — downstream
    counter.update(1, 100, 400)
    counter.update(1, 100, 500)
    result = counter.update(1, 100, 600)
    assert result == "downstream"
    assert counter.downstream == 1
    # Downstream does not add to total (total = upstream only)
    assert counter.total == 0


def test_net_upstream():
    counter = LineCounter(line_y=540)
    # One upstream
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    counter.update(1, 100, 520)
    # One downstream (different track)
    counter.update(2, 100, 400)
    counter.update(2, 100, 500)
    counter.update(2, 100, 600)
    assert counter.upstream == 1
    assert counter.downstream == 1
    assert counter.net_upstream() == 0


def test_reset():
    counter = LineCounter(line_y=540)
    counter.update(1, 100, 600)
    counter.update(1, 100, 560)
    counter.update(1, 100, 520)
    assert counter.upstream == 1
    counter.reset()
    assert counter.total == 0
    assert counter.upstream == 0
    assert counter.downstream == 0
