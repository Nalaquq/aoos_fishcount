"""Main inference pipeline: capture → detect → track → count → log."""

from __future__ import annotations

import logging
import time
from typing import Any

import cv2

from aoos_fishcount.inference.counter import LineCounter
from aoos_fishcount.inference.model import SalmonDetector
from aoos_fishcount.sensors.camera import CameraCapture
from aoos_fishcount.sensors.environment import EnvironmentSensor
from aoos_fishcount.utils.database import Database
from aoos_fishcount.utils.push import push_summary

log = logging.getLogger(__name__)

HEALTH_INTERVAL_S = 300   # Log interior environment every 5 minutes
PUSH_INTERVAL_S   = 3600  # Push count summary every 60 minutes


class Pipeline:
    """End-to-end salmon counting pipeline.

    Args:
        cfg: Validated deployment configuration dictionary.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        inf = cfg["inference"]
        cam = cfg["camera"]
        log_cfg = cfg["logging"]

        self.camera   = CameraCapture(cam["device_index"], cam["width"], cam["height"], cam["fps"])
        self.detector = SalmonDetector(inf["model_path"], inf["conf_threshold"])
        self.counter  = LineCounter(line_y=inf["line_y"])
        self.db       = Database(log_cfg["db_path"])
        self.env      = EnvironmentSensor()

        self._last_health = 0.0
        self._last_push   = 0.0

    def run(self) -> None:
        """Start the main inference loop. Runs until interrupted."""
        log.info(
            "Pipeline started — site: %s, line_y: %d",
            self.cfg["site"]["name"],
            self.cfg["inference"]["line_y"],
        )
        try:
            while True:
                frame = self.camera.read()
                if frame is None:
                    time.sleep(0.1)
                    continue

                self._maybe_log_health()
                self._maybe_push_summary()
                self._process_frame(frame)
        except KeyboardInterrupt:
            log.info("Pipeline stopped by user. Total count: %d", self.counter.total)
        finally:
            self.camera.release()
            self.db.close()

    def _process_frame(self, frame) -> None:
        results = self.detector.track(frame)
        if results.boxes.id is None:
            return

        boxes = results.boxes.xyxy.cpu().numpy()
        ids   = results.boxes.id.int().cpu().numpy()
        clss  = results.boxes.cls.int().cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()

        for box, tid, cls, conf in zip(boxes, ids, clss, confs):
            cx = int((box[0] + box[2]) / 2)
            cy = int((box[1] + box[3]) / 2)
            crossed = self.counter.update(tid, cx, cy)
            if crossed:
                species = self.detector.class_names.get(cls, "unknown")
                self.db.log_count(species, float(conf), int(tid))
                log.info(
                    "COUNT #%d — species=%s conf=%.2f track_id=%d",
                    self.counter.total, species, conf, tid,
                )

    def _maybe_log_health(self) -> None:
        now = time.time()
        if now - self._last_health < HEALTH_INTERVAL_S:
            return
        self._last_health = now
        reading = self.env.read()
        if reading:
            self.db.log_health(reading["temp_c"], reading["humidity_pct"])
            if reading["humidity_pct"] and reading["humidity_pct"] > 70:
                log.warning(
                    "Interior humidity HIGH: %.0f%% — check desiccant",
                    reading["humidity_pct"],
                )

    def _maybe_push_summary(self) -> None:
        now = time.time()
        if now - self._last_push < PUSH_INTERVAL_S:
            return
        self._last_push = now
        summary = self.db.hourly_summary()
        endpoint = self.cfg.get("push", {}).get("endpoint")
        push_summary(summary, endpoint=endpoint)
