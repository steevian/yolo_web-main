# 轻量化模块结构（已执行）

## 当前核心模块

- `yolo_weed_detection_flask`：后端核心（Flask + SQLite + YOLOv11）
- `yolo_weed_detection_vue`：前端核心（Vue + Vite）

## 已完成的结构优化

### 1) 删除历史模块
- 已删除：`yolo_weed_detection_springboot/`
- 保留：`yolo_weed_detection_springboot.zip`（按需留档）

### 2) Flask 侧模块化拆分（新增）
- `yolo_weed_detection_flask/core/settings.py`
  - 统一读取 `FLASK_HOST`、`PORT`、`SQLITE_DB_PATH`
- `yolo_weed_detection_flask/core/database.py`
  - 统一 SQLite 连接与性能 PRAGMA（WAL / busy_timeout 等）
- `yolo_weed_detection_flask/main.py`
  - 业务路由与推理流程主入口（保持原主链路）
- `yolo_weed_detection_flask/user_manager.py`
  - 用户相关数据库访问统一复用 core 数据库连接

## 运行入口

- 后端：`yolo_weed_detection_flask/main.py`
- 前端：`yolo_weed_detection_vue` 下 `npm run dev`

## 兼容性说明

- 现有 `/flask/*` 接口路径保持不变
- 摄像头/视频/图片检测、记录查询删除、用户管理、上传预览主链路保持不变
