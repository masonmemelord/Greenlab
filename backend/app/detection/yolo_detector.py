import torch
from pathlib import Path
from ultralytics import YOLO
from ultralytics.engine.results import Results


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = BACKEND_ROOT / "ml" / "weights" / "detection" / "best.pt"


class CellDetector:
    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH):
        if torch.backends.mps.is_available():
            self.device = 'mps'
        elif torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'

        print(f"Using device: {self.device}")

        try:
            self.model = YOLO(str(model_path))
            self.model.to(self.device)
            print(f"Loaded model from {model_path}")
        except Exception as e:
            raise RuntimeError(
                f"Could not load model from '{model_path}'. "
                "Please make sure the detection weights file is available."
            )

    def predict(self, image, confidence=0.25, iou=0.4):
        """Runs detection on a PIL image using YOLOv8."""
        results = self.model.predict(
            source=image,
            conf=confidence,
            iou=iou,
            device=self.device,
            imgsz=1280,
            augment=True,
            agnostic_nms=True,
            max_det=1000,
        )
        return results[0]

    def get_metadata(self, results: Results, cell_types: dict = None):
        """Extracts cell metadata from results."""
        cells = []
        for i, box in enumerate(results.boxes):
            class_id = int(box.cls[0].item())
            cell_type = cell_types.get(class_id, f"Class {class_id}") if cell_types else results.names.get(class_id, f"Class {class_id}")
            cells.append({
                "Cell(s)": i + 1,
                "Cell Type": cell_type,
                "Confidence Score": round(float(box.conf[0].item()), 3),
                "Class ID": class_id,
                "Coordinates": box.xyxy[0].tolist(),
                "Center & Size": box.xywh[0].tolist(),
            })
        return cells
