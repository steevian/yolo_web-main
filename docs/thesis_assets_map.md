# Thesis Assets Map

## Data Engineering Artifacts
- Data issues log: `experiments/logs/data_issues.log`
- XML conversion errors: `experiments/logs/xml_convert_errors.csv`
- Data YAML validation: `experiments/logs/data_yaml_validation.md`

## Baseline Training Artifacts (Phase 2)
- Run summary: `experiments/YOLOv11-S/<run_id>/run_summary.json`
- Hyperparameters: `experiments/YOLOv11-S/<run_id>/hyperparams.json`
- Environment snapshot: `experiments/YOLOv11-S/<run_id>/environment_snapshot.json`
- Per-epoch metrics: `experiments/YOLOv11-S/<run_id>/metrics_epoch.csv`
- Curves figure: `experiments/YOLOv11-S/<run_id>/plots/metrics_curve_1280x720.png`
- Confusion matrix: `experiments/YOLOv11-S/<run_id>/plots/confusion_matrix.png`

## Planned Phase 3-5 Artifacts
- MobileNetV3 and ECA run outputs: `experiments/YOLOv11-S-MBV3/`, `experiments/YOLOv11-S-MBV3-ECA/`
- Final comparison table: `experiments/summary/comparison_metrics.md`
- Final report: `experiments/summary/实验汇总报告.md`
- Figures index: `experiments/summary/figures_index.md`
