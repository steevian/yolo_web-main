# 项目记忆与训练基线

## 1. 项目定位
- 仓库目录：yolo_web-main
- 项目形态：前后端分离的杂草检测系统，训练实验与业务系统共仓但逻辑分离。
- 前端：Vue 3、Vite、TypeScript、Pinia、Element Plus。
- 后端：Flask、Flask-Cors、Flask-SocketIO、SQLite、JWT。
- 检测推理：Ultralytics YOLO、Torch、OpenCV、NumPy、Pillow。
- 训练实验：统一放在 training 与 experiments 下，不直接改业务目录。

## 2. 目录职责总览

### 2.1 业务目录
- yolo_weed_detection_flask：后端服务入口、检测接口、记录管理、用户与权限。
- yolo_weed_detection_vue：前端页面、训练管理界面、检测与历史页面。
- data：原始数据集目录，包含 2021、2022、2023 三年数据。
- reference：参考项目，不是当前主运行入口。
- _legacy_archive：历史备份与旧结果归档。

### 2.2 训练目录
- training/configs：数据配置、复现实验配置、模型结构配置。
- training/scripts：phase0 到 phase5 的训练、评测、守护与链式执行脚本。
- training/lib：训练记录、环境快照、曲线图与混淆矩阵整理工具。
- training/models：自定义模型模块，当前包括 ECA 与 MobileNetV3 backbone 相关实现。
- training/ultralytics_custom：本地 ultralytics 副本，用于 phase4/phase5 自定义模块注册场景。

### 2.3 实验目录
- experiments/YOLOv11-S：基线模型各次训练 run。
- experiments/YOLOv11-S-MBV3：MobileNetV3 改进版训练 run。
- experiments/YOLOv11-S-MBV3-ECA：ECA 改进版训练 run。
- experiments/logs：数据校验、训练守护、失败记录、实时状态与活动进度日志。
- experiments/summary：对比指标、图表索引、样例导出、实验汇总报告。

## 3. training 目录功能基线

### 3.1 配置文件
- training/configs/data_3seasonweeddet10.yaml：正式训练使用的数据集入口。
- training/configs/data_3seasonweeddet10_aligned.yaml：对齐校验版数据配置。
- training/configs/reproducibility.yaml：随机种子与确定性设置基线。
- training/configs/yolo11s_mbv3.yaml：MobileNetV3 改进版结构配置。
- training/configs/yolo11s_mbv3_eca.yaml：ECA 改进版结构配置。

### 3.2 核心脚本
- phase0_prepare_ultralytics_custom.py：复制本地 ultralytics 工作副本。
- phase1_merge_split.py：合并与划分数据集。
- phase1_voc_to_yolo.py：VOC/XML 转 YOLO 标签。
- phase1_generate_data_yaml.py：生成并校验 data.yaml。
- phase2_train_yolo11s.py：YOLOv11-S 基线训练主脚本。
- phase3_train_yolo11s_mbv3.py：MobileNetV3 改进版训练脚本。
- phase4_train_yolo11s_mbv3_eca.py：ECA 改进版训练脚本。
- phase4_sanity_check_forward.py：phase4 结构与前向健全性检查。
- phase5_evaluate_all.py：统一评测三模型。
- phase5_export_samples.py：导出测试样例。
- phase5_generate_report.py：生成实验汇总 Markdown 报告。

### 3.3 守护与编排脚本
- run_phase2_fresh_resilient.ps1：基线 fresh 训练守护入口，负责 strict-batch 新开训练、失败记录、失败 run 清理、活动进度日志输出。
- run_phase2_fresh_monitor.ps1：phase2 训练巡检与重拉起脚本，输出 GPU 与进程状态。
- watch_phase2_active_progress_clean.ps1：清洗乱码后的实时训练终端观察脚本。
- run_formal_200_pipeline.ps1：正式 200 轮全流程串联执行脚本。
- run_phase3_to_phase5_chain.ps1：phase3 后续链式执行。
- run_phase4_to_phase5_chain.ps1：phase4 后续链式执行。
- run_phase2_resilient.ps1 与 run_phase2_monitor.ps1：旧的 checkpoint 续训守护链，当前不应用于正式公平基线。

### 3.4 支撑库
- training/lib/experiment_logger.py：run_id、环境快照、run_summary、results.csv 归一化输出。
- training/lib/plotter.py：训练曲线图与混淆矩阵归档。

## 4. experiments 目录功能基线

