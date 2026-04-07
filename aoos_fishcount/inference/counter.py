"""Virtual line crossing counter using ByteTrack track history."""

from __future__ import annotations

import logging
from collections import defaultdict

log = logging.getLogger(__name__)


class LineCounter:
    """Counts objects crossing a horizontal virtual line.

    Args:
        line_y: Y-pixel coordinate of the counting line (0 = top of frame).
        history_len: Number of historical positions to retain per track.
    """

    def __init__(self, line_y: int, history_len: int = 5) -> None:
        self.line_y = line_y
        self.history_len = history_len
        self._history: dict[int, list[tuple[int, int]]] = defaultdict(list)
        self._counted: set[int] = set()
        self.total: int = 0

    def update(
        self,
        track_id: int,
        cx: int,
        cy: int,
    ) -> bool:
        """Update position history and check for line crossing.

        Args:
            track_id: Unique ByteTrack ID for this detection.
            cx: Centre X pixel coordinate.
            cy: Centre Y pixel coordinate.

        Returns:
            True if this update triggered a new upstream count.
        """
        history = self._history[track_id]
        history.append((cx, cy))
        if len(history) > self.history_len:
            history.pop(0)

        if track_id in self._counted or len(history) < 3:
            return False

        # Upstream crossing: fish moves from below line_y to above (cy decreasing)
        if history[-3][1] > self.line_y >= cy:
            self._counted.add(track_id)
            self.total += 1
            log.debug("Upstream crossing: track_id=%d total=%d", track_id, self.total)
            return True

        return False

    def reset(self) -> None:
        """Clear history and counts."""
        self._history.clear()
        self._counted.clear()
        self.total = 0
