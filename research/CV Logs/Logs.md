# Computer Vision Logs
## Oct 3 — Improving CV dataset

### Objective
Determine whether a YOLO-based instance segmentation architecture can
improve cell localization and morphological measurement compared with
the existing YOLOv8 object-detection pipeline.

### Background / Rationale
The current YOLOv8 pipeline identifies cells using bounding boxes.
While this is sufficient for localization, bounding boxes do not
represent the actual boundaries of irregularly shaped cells.

Earlier development also identified discrepancies between automated
CV measurements and the manual CellSizer workflow. Segmentation may
provide a better representation for morphological measurements.

### Research Question
Does instance segmentation provide more reliable cell morphology
measurements than the existing bounding-box detection pipeline?

### Hypothesis
Pixel-level segmentation masks will provide more accurate estimates
of cell area and equivalent diameter than measurements derived from
bounding boxes.

### Method

**Baseline:** Current YOLOv8 detection pipeline

**Experimental Model:** YOLO segmentation architecture

**Dataset:** Existing Roboflow dataset

**Initial Metrics:**
- IoU
- Dice coefficient
- Precision
- Recall
- Area measurement error
- Equivalent diameter error

### Experimental Plan

**Phase 1:** Train segmentation model and compare against current
detection pipeline.

**Phase 2:** Deploy segmentation as an experimental feature for
side-by-side comparison.

**Phase 3:** Replace the existing detection architecture if
segmentation demonstrates sufficient reliability.

### Results
Experiment pending.

### Sources
- [Add relevant YOLO segmentation paper/documentation]
- [Add biomedical cell-segmentation paper]
- [Add morphology/measurement paper]

### Next Steps
- Establish baseline metrics for current YOLOv8 model
- Train first segmentation model
- Define test dataset
- Compare segmentation measurements against manual measurements