### 4.1 logs
- data_yaml_validation.md：数据配置校验结果。
- data_yaml_validation_aligned.md：对齐版数据校验结果。
- xml_convert_errors.csv：VOC 转换错误记录。
- phase2_active_progress.log：当前活跃训练 attempt 的统一进度日志。
- phase2_active_attempt.json：当前活跃 attempt 的状态描述。
- phase2_monitor_status.json：巡检状态快照，包含进程数、GPU、attempt 信息。
- phase2_monitor_heartbeat.log：巡检心跳。
- phase2_failures_fresh：fresh strict-batch 失败 attempt 记录。
- phase2_failures：旧 resume 模式失败记录。

### 4.2 各模型 run 根目录
- experiments/YOLOv11-S：基线 run，包含历史 50 轮冒烟 run 与当前正式 run。
- experiments/YOLOv11-S-MBV3：MobileNetV3 run。
- experiments/YOLOv11-S-MBV3-ECA：ECA run。

### 4.3 summary
- comparison_metrics.csv：三模型统一指标汇总表。
- comparison_metrics.md：对比指标 Markdown 版。
- experiments/summary/实验汇总报告.md：自动生成实验说明与结论草稿。
- figures_index.md：图表与样例索引。
- samples：导出样例图。

## 5. 已确认的数据与实验事实
- 正式 full 数据划分结果：train=5654，val=998，test=1784。
- 当前 full test split 实际仅覆盖 8 类，缺少 ID 1 与 4；这是 2023 原始数据覆盖事实，不是 Phase1 脚本错误。
- 早期 smoke test 的结果只用于链路验证，不能直接作为论文正式结论。
- 当前正式对比要求三模型除结构差异外，其余训练参数保持一致。

## 6. 公平性关键决策
- 放弃此前“前 20 轮 batch=8，后续再改 batch=6”的基线结果。
- 该结果不再作为正式对比依据，因为存在 batch 混用，破坏同参公平性。
- 正式基线要求：YOLOv11-S 必须从 yolo11s.pt 全新启动，epochs=200，batch=6，resume=false，strict-batch=true。
- 训练异常时不允许降 batch 续训；失败 run 直接废弃并清理，随后重新 fresh 启动。
- 当前实时训练统一以 phase2_active_progress.log 作为唯一进度观察入口，避免 stdout/stderr 分裂与旧 attempt 残留误导。

## 7. 当前训练策略与抗崩溃基线
- 守护入口：training/scripts/run_phase2_fresh_resilient.ps1。
- 巡检入口：training/scripts/run_phase2_fresh_monitor.ps1。
- 实时终端入口：training/scripts/watch_phase2_active_progress_clean.ps1。
- 固定环境保护项：KMP_DUPLICATE_LIB_OK、OMP_NUM_THREADS、MKL_SERVICE_FORCE_INTEL、PYTHONUTF8、PYTHONIOENCODING。
- strict-batch 已开启：内存错误不会自动降 batch。
- 失败 run 可自动清理，避免磁盘被无效中间产物持续占用。
- 当前清洗版观察终端会保留轮次、显存、loss、batch 进度、速度与 ETA，并去除乱码进度条块。

## 8. 本机环境快照
- 主机：Redmi G 2022。
- 系统：Windows 11 家庭中文版 10.0.26100。
- CPU：AMD Ryzen 7 6800H。
- 内存：16GB。
- GPU：NVIDIA GeForce RTX 3060 Laptop GPU。
- Python 环境：weedweb_detection。
- Python：3.11.x。
- torch：2.9.1。
- torchvision：0.24.1。
- ultralytics：8.4.7。

## 9. 当前可直接使用的结论
- 业务系统与训练系统已完成物理分离，训练不应改动前后端业务目录。
- 正式 baseline 的唯一合法路径是 fresh strict-batch 全量训练。
- 当前最应关注的实验状态文件是 experiments/logs/phase2_active_progress.log 与 experiments/logs/phase2_monitor_status.json。
- 若后续要生成论文正式结论，应在三模型都完成统一 200 轮正式训练后，再执行 phase5 统一评测与报告生成。

## 10. 近期状态记录
- 2026-03-11：已停止旧 resume 守护链与失败重试链。
- 2026-03-11：已清空 baseline_full200_fresh 与 baseline_full200_retry 残留 run，重新从零启动正式 baseline。
- 2026-03-11：已将 phase5_generate_report.py 中过时的 batch=8 描述修正为 batch=6。
- 2026-03-11：已新增统一 active progress 机制与清洗版实时终端，避免再次盯错旧日志或错误流。
