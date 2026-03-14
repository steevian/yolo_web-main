# Training Runbook (Phase by Phase)

## Scope
This runbook executes the graduation-project training plan under `training/` without touching Flask/Vue business code.

## Environment
1. Use conda env `weedweb_detection`.
2. Install phase dependencies:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe -m pip install -r training/requirements-training.txt
```

## Phase 0 (Ultralytics Local Copy)
1. Prepare editable local copy:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase0_prepare_ultralytics_custom.py --force
```
2. Register custom modules (ECA/MobileNetV3Backbone) into local copy:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase3_register_custom_modules.py
```

## Phase 1 (Done-first)
1. Smoke run:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_merge_split.py --limit 200 --limit-test 200 --clean-output
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_voc_to_yolo.py --force
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_generate_data_yaml.py --validate-only
```
2. Full run:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_merge_split.py --clean-output
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_voc_to_yolo.py --force
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase1_generate_data_yaml.py
```

## Phase 2 (Baseline YOLOv11-S)
1. Smoke 50 epochs:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase2_train_yolo11s.py --epochs 50
```
2. Full 200 epochs:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase2_train_yolo11s.py --epochs 200
```

## Phase 3 (YOLOv11-S + MobileNetV3)
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase3_train_yolo11s_mbv3.py --epochs 50
```

## Phase 4 (YOLOv11-S + MobileNetV3 + ECA)
1. Structure sanity check:
```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase4_sanity_check_forward.py --model training/configs/yolo11s_mbv3_eca.yaml --ultralytics-root training/ultralytics_custom --imgsz 640
```
2. Training:
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase4_train_yolo11s_mbv3_eca.py --epochs 50 --ultralytics-root training/ultralytics_custom
```

## Phase 5 (Evaluation & Report)
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase5_evaluate_all.py --baseline <baseline_best.pt> --mbv3 <mbv3_best.pt> --mbv3-eca <mbv3_eca_best.pt>
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase5_export_samples.py --weights <mbv3_eca_best.pt>
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase5_generate_report.py
```

## Resume Training
```powershell
C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe training/scripts/phase2_train_yolo11s.py --resume
```

## Key Outputs
- Data config: `training/configs/data_3seasonweeddet10.yaml`
- Logs: `experiments/logs/`
- Baseline runs: `experiments/YOLOv11-S/<run_id>/`
