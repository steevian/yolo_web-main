## 2026-03-13 19:51:17 | Phase2 watchdog start

- mode=fresh
- checkpoint=
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-13 19:51:43 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195142
- resume=False
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_20260310_141013\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True
## 2026-03-13 19:53:34 | Phase2 watchdog start

- mode=fresh
- checkpoint=
- epochs=200, batch=6, workers=0, cache=disk, device=0

## 2026-03-13 19:53:46 | Phase2启动

- run_id=baseline_full200_fresh_20260313_195344
- resume=False
- checkpoint=D:\cyd\Desktop\yolo_web-main\experiments\YOLOv11-S\baseline_20260310_141013\weights\last.pt
- epochs=200, batch=6, workers=0, cache=disk, amp=True

## 2026-03-13 20:00:00 | Phase2恢复性判定与清理分支执行

- 判定结论：历史路径 `experiments/YOLOv11-S/baseline_full200_retry_20260311_140837/weights/last.pt` 不存在，无法恢复 140+ 轮完整状态。
- 执行分支：按规则转为“清理无效全量残留 + fresh 200轮重启”。
- 清理保留策略：仅保留 `baseline_20260310_141013`（50轮冒烟完整成果）。
- 已删除目录：
- `baseline_20260310_233358`
- `baseline_full200_fresh_20260313_122052`
- `baseline_full200_fresh_20260313_131247`
- `baseline_full200_fresh_recover_20260313_131330`

## 2026-03-13 20:00:30 | Phase2脚本重构与公平性加固

- `training/scripts/phase2_train_yolo11s.py` 已重构为唯一 Phase2 主训练脚本。
- 关键能力：
- 支持 `--resume --checkpoint` 完整断点续训（epoch/optimizer/lr状态由 Ultralytics `last.pt` 接管）。
- 自动落盘 `train.log`、`env.txt`、`hyperparams.json`、`environment_snapshot.json`、`run_summary.json`。
- 训练异常/中断自动写入 `docs/trianlog.md`，并同步更新 `docs/firstmemory.md`。
- 参数公平锁定（Phase2/3/4 对齐）：`epochs=200`、`batch=6`、`workers=0`、`cache=disk`、`device=0`、`amp=True`、`resume`按模式控制。

## 2026-03-13 20:01:00 | Phase2守护脚本精简

- `training/scripts/run_phase2_resilient.ps1` 为唯一 Phase2 守护脚本。
- 守护模式：`-Mode fresh|resume`，失败自动重试，失败详情写入 `experiments/logs/phase2_failures/`。
- 已移除冗余 Phase2 脚本：
- `run_phase2_fresh_monitor.ps1`
- `run_phase2_fresh_resilient.ps1`
- `run_phase2_monitor.ps1`
- `watch_phase2_active_progress_clean.ps1`

## 2026-03-13 20:01:20 | .gitignore精准化

- 不再整体忽略 `experiments/`，改为“忽略大文件产物 + 追踪核心文本资产”。
- 可追踪核心文件：`results.csv`、`metrics_epoch.csv`、`run_summary.json`、`args.yaml`、`hyperparams.json`、`environment_snapshot.json`、`env.txt`、`train.log`、`experiments/logs/*.json|*.md|*.csv|*.log`、`experiments/summary/*.md|*.csv`。

## 2026-03-13 20:01:40 | 本轮fresh 200启动状态

- 守护启动参数：`Mode=fresh, Epochs=200, Batch=6, Workers=0, Cache=disk, Device=0, Amp=true, MaxRestarts=500`。
- 当前活跃 run：`baseline_full200_fresh_20260313_195344`（已进入 epoch 1 训练）。

## 2026-03-13 20:02:10 | 勘误

- 19:51 与 19:53 的 `Phase2启动` 记录中 `checkpoint=` 字段来自旧逻辑自动探测展示，不代表实际使用 `--resume`。
- 已修复：fresh 模式不再写入自动探测的 checkpoint 字段，后续日志将准确反映真实训练模式。

## 2026-03-13 20:10:20 | 进度卡顿与双终端不一致排查

- 现象：出现两个训练终端，显示进度不一致，并有卡住观感。
- 根因：误开了两套守护链，导致两个 fresh run 并行训练：
- `baseline_full200_fresh_20260313_195142`
- `baseline_full200_fresh_20260313_195344`
- 处置：保留正式守护链（`MaxRestarts=500` + `--amp`）并停止误开的单次调试链（`MaxRestarts=1`）。
- 结果：当前仅保留单路训练进程（1个 powershell + 1个 python），进度来源已统一。
- 状态确认：GPU 利用率约 100%，属于正常训练而非卡死。
## 2026-03-14 23:26:42 | Phase2中断

- run_id=baseline_full200_fresh_20260313_195344
- Training interrupted by user/terminal.
