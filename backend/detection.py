"""Compatibility import. Use ``app.detection.yolo_detector`` in new code."""

from app.detection.yolo_detector import CellDetector

__all__ = ["CellDetector"]
