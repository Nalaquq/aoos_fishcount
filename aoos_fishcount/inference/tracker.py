"""ByteTrack tracker utilities and track state management."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Track:
    """Represents a single ByteTrack object track."""
    track_id: int
    positions: list[tuple[int, int]] = field(default_factory=list)
    species: str | None = None
    confidence: float = 0.0

    def update(self, cx: int, cy: int, species: str, conf: float) -> None:
        self.positions.append((cx, cy))
        self.species = species
        self.confidence = conf


class TrackRegistry:
    """In-memory registry of active ByteTrack tracks."""

    def __init__(self, max_history: int = 30) -> None:
        self._tracks: dict[int, Track] = {}
        self.max_history = max_history

    def update(self, track_id: int, cx: int, cy: int, species: str, conf: float) -> Track:
        if track_id not in self._tracks:
            self._tracks[track_id] = Track(track_id=track_id)
        t = self._tracks[track_id]
        t.update(cx, cy, species, conf)
        if len(t.positions) > self.max_history:
            t.positions.pop(0)
        return t

    def get(self, track_id: int) -> Track | None:
        return self._tracks.get(track_id)

    def prune(self, active_ids: set[int]) -> None:
        """Remove tracks that are no longer active."""
        stale = [tid for tid in self._tracks if tid not in active_ids]
        for tid in stale:
            del self._tracks[tid]
