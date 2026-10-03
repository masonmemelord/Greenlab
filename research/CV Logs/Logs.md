# Computer Vision Logs
## Oct 3 — Improving CV Dataset

Today’s focus is improving the computer-vision dataset before choosing or training additional models.

### Goal

Build a reliable labeled dataset that can be used to compare cell detection and future segmentation approaches against manually determined ground truth.

### Dataset priorities

- Review uploaded images for blur, low contrast, inconsistent magnification, or duplicate images.
- Keep image metadata organized by condition, timepoint, magnification, and source.
- Use manual cell coordinates as ground truth for cell detection.
- Use manually traced colony boundaries as ground truth for segmentation.
- Create a held-out validation set that is never used during training.
- Ensure each training, validation, and test split contains representative image conditions.

### Evaluation plan

Compare models using:

- Precision and recall for cell detection
- IoU and Dice coefficient for segmentation overlap
- Cell-count error
- Area measurement error
- Equivalent diameter error

### Current architectural decision

Manual tracing remains a backup and labeling workflow. It is not itself a segmentation model, but its saved outlines and coordinates can become high-quality labels for future CV experiments.

### Next Goals
Make and annotation contribution workflow. 

#### How it works (or at least how I want it to work) 
1. User manualy traces cell/colony
2. Optional "Contribute this annotation" checkbox
3. Submission API + consent + image/trace metadata
4. Unreviewed data storage
5. Quality checks + admin (me) approval
6. Accepted dataset export
7. Detection or segmentation training

