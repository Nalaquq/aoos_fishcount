"""Virtual line crossing counter using ByteTrack track history."""

from __future__ import annotations

import logging
from collections import defaultdict

log = logging.getLogger(__name__)


class LineCounter:
    """Counts objects crossing a horizontal virtual line (bidirectional).

    Tracks both upstream (cy decreasing across line_y) and downstream
    (cy increasing across line_y) crossings.  Each track ID is counted
    at most once per direction to avoid double-counting milling fish.

    Args:
        line_y: Y-pixel coordinate of the counting line (0 = top of frame).
        history_len: Number of historical positions to retain per track.
    """

    def __init__(self, line_y: int, history_len: int = 5) -> None:
        self.line_y = line_y
        self.history_len = history_len
        self._history: dict[int, list[tuple[int, int]]] = defaultdict(list)
        self._counted_up: set[int] = set()
        self._counted_down: set[int] = set()
        self.total: int = 0
        self.upstream: int = 0
        self.downstream: int = 0

    def update(
        self,
        track_id: int,
        cx: int,
        cy: int,
    ) -> str | None:
        """Update position history and check for line crossing.

        Args:
            track_id: Unique ByteTrack ID for this detection.
            cx: Centre X pixel coordinate.
            cy: Centre Y pixel coordinate.

        Returns:
            ``"upstream"`` or ``"downstream"`` if a crossing was detected,
            ``None`` otherwise.
        """
        history = self._history[track_id]
        history.append((cx, cy))
        if len(history) > self.history_len:
            history.pop(0)

        if len(history) < 3:
            return None

        # Upstream crossing: fish moves from below line_y to above (cy decreasing)
        if track_id not in self._counted_up and history[-3][1] > self.line_y >= cy:
            self._counted_up.add(track_id)
            self.upstream += 1
            self.total += 1
            log.debug("Upstream crossing: track_id=%d total=%d", track_id, self.total)
            return "upstream"

        # Downstream crossing: fish moves from above line_y to below (cy increasing)
        if track_id not in self._counted_down and history[-3][1] < self.line_y <= cy:
            self._counted_down.add(track_id)
            self.downstream += 1
            log.debug("Downstream crossing: track_id=%d downstream=%d", track_id, self.downstream)
            return "downstream"

        return None

    def net_upstream(self) -> int:
        """Return net upstream count (upstream - downstream)."""
        return self.upstream - self.downstream

    def reset(self) -> None:
        """Clear history and counts."""
        self._history.clear()
        self._counted_up.clear()
        self._counted_down.clear()
        self.total = 0
        self.upstream = 0
        self.downstream = 0
