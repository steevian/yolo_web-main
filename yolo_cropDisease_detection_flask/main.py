# -*- coding: utf-8 -*-
# @Time : 2024-12-2024/12/26 23:21改
# @File : main.py
# 核心修正1：跳过SSL证书验证，彻底解决模型下载/网络请求的SSL报错
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import json
import os
import subprocess
import cv2
import requests
import torch
import numpy as np
import sqlite3
import uuid
import shutil
from datetime import datetime
from flask import Flask, Response, request, jsonify, send_from_directory
from ultralytics import YOLO
from flask_socketio import SocketIO, emit
import jwt
import hashlib
from user_manager import UserManager
from flask_cors import CORS

class DatabaseManager:
    """SQLite 数据库管理器 - 修复路径问题版本"""
    def __init__(self, db_path='weed_detection.db', base_dir=None):
        # 如果提供了base_dir，使用它；否则使用当前文件所在目录
        if base_dir:
            self.BASE_DIR = base_dir
        else:
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # 数据库路径
        self.db_path = os.path.join(self.BASE_DIR, db_path)
        
        self.init_database()
        print(f"✅ 数据库管理器初始化完成: {self.db_path}")
    
    # 在 DatabaseManager 类的 init_database 方法中添加时区支持
    def init_database(self):
        """初始化数据库表（带时区支持）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 🔥 设置数据库连接时区（SQLite本身不支持，但可以在应用层处理）
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 🔥 创建带时区信息的时间戳字段
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                out_video TEXT,
                conf REAL,
                start_time DATETIME NOT NULL,  -- 存储为UTC时间
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))  -- 自动使用本地时间
            )
        ''')
        
        conn.commit()
        conn.close()

    def convert_to_relative_path(self, path):
        """将绝对路径转换为相对于BASE_DIR的相对路径"""
        if not path:
            return path
        
        try:
            # 如果是绝对路径且包含BASE_DIR，转换为相对路径
            if os.path.isabs(path) and path.startswith(self.BASE_DIR):
                relative_path = os.path.relpath(path, self.BASE_DIR)
                # 统一使用正斜杠
                return '/' + relative_path.replace('\\', '/')
            
            # 如果已经是相对路径（以/开头），直接返回
            if path.startswith('/'):
                return path
            
            # 其他情况返回原值
            return path
        except Exception as e:
            print(f"⚠️  路径转换失败 {path}: {e}")
            return path

    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 图片检测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS img_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                input_img TEXT NOT NULL,
                out_img TEXT,
                label TEXT,
                confidence REAL,
                all_time REAL,
                conf REAL,
                start_time DATETIME NOT NULL,
                detections TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 视频检测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                input_video TEXT NOT NULL,
                out_video TEXT,
                conf REAL,
                start_time DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 摄像头检测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                out_video TEXT,
                conf REAL,
                start_time DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ 数据库初始化完成: {self.db_path}")
    
    def add_img_record(self, data):
        """添加图片检测记录 - 修复路径版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 转换路径为相对路径
            input_img = self.convert_to_relative_path(data.get('inputImg', ''))
            out_img = self.convert_to_relative_path(data.get('outImg', ''))
            
            # 转换数据格式
            label = data.get('label', '')
            if isinstance(label, list):
                label = json.dumps(label, ensure_ascii=False)
            
            confidence = data.get('confidence', 0.0)
            if isinstance(confidence, list):
                confidence = json.dumps(confidence, ensure_ascii=False)
            
            # 调试信息
            print(f"📊 保存图片记录:")
            print(f"  - 原始inputImg: {data.get('inputImg', '')}")
            print(f"  - 转换后inputImg: {input_img}")
            print(f"  - outImg: {out_img}")
            
            cursor.execute('''
                INSERT INTO img_records 
                (username, input_img, out_img, label, confidence, all_time, conf, start_time, detections)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('username', ''),
                input_img,
                out_img,
                label,
                confidence,
                data.get('allTime', 0.0),
                data.get('conf', 0.5),
                data.get('startTime', ''),
                json.dumps(data.get('detections', []), ensure_ascii=False) if data.get('detections') else ''
            ))
            
            conn.commit()
            record_id = cursor.lastrowid
            
            print(f"✅ 图片记录保存成功，ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ 保存图片记录失败: {e}")
            conn.rollback()
            raise e
            
        finally:
            conn.close()
    
    def get_img_records(self, page=1, page_size=10, username=None, search_label=None):
        """获取图片检测记录（分页）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        if search_label:
            conditions.append("label LIKE ?")
            params.append(f"%{search_label}%")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 计算总数
        cursor.execute(f"SELECT COUNT(*) as total FROM img_records {where_clause}", params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        
        query = f'''
            SELECT * FROM img_records 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        cursor.execute(query, params + [page_size, offset])
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            # 尝试解析 JSON 字段
            try:
                if record.get('label'):
                    record['label'] = json.loads(record['label'])
                if record.get('confidence'):
                    record['confidence'] = json.loads(record['confidence'])
                if record.get('detections'):
                    record['detections'] = json.loads(record['detections'])
            except:
                pass  # 如果解析失败，保持原样
            records.append(record)
        
        conn.close()
        
        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def delete_img_record(self, record_id):
        """删除图片检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM img_records WHERE id = ?", (record_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def add_video_record(self, data):
        """添加视频检测记录 - 增强版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 转换路径为相对路径
            input_video = self.convert_to_relative_path(data.get('inputVideo', ''))
            out_video = self.convert_to_relative_path(data.get('outVideo', ''))
            
            # 调试信息
            print(f"📊 保存视频记录:")
            print(f"  - 原始inputVideo: {data.get('inputVideo', '')}")
            print(f"  - 转换后inputVideo: {input_video}")
            print(f"  - outVideo: {out_video}")
            
            cursor.execute('''
                INSERT INTO video_records 
                (username, input_video, out_video, conf, start_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.get('username', ''),
                input_video,
                out_video,
                data.get('conf', 0.5),
                data.get('startTime', '')
            ))
            
            conn.commit()
            record_id = cursor.lastrowid
            
            print(f"✅ 视频记录保存成功，ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ 保存视频记录失败: {e}")
            conn.rollback()
            raise e
            
        finally:
            conn.close()
    
    def get_video_records(self, page=1, page_size=10, username=None):
        """获取视频检测记录（分页）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 计算总数
        cursor.execute(f"SELECT COUNT(*) as total FROM video_records {where_clause}", params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        
        query = f'''
            SELECT * FROM video_records 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        cursor.execute(query, params + [page_size, offset])
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def delete_video_record(self, record_id):
        """删除视频检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM video_records WHERE id = ?", (record_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def add_camera_record(self, data):
        """添加摄像头检测记录 - 修复路径版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 转换路径为相对路径
            out_video = self.convert_to_relative_path(data.get('outVideo', ''))
            
            # 调试信息
            print(f"📊 保存摄像头记录:")
            print(f"  - outVideo: {out_video}")
            
            cursor.execute('''
                INSERT INTO camera_records 
                (username, out_video, conf, start_time)
                VALUES (?, ?, ?, ?)
            ''', (
                data.get('username', ''),
                out_video,
                data.get('conf', 0.5),
                data.get('startTime', '')
            ))
            
            conn.commit()
            record_id = cursor.lastrowid
            
            print(f"✅ 摄像头记录保存成功，ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ 保存摄像头记录失败: {e}")
            conn.rollback()
            raise e
            
        finally:
            conn.close()
    
    def get_camera_records(self, page=1, page_size=10, username=None):
        """获取摄像头检测记录（分页）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 计算总数
        cursor.execute(f"SELECT COUNT(*) as total FROM camera_records {where_clause}", params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        
        query = f'''
            SELECT * FROM camera_records 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        cursor.execute(query, params + [page_size, offset])
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def delete_camera_record(self, record_id):
        """删除摄像头检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM camera_records WHERE id = ?", (record_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


class VideoProcessingApp:
    # 核心优化1：固定局域网IP为192.168.0.101，端口5000
    def __init__(self, host='192.168.0.101', port=5000):
        self.app = Flask(__name__)
        # 全局开启跨域，解决前端跨域请求问题
        CORS(self.app, supports_credentials=True)
        # 核心优化2：去掉async_mode='gevent'，解决启动异步模式报错
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        self.host = host
        self.port = port
        
        # 配置JSON响应确保中文正常显示
        self.app.config['JSON_AS_ASCII'] = False
        self.app.config['JSONIFY_MIMETYPE'] = 'application/json;charset=utf-8'
        
        # 核心锚点：获取Flask项目根目录（所有路径基于此）
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # 创建必要目录（基于Flask项目根目录）
        self.create_directories()
        
        # 初始化数据库管理器 - 传递base_dir参数
        self.db_manager = DatabaseManager(base_dir=self.BASE_DIR)
        
        # 新增：初始化用户管理器
        self.user_manager = UserManager()
        
        # 核心指定：你的weed_best.pt模型路径（固定死，不修改）
        self.weights_root = os.path.join(self.BASE_DIR, "weights")
        self.weed_model_name = "weed_best.pt"
        self.weed_model_path = os.path.join(self.weights_root, self.weed_model_name)
        self.system_font_path = "C:/Windows/Fonts/msyh.ttc"
        
        # 提前加载杂草检测模型（强制加载本地模型，不存在直接报错）
        self.load_weed_model()
        
        # 根据模型实际类别设置
        self.weed_classes = ["杂草"] if not hasattr(self.weed_model, 'names') else list(self.weed_model.names.values())
        
        # 摄像头相关实例变量
        self.camera_cap = None
        self.camera_writer = None
        self.recording = False
        self.camera_lock = False  # 摄像头锁，防止重复打开
        self.camera_data = {}  # 新增：存储摄像头检测参数
        self.current_camera_video = None  # 新增：当前摄像头视频路径
        
        self.setup_routes()
        self.data = {}
        # 所有路径锚定到Flask项目根目录，解决保存到外层目录问题
        self.paths = {
            'download': os.path.join(self.BASE_DIR, 'runs/video/download.mp4'),
            'output': os.path.join(self.BASE_DIR, 'runs/video/output.mp4'),
            'camera_output': os.path.join(self.BASE_DIR, "runs/video/camera_output.avi"),
            'video_output': os.path.join(self.BASE_DIR, "runs/video/camera_output.avi"),
            'uploads': os.path.join(self.BASE_DIR, 'uploads'),
            'results': os.path.join(self.BASE_DIR, 'results'),
            'temp_result': os.path.join(self.BASE_DIR, 'runs/result.jpg')  # 临时检测结果图
        }
        # 新增：视频处理进度缓存，用于Socket实时推送
        self.video_process_progress = 0
        # 新增：当前处理的视频线程
        self.current_video_thread = None

    def create_directories(self):
        """创建必要的目录（基于Flask项目根目录）"""
        directories = [
            'runs', 'runs/video', 'runs/images', 'weights',
            'uploads', 'uploads/images', 'uploads/videos',
            'results', 'results/images', 'results/videos'
        ]
        
        for dir_name in directories:
            dir_path = os.path.join(self.BASE_DIR, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"ℹ️  确保目录存在: {dir_path}")

    def load_weed_model(self):
        """预加载杂草检测模型（强制加载本地模型，不存在直接抛出错误）"""
        try:
            # 核心修改：移除官方模型兜底，只加载指定的weed_best.pt
            if not os.path.exists(self.weed_model_path):
                raise FileNotFoundError(f"指定的模型文件不存在，请检查路径！\n模型路径：{self.weed_model_path}")
            
            print(f"ℹ️  检测到本地模型文件，开始加载: {self.weed_model_path}")
            self.weed_model = YOLO(self.weed_model_path)
            
            # 强制CPU推理（避免显卡/环境问题）
            self.weed_model.to(device='cpu', dtype=torch.float32)
            
            # 获取模型的实际类别
            if hasattr(self.weed_model, 'names') and self.weed_model.names:
                self.weed_classes = list(self.weed_model.names.values())
                print(f"✅  杂草检测模型加载成功，类别数: {len(self.weed_classes)}")
                print(f"✅  类别列表: {self.weed_classes}")
            else:
                print("⚠️  无法获取模型类别，使用默认类别: [杂草]")
                
        except Exception as e:
            print(f"❌  加载杂草模型失败: {str(e)}")
            raise SystemExit(1)  # 模型加载失败直接退出服务

    def setup_routes(self):
        """设置路由（统一管理，避免冲突）"""
        # 根路径测试接口
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        
        # 文件上传接口
        self.app.add_url_rule('/flask/upload', 'upload_file', self.upload_file, methods=['POST'])
        self.app.add_url_rule('/upload', 'upload', self.upload_file, methods=['POST'])  # 兼容原前端/upload请求
        self.app.add_url_rule('/files/upload', 'files_upload', self.upload_file, methods=['POST'])  # 兼容前端配置
        
        # 图片检测核心接口（兼容/predict和/predictImg，避免前端路径错误）
        self.app.add_url_rule('/predict', 'predict', self.predictImg, methods=['POST'])
        self.app.add_url_rule('/predictImg', 'predictImg', self.predictImg, methods=['POST'])
        
        # 模型列表接口
        self.app.add_url_rule('/file_names', 'file_names', self.file_names, methods=['GET'])
        
        # 视频检测相关
        self.app.add_url_rule('/predictVideo', 'predictVideo', self.predictVideo)
        self.app.add_url_rule('/predictCamera', 'predictCamera', self.predictCamera)
        
        # 🔥 关键修复：同时添加两个stopCamera路由
        self.app.add_url_rule('/stopCamera', 'stopCamera', self.stopCamera, methods=['GET'])
        self.app.add_url_rule('/flask/stopCamera', 'stopCamera_flask', self.stopCamera, methods=['GET'])
        
        # 测试接口
        self.app.add_url_rule('/test_detection', 'test_detection', self.test_detection, methods=['POST'])
        self.app.add_url_rule('/flask/test', 'test_connection', self.test_connection, methods=['GET'])
        
        # 记录管理接口
        self.app.add_url_rule('/flask/img_records', 'get_img_records', self.get_img_records, methods=['GET'])
        self.app.add_url_rule('/flask/img_records/<int:record_id>', 'delete_img_record', self.delete_img_record, methods=['DELETE'])
        self.app.add_url_rule('/flask/video_records', 'get_video_records', self.get_video_records, methods=['GET'])
        self.app.add_url_rule('/flask/video_records/<int:record_id>', 'delete_video_record', self.delete_video_record, methods=['DELETE'])
        self.app.add_url_rule('/flask/camera_records', 'get_camera_records', self.get_camera_records, methods=['GET'])
        self.app.add_url_rule('/flask/camera_records/<int:record_id>', 'delete_camera_record', self.delete_camera_record, methods=['DELETE'])
        
        # 新增：用户认证相关接口
        self.app.add_url_rule('/flask/login', 'login', self.user_login, methods=['POST'])
        self.app.add_url_rule('/flask/register', 'register', self.user_register, methods=['POST'])
        self.app.add_url_rule('/flask/user', 'get_all_users', self.get_all_users, methods=['GET'])
        self.app.add_url_rule('/flask/user/<username>', 'get_user_by_username', self.get_user_by_username, methods=['GET'])
        self.app.add_url_rule('/flask/user/<int:user_id>', 'update_user', self.update_user, methods=['POST'])
        self.app.add_url_rule('/flask/user/<int:user_id>', 'delete_user', self.delete_user, methods=['DELETE'])
        
        # 静态文件访问（关键：解决前端获取上传/结果文件404）
        self.app.add_url_rule('/uploads/<path:filename>', 'serve_upload', self.serve_upload)
        self.app.add_url_rule('/results/<path:filename>', 'serve_result', self.serve_result)
        self.app.add_url_rule('/runs/<path:filename>', 'serve_runs', self.serve_runs)

        # WebSocket事件
        @self.socketio.on('connect')
        def handle_connect():
            self.video_process_progress = 0  # 连接重置进度
            print("WebSocket connected! 杂草检测服务已就绪")
            emit('message', {'data': 'Connected to Weed Detection WebSocket server!'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.video_process_progress = 0  # 断开重置进度
            print("WebSocket disconnected!")

        # ========== 核心新增：监听前端的process_video指令 ==========
        @self.socketio.on('process_video')
        def handle_process_video(data):
            """接收前端视频处理请求，触发检测并实时推送进度"""
            try:
                print(f"\n📹 收到前端视频处理请求 >> {data}")
                
                # 提取前端参数
                username = data.get('username', 'default_user')
                input_video = data.get('inputVideo', '')
                conf = float(data.get('conf', 0.5))
                start_time = data.get('startTime', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # 验证参数
                if not input_video:
                    emit('message', {'data': '视频地址为空，检测失败！'})
                    emit('progress', 100)
                    return
                
                # 处理视频路径
                video_path = input_video
                if video_path.startswith(('http://', 'https://')):
                    local_path = self.download_file(video_path, os.path.join(self.paths['uploads'], 'videos/'))
                    if not local_path:
                        emit('message', {'data': '网络视频下载失败，检测终止！'})
                        emit('progress', 100)
                        return
                    video_path = local_path
                elif video_path.startswith('/'):
                    video_path = os.path.join(self.BASE_DIR, video_path.lstrip('/'))
                
                # 验证视频文件
                if not os.path.exists(video_path):
                    emit('message', {'data': f'视频文件不存在：{video_path}'})
                    emit('progress', 100)
                    return
                
                # 启动视频处理线程
                import threading
                thread = threading.Thread(
                    target=self.process_video_with_progress,
                    args=(video_path, username, conf, start_time)
                )
                thread.daemon = True
                thread.start()
                self.current_video_thread = thread
                
                emit('message', {'data': '开始处理视频，请等待...'})
                
            except Exception as e:
                print(f"❌ 视频处理指令监听出错：{str(e)}")
                emit('message', {'data': f'视频处理初始化失败：{str(e)}'})
                emit('progress', 100)
        # ========== WebSocket指令监听结束 ==========

    def serve_upload(self, filename):
        """提供上传文件访问"""
        try:
            # 构建完整的上传文件路径
            uploads_dir = self.paths['uploads']
            file_path = os.path.join(uploads_dir, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return f"文件不存在: {filename}", 404
            
            return send_from_directory(uploads_dir, filename, as_attachment=False)
        except Exception as e:
            print(f"提供上传文件访问失败: {str(e)}")
            return f"服务错误: {str(e)}", 500
    
    def serve_result(self, filename):
        """提供结果文件访问"""
        try:
            # 构建完整的结果文件路径
            results_dir = self.paths['results']
            file_path = os.path.join(results_dir, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return f"结果文件不存在: {filename}", 404
            
            return send_from_directory(results_dir, filename, as_attachment=False)
        except Exception as e:
            print(f"提供结果文件访问失败: {str(e)}")
            return f"服务错误: {str(e)}", 500
    
    def serve_runs(self, filename):
        """提供runs目录文件访问（解决检测结果图片404）"""
        try:
            # 构建完整的runs目录路径
            runs_dir = os.path.join(self.BASE_DIR, 'runs')
            file_path = os.path.join(runs_dir, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return f"运行文件不存在: {filename}", 404
            
            return send_from_directory(runs_dir, filename, as_attachment=False)
        except Exception as e:
            print(f"提供运行文件访问失败: {str(e)}")
            return f"服务错误: {str(e)}", 500

    # 新增：带进度反馈的视频处理函数
    def process_video_with_progress(self, video_path, username, conf, start_time):
        """处理视频并实时推送进度 - 修复版本"""
        try:
            print(f"🎬 开始处理视频: {video_path}")
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.socketio.emit('message', {'data': '无法打开视频文件'})
                self.socketio.emit('progress', 100)
                return
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if total_frames == 0:
                self.socketio.emit('message', {'data': '视频无有效帧'})
                self.socketio.emit('progress', 100)
                cap.release()
                return
            
            print(f"📊 视频信息: {total_frames}帧, {fps}FPS, {width}x{height}")
            self.socketio.emit('message', {'data': f'视频分析: {total_frames}帧, 开始处理...'})
            
            # 初始化输出视频
            output_dir = os.path.join(self.BASE_DIR, "runs/video")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"processed_{int(datetime.now().timestamp())}.avi")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 处理视频帧
            current_frame = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_frame += 1
                
                # 更新进度
                progress = int((current_frame / total_frames) * 100)
                self.video_process_progress = progress
                self.socketio.emit('progress', progress)
                
                # 每10帧发送一次状态更新
                if current_frame % 10 == 0:
                    self.socketio.emit('message', {'data': f'正在处理第 {current_frame}/{total_frames} 帧...'})
                
                # 执行杂草检测
                results = self.weed_model.predict(
                    source=frame,
                    conf=conf,
                    show=False,
                    device='cpu',
                    
                )
                
                # 绘制检测结果
                processed_frame = results[0].plot()
                out.write(processed_frame)
            
            # 释放资源
            cap.release()
            out.release()
            
            # 转换为MP4格式
            final_output = os.path.join(output_dir, f"final_{int(datetime.now().timestamp())}.mp4")
            try:
                subprocess.run([
                    'ffmpeg', '-i', output_path, 
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-y', final_output
                ], capture_output=True, timeout=30)
            except subprocess.TimeoutExpired:
                print("视频转换超时，使用原始文件")
                final_output = output_path
            except Exception as e:
                print(f"视频转换失败: {str(e)}")
                final_output = output_path
            
            # 复制到results目录
            result_video_name = f"video_{int(datetime.now().timestamp())}.mp4"
            result_video_dir = os.path.join(self.paths['results'], 'videos')
            result_video_path = os.path.join(result_video_dir, result_video_name)
            os.makedirs(result_video_dir, exist_ok=True)
            if os.path.exists(final_output):
                shutil.copy(final_output, result_video_path)
            elif os.path.exists(output_path):
                shutil.copy(output_path, result_video_path)
            
            # 构建访问URL
            result_url = f"/results/videos/{result_video_name}"
            
            # 保存记录到数据库
            record_data = {
                "username": username,
                "inputVideo": video_path,  # 原始路径，让DatabaseManager处理
                "outVideo": result_url,
                "conf": conf,
                "startTime": start_time
            }
            
            try:
                self.db_manager.add_video_record(record_data)
                print(f"✅ 视频记录保存成功: {result_url}")
            except Exception as db_error:
                print(f"⚠️  数据库记录保存失败，但视频已生成: {db_error}")
                # 继续处理，不要因为数据库错误中断视频处理
            
            # 通知前端处理完成
            print(f"✅ 准备发送视频结果到前端: {result_url}")
            self.socketio.emit('video_result', {'video_path': result_url})
            print(f"✅ 已发送视频结果事件")
            self.socketio.emit('message', {'data': '视频检测完成！'})
            self.socketio.emit('progress', 100)
            
            # 清理临时文件
            for temp_file in [output_path, final_output]:
                if os.path.exists(temp_file) and temp_file != result_video_path:
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                        
            print(f"✅ 视频处理完成: {result_url}")
            
        except Exception as e:
            print(f"❌ 视频处理失败: {str(e)}")
            self.socketio.emit('message', {'data': f'视频处理失败: {str(e)}'})
            self.socketio.emit('progress', 100)

    # 核心优化3：重写run方法，只显示127.0.0.1和192.168.0.101，隐藏0.0.0.0
    def run(self):
        """启动 Flask 应用"""
        print("="*60)
        print(f"🚀 杂草检测服务启动成功！")
        print(f"✅ 本地访问地址：http://127.0.0.1:{self.port}")
        print(f"✅ 局域网访问地址：http://{self.host}:{self.port}")
        print(f"📌 加载模型路径：{self.weed_model_path}")
        print(f"📌 项目根目录：{self.BASE_DIR}")
        print("="*60)
        # log_output=False 隐藏默认的0.0.0.0日志，host=0.0.0.0确保两个地址都能访问
        self.socketio.run(
            self.app, 
            host='0.0.0.0',  # 底层保持0.0.0.0，确保本地+局域网都能访问
            port=self.port, 
            allow_unsafe_werkzeug=True, 
            debug=False,
            log_output=False  # 关键：关闭SocketIO默认日志，不显示0.0.0.0
        )

    # 基础测试接口
    def index(self):
        """根路径测试接口"""
        return jsonify({"code":0, "msg":"Flask杂草检测服务正常运行", "model_path":self.weed_model_path, "base_dir":self.BASE_DIR})
    
    def upload_file(self):
        """文件上传接口（替代原来的SpringBoot上传）"""
        try:
            if 'file' not in request.files:
                return jsonify({"status": 400, "message": "没有上传文件"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"status": 400, "message": "没有选择文件"}), 400
            
            # 根据文件类型决定保存目录
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                save_dir = os.path.join(self.paths['uploads'], 'images')
            elif file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                save_dir = os.path.join(self.paths['uploads'], 'videos')
            else:
                return jsonify({"status": 400, "message": "不支持的文件类型，仅支持图片/视频"}), 400
            
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成唯一文件名，避免重复
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(save_dir, unique_filename)
            
            # 保存文件
            file.save(file_path)
            
            # 构建前端可访问的相对路径（关键：统一斜杠，避免路径错误）
            relative_path = os.path.relpath(file_path, self.BASE_DIR).replace('\\', '/')
            access_url = f"/{relative_path}"
            
            return jsonify({
                "status": 200,
                "message": "文件上传成功",
                "data": access_url
            })
            
        except Exception as e:
            return jsonify({"status": 500, "message": f"文件上传失败: {str(e)}"}), 500

    def file_names(self):
        """模型列表接口"""
        try:
            return jsonify({'weight_items': [{'name': '杂草检测模型', 'path': self.weed_model_path}]})
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return jsonify({'weight_items': []})

    def test_detection(self):
        """测试接口：直接返回检测框数据"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': '没有上传图片'}), 400
            
            file = request.files['image']
            file_path = os.path.join(self.paths['uploads'], 'images/test_temp.jpg')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            # 直接使用指定的weed模型进行检测
            results = self.weed_model(file_path, conf=0.5)
            
            detections = []
            for r in results:
                if r.boxes is not None:
                    boxes = r.boxes
                    for i, box in enumerate(boxes):
                        # 获取坐标
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = box.conf[0].item()
                        cls = int(box.cls[0].item())
                        
                        # 创建检测结果
                        detection = {
                            'id': i,
                            'weed_name': self.weed_classes[cls] if cls < len(self.weed_classes) else f'杂草{cls}',
                            'confidence': round(conf, 4),
                            'bbox': {
                                'x': int(x1),
                                'y': int(y1),
                                'width': int(x2 - x1),
                                'height': int(y2 - y1),
                                'x1': int(x1),
                                'y1': int(y1),
                                'x2': int(x2),
                                'y2': int(y2)
                            }
                        }
                        detections.append(detection)
            
            # 保存可视化结果到项目内runs目录
            result_img_path = os.path.join(self.BASE_DIR, 'runs/test_result.jpg')
            os.makedirs(os.path.dirname(result_img_path), exist_ok=True)
            result_img = results[0].plot()
            cv2.imwrite(result_img_path, result_img)
            
            return jsonify({
                'success': True,
                'message': '测试检测成功',
                'detections': detections,
                'detection_count': len(detections),
                'result_image': '/runs/test_result.jpg'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    def test_connection(self):
        """测试连接接口"""
        return jsonify({
            "status": 200,
            "message": "Flask杂草检测服务运行正常",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_loaded": os.path.exists(self.weed_model_path),
            "base_dir": self.BASE_DIR
        })

    def predictImg(self):
        """图片杂草检测核心接口"""
        try:
            # 接收参数：兼容JSON和表单提交
            data = request.get_json() if request.is_json else request.form.to_dict()
            print(f"📸 接收图片杂草检测参数: {data}")
        
            # 校验必要参数
            if 'inputImg' not in data or not data['inputImg']:
                return jsonify({
                    "status": 400,
                    "message": "缺少必要参数: inputImg",
                    "label": "",
                    "confidence": 0.0,
                    "allTime": 0.0,
                    "outImg": "",
                    "detections": [],
                    "detection_count": 0
                })
        
            # 初始化参数 - 使用服务器当前时间，不要从前端获取
            self.data.clear()
            self.data.update({
                "username": data.get('username', ''),
                "conf": float(data.get('conf', 0.5)),
                "inputImg": data['inputImg']
            })
        
            print(f"🔍 执行杂草检测，置信度: {self.data['conf']}, 原始图片路径: {self.data['inputImg']}")
        
            # ==============================================
            # 路径处理（保持不变）
            # ==============================================
            img_path = self.data["inputImg"]
            # 1. 处理Windows绝对路径
            if img_path.startswith(('D:\\', 'd:\\')):
                img_path = img_path.split('D:\\', 1)[-1].replace('\\', '/')
                img_path = os.path.join(self.BASE_DIR, img_path)
                print(f"📌 修正Windows绝对路径为: {img_path}")
            # 2. 处理/开头的相对路径
            elif img_path.startswith('/'):
                img_path = os.path.join(self.BASE_DIR, img_path.lstrip('/'))
                print(f"📌 修正/开头相对路径为: {img_path}")
            # 3. 统一替换斜杠
            img_path = img_path.replace('\\', '/')
            self.data["inputImg"] = img_path
        
            # 处理网络图片URL
            if img_path.startswith(('http://', 'https://')):
                local_path = self.download_file(img_path, os.path.join(self.paths['uploads'], 'images/'))
                if not local_path:
                    return jsonify({
                        "status": 400,
                        "message": "网络图片下载失败",
                        "label": "",
                        "confidence": 0.0,
                        "allTime": 0.0,
                        "outImg": "",
                        "detections": [],
                        "detection_count": 0
                    })
                img_path = local_path
                self.data["inputImg"] = img_path
        
            # 转换为绝对路径，最终校验文件是否存在
            img_abs_path = os.path.abspath(img_path)
            if not os.path.exists(img_abs_path):
                return jsonify({
                    "status": 404,
                    "message": f"检测图片不存在，请检查路径！\n实际检测路径：{img_abs_path}",
                    "label": "",
                    "confidence": 0.0,
                    "allTime": 0.0,
                    "outImg": "",
                    "detections": [],
                    "detection_count": 0
                })
        
            # ==============================================
            # 关键修复：统一使用服务器时间对象，而不是字符串
            # ==============================================
            # 记录检测开始时间（datetime对象）
            start_datetime = datetime.now()
        
            # 执行检测
            detections = self.direct_detection(img_abs_path)
            detection_count = len(detections)
        
            # 计算检测耗时（datetime对象相减）
            end_datetime = datetime.now()
            all_time = (end_datetime - start_datetime).total_seconds()
        
            # 处理检测结果
            labels = [d['weed_name'] for d in detections] if detections else []
            confidences = [d['confidence'] for d in detections] if detections else []
            confidence_val = confidences[0] if confidences else 0.0
            label_str = ",".join(labels) if labels else "未检测到杂草"
        
            # 保存检测结果图片
            result_img_name = f"result_{int(datetime.now().timestamp())}.jpg"
            result_img_dir = os.path.join(self.paths['results'], 'images')
            result_img_path = os.path.join(result_img_dir, result_img_name)
            os.makedirs(result_img_dir, exist_ok=True)
            if os.path.exists(self.paths['temp_result']):
                shutil.copy(self.paths['temp_result'], result_img_path)
                print(f"📸 结果图片已保存到: {result_img_path}")
        
            # 构建前端可访问的结果图URL
            out_img_url = f"/results/images/{result_img_name}"
        
            # ==============================================
            # 关键修复：保存检测记录时使用格式化的时间字符串
            # ==============================================
            # 格式化时间为标准字符串
            formatted_start_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        
            # 保存检测记录到数据库
            if detection_count > 0 or label_str != "未检测到杂草":
                record_data = {
                    "username": self.data["username"],
                    "inputImg": self.data["inputImg"],
                    "outImg": out_img_url,
                    "label": labels,
                    "confidence": confidences,
                    "allTime": all_time,
                    "conf": self.data["conf"],
                    "startTime": formatted_start_time,  # 使用格式化的时间字符串
                    "detections": detections
                }
                self.db_manager.add_img_record(record_data)
        
            # 构造成功响应
            response_data = {
                "status": 200,
                "message": f"杂草检测成功，共检测到 {detection_count} 个目标" if detection_count else "未检测到杂草",
                "outImg": out_img_url,
                "allTime": round(all_time, 4),
                "confidence": round(confidence_val, 4),
                "label": label_str,
                "confidences": [round(c,4) for c in confidences],
                "labels": labels,
                "detections": detections,
                "detection_count": detection_count
            }
        
            return jsonify(response_data)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "status": 500,
                "message": f"杂草检测出错: {str(e)}",
                "label": "",
                "confidence": 0.0,
                "allTime": 0.0,
                "outImg": "",
                "detections": [],
                "detection_count": 0
            })

    def extract_detections_from_results(self, results):
        """从检测结果中提取检测框数据"""
        detections = []
        try:
            if 'boxes' in results and results['boxes']:
                boxes = results.get('boxes', [])
                confidences = results.get('confidences', [])
                labels = results.get('labels', [])
                
                for i, (box, conf, label) in enumerate(zip(boxes, confidences, labels)):
                    if isinstance(box, (list, tuple)) and len(box) >= 4:
                        x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
                        detection = {
                            'id': i,
                            'weed_name': str(label),
                            'confidence': float(conf),
                            'bbox': {
                                'x': int(x1),
                                'y': int(y1),
                                'width': int(x2 - x1),
                                'height': int(y2 - y1),
                                'x1': int(x1),
                                'y1': int(y1),
                                'x2': int(x2),
                                'y2': int(y2)
                            }
                        }
                        detections.append(detection)
        except Exception as e:
            print(f"提取检测框失败: {e}")
        return detections

    def direct_detection(self, img_path):
        """直接使用指定模型检测（核心：替代ImagePredictor，解决兼容问题）"""
        detections = []
        try:
            print(f"📌 直接使用模型检测图片: {img_path}")
            # 使用指定的weed_best.pt模型检测
            detection_results = self.weed_model(img_path, conf=self.data.get("conf", 0.5), device='cpu')
            
            for r in detection_results:
                if r.boxes is not None:
                    boxes = r.boxes
                    for j, box in enumerate(boxes):
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        conf = box.conf[0].item()
                        cls = int(box.cls[0].item())
                        
                        detection = {
                            'id': len(detections),
                            'weed_name': self.weed_classes[cls] if cls < len(self.weed_classes) else f'杂草{cls}',
                            'confidence': round(conf, 4),
                            'bbox': {
                                'x': int(x1),
                                'y': int(y1),
                                'width': int(x2 - x1),
                                'height': int(y2 - y1),
                                'x1': int(x1),
                                'y1': int(y1),
                                'x2': int(x2),
                                'y2': int(y2)
                            }
                        }
                        detections.append(detection)
            
            print(f"✅ 直接检测到 {len(detections)} 个杂草目标")
            
            # 核心修改2：保存检测结果图片到Flask项目内的runs目录（临时文件）
            if detections:
                result_img = detection_results[0].plot()
                cv2.imwrite(self.paths['temp_result'], result_img)
            else:
                # 未检测到目标，复制原图作为结果到项目内临时路径
                shutil.copy(img_path, self.paths['temp_result'])
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ 直接检测失败: {e}")
            
        return detections

    def predictVideo(self):
        """视频杂草检测流接口【核心修改：添加真实进度计算】"""
        self.data.clear()
        self.data.update({
            "username": request.args.get('username', ''),
            "conf": float(request.args.get('conf', 0.5)),
            "startTime": request.args.get('startTime', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "inputVideo": request.args.get('inputVideo', '')
        })
        # 重置进度（关键）
        self.video_process_progress = 0
        
        # 下载前端传入的视频文件到项目内uploads
        video_path = self.data["inputVideo"]
        if video_path.startswith(('http://', 'https://')):
            local_path = self.download_file(video_path, os.path.join(self.paths['uploads'], 'videos/'))
            if not local_path:
                return Response("视频下载失败", status=400)
            video_path = local_path
            self.data["inputVideo"] = video_path
        
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            return Response(f"视频文件不存在: {video_path}", status=404)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return Response("无法打开视频文件，请检查路径！", status=400)
        
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # 核心新增：获取视频总帧数，计算真实进度
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        current_frame = 0
        
        # 初始化视频写入器（项目内路径）
        os.makedirs(os.path.dirname(self.paths['video_output']), exist_ok=True)
        video_writer = cv2.VideoWriter(
            self.paths['video_output'],
            cv2.VideoWriter_fourcc(*'XVID'),
            fps,
            (width, height)
        )

        def generate():
            nonlocal current_frame
            try:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    current_frame += 1
                    # 核心修改：计算并更新真实进度（同步推送给前端）
                    if total_frames > 0:
                        self.video_process_progress = min(int((current_frame / total_frames) * 100), 99)
                    
                    # 杂草检测（强制CPU）
                    results = self.weed_model.predict(
                        source=frame,
                        conf=self.data['conf'],
                        show=False,
                        half=False,
                        device='cpu',
                       
                    )
                    
                    # 绘制检测框和标签
                    processed_frame = results[0].plot()
                    video_writer.write(processed_frame)
                    
                    # 编码为jpg，生成视频流返回前端
                    _, jpeg = cv2.imencode('.jpg', processed_frame)
                    yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
                    
            finally:
                # 释放资源前，进度置为100%
                self.video_process_progress = 100
                # 释放资源
                self.cleanup_resources(cap, video_writer)
                self.socketio.emit('message', {'data': '杂草检测完成，正在保存视频！'})
                
                # 转换视频格式
                if os.path.exists(self.paths['video_output']):
                    for progress in self.convert_avi_to_mp4(self.paths['video_output']):
                        self.socketio.emit('progress', {'data': progress})
                
                # 保存检测后的视频到项目内results目录
                result_video_name = f"video_{int(datetime.now().timestamp())}.mp4"
                result_video_dir = os.path.join(self.paths['results'], 'videos')
                result_video_path = os.path.join(result_video_dir, result_video_name)
                os.makedirs(result_video_dir, exist_ok=True)
                if os.path.exists(self.paths['output']):
                    shutil.copy(self.paths['output'], result_video_path)
                    # 构建访问URL
                    out_video_url = f"/results/videos/{result_video_name}"
                    self.data["outVideo"] = out_video_url
                    
                    # 保存检测记录到数据库
                    self.db_manager.add_video_record(self.data)
                
                # 清理临时文件
                self.cleanup_files([self.paths['download'], self.paths['output'], self.paths['video_output']])

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def predictCamera(self):
        """摄像头实时杂草检测接口（修复版）- 在流结束时自动保存记录"""
        print("📹 开始摄像头检测...")
        
        # 检查摄像头是否已被占用
        if self.camera_lock:
            print("⚠️ 摄像头正在被其他进程占用")
            self.socketio.emit('message', {'data': '摄像头正在被其他进程占用，请稍后再试'})
            return Response("摄像头正在被其他进程占用", status=409)
        
        try:
            self.camera_lock = True
            # 关键修复：使用本地时间，并格式化为正确的字符串
            from datetime import datetime, timezone, timedelta
            
            # 获取本地时间（东八区）
            local_tz = timezone(timedelta(hours=8))
            local_time = datetime.now(local_tz)
            
            # 保存用户参数到实例变量，以便后续使用
            self.camera_data = {
                "username": request.args.get('username', 'unknown'),
                "conf": float(request.args.get('conf', 0.5)),
                # 关键修复：使用格式化的本地时间字符串
                "startTime": local_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存用户参数到实例变量，以便后续使用
            self.camera_data = {
                "username": request.args.get('username', 'unknown'),
                "conf": float(request.args.get('conf', 0.5)),
                "startTime": request.args.get('startTime', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
            
            # 生成唯一的视频文件名，避免冲突
            video_timestamp = int(datetime.now().timestamp())
            video_filename = f"camera_{video_timestamp}.avi"
            camera_output_path = os.path.join(os.path.dirname(self.paths['camera_output']), video_filename)
            
            print(f"🎬 摄像头检测开始，用户名: {self.camera_data['username']}, 置信度: {self.camera_data['conf']}")
            print(f"📁 视频将保存到: {camera_output_path}")
            
            self.recording = True

            # 初始化电脑摄像头
            print("🔧 初始化摄像头...")
            self.camera_cap = cv2.VideoCapture(0)
            if not self.camera_cap.isOpened():
                print("❌ 无法打开摄像头")
                self.camera_lock = False
                return Response("无法打开摄像头，请检查设备！", status=400)
            
            # 设置摄像头参数
            self.camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera_cap.set(cv2.CAP_PROP_FPS, 20)
            
            print(f"✅ 摄像头已打开，分辨率: 640x480, FPS: 20")
            self.socketio.emit('message', {'data': '摄像头已打开，开始实时杂草检测...'})
            
            # 初始化视频写入器（使用唯一文件名）
            os.makedirs(os.path.dirname(camera_output_path), exist_ok=True)
            self.camera_writer = cv2.VideoWriter(
                camera_output_path,
                cv2.VideoWriter_fourcc(*'XVID'),
                20,
                (640, 480)
            )
            
            # 存储视频路径以便后续保存
            self.current_camera_video = camera_output_path

            def generate():
                frame_count = 0
                try:
                    while self.recording and self.camera_cap.isOpened():
                        ret, frame = self.camera_cap.read()
                        if not ret:
                            print("❌ 摄像头读取帧失败")
                            break
                        
                        frame_count += 1
                        
                        # 实时杂草检测（强制CPU）
                        results = self.weed_model.predict(
                            source=frame,
                            imgsz=640,
                            conf=self.camera_data['conf'],
                            show=False,
                            half=False,
                            device='cpu',
                        )
                        
                        # 绘制检测框和标签
                        processed_frame = results[0].plot()
                        if self.recording:
                            self.camera_writer.write(processed_frame)
                        
                        # 编码为jpg，生成实时流返回前端
                        _, jpeg = cv2.imencode('.jpg', processed_frame)
                        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
                        
                        # 每30帧输出一次状态
                        if frame_count % 30 == 0:
                            print(f"📊 已处理 {frame_count} 帧")
                            
                except Exception as e:
                    print(f"❌ 摄像头检测异常: {e}")
                    self.socketio.emit('message', {'data': f'摄像头检测异常: {str(e)}'})
                finally:
                    print("🛑 摄像头检测流结束，清理资源...")
                    
                    # 🔥 核心修复：在流结束时立即保存记录
                    if frame_count > 0:  # 确保有处理过帧
                        self.save_camera_record_now()
                    
                    self.cleanup_camera_resources()

            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
            
        except Exception as e:
            print(f"❌ 摄像头检测初始化失败: {e}")
            self.camera_lock = False
            return Response(f"摄像头检测初始化失败: {str(e)}", status=500)

    def save_camera_record_now(self):
        """立即保存摄像头检测记录"""
        try:
            if not hasattr(self, 'current_camera_video') or not self.current_camera_video:
                print("⚠️ 没有当前摄像头视频文件，跳过保存记录")
                return
            
            video_path = self.current_camera_video
            
            if not os.path.exists(video_path):
                print(f"⚠️ 摄像头视频文件不存在: {video_path}")
                return
            
            print(f"💾 正在保存摄像头记录，视频文件: {video_path}")
            
            # 生成结果视频文件名
            result_video_name = f"camera_{int(datetime.now().timestamp())}.mp4"
            result_video_dir = os.path.join(self.paths['results'], 'videos')
            result_video_path = os.path.join(result_video_dir, result_video_name)
            os.makedirs(result_video_dir, exist_ok=True)
            
            # 转换视频格式为MP4
            try:
                print(f"🔄 转换视频格式: {video_path} -> {result_video_path}")
                subprocess.run([
                    'ffmpeg', '-i', video_path,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-y', result_video_path
                ], capture_output=True, timeout=30, check=True)
                print(f"✅ 视频格式转换成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ 视频格式转换失败: {e}")
                # 如果转换失败，尝试直接复制
                try:
                    shutil.copy(video_path, result_video_path)
                    print(f"📄 已直接复制视频文件")
                except Exception as copy_error:
                    print(f"❌ 复制视频文件失败: {copy_error}")
                    return
            except Exception as e:
                print(f"❌ FFmpeg转换异常: {e}")
                return
            
            # 构建访问URL
            result_url = f"/results/videos/{result_video_name}"
            
            # 保存记录到数据库
            if hasattr(self, 'camera_data'):
                record_data = {
                    "username": self.camera_data.get("username", "unknown"),
                    "outVideo": result_url,
                    "conf": self.camera_data.get("conf", 0.5),
                    "startTime": self.camera_data.get("startTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
            else:
                # 如果 camera_data 不存在，使用默认值
                record_data = {
                    "username": "unknown",
                    "outVideo": result_url,
                    "conf": 0.5,
                    "startTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            print(f"📊 准备保存摄像头记录到数据库: {record_data}")
            
            try:
                record_id = self.db_manager.add_camera_record(record_data)
                print(f"✅ 摄像头检测记录已保存到数据库，ID: {record_id}")
                
                # 发送WebSocket通知
                self.socketio.emit('message', {'data': f'摄像头检测记录已保存 (ID: {record_id})'})
                
            except Exception as db_error:
                print(f"❌ 数据库保存失败: {db_error}")
                # 即使数据库保存失败，也要保留视频文件
            
            # 清理临时文件（但不删除结果文件）
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"🗑️ 已清理临时视频文件: {video_path}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {e}")
                
            # 重置当前视频路径
            self.current_camera_video = None
            
        except Exception as e:
            print(f"❌ 保存摄像头记录失败: {e}")

    def stopCamera(self):
        """停止摄像头杂草检测（简化为仅设置标志）"""
        print("🛑 收到停止摄像头检测请求")
        
        try:
            # 只需设置停止标志，视频流会自然结束并保存记录
            self.recording = False
            
            response = {
                "status": 200,
                "message": "已发送停止信号，摄像头检测将停止并保存记录",
                "code": 0
            }
            
            self.socketio.emit('message', {'data': '摄像头检测即将停止...'})
            
            return jsonify(response)
            
        except Exception as e:
            print(f"❌ 停止摄像头检测异常: {e}")
            return jsonify({
                "status": 500,
                "message": f"停止摄像头检测失败: {str(e)}",
                "code": 1
            })

    def cleanup_camera_resources(self):
        """清理摄像头资源"""
        success = True
        try:
            print("🧹 清理摄像头资源...")
            
            # 释放摄像头
            if self.camera_cap is not None and self.camera_cap.isOpened():
                self.camera_cap.release()
                self.camera_cap = None
                print("✅ 摄像头已释放")
            elif self.camera_cap is not None:
                self.camera_cap = None
                print("ℹ️  摄像头引用已清理")
            
            # 释放视频写入器
            if self.camera_writer is not None:
                self.camera_writer.release()
                self.camera_writer = None
                print("✅ 视频写入器已释放")
            
            # 清理OpenCV窗口
            cv2.destroyAllWindows()
            
            # 清理临时文件
            temp_files = [
                self.paths.get('download', ''),
                self.paths.get('output', ''),
                self.paths.get('camera_output', '')
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"🗑️  已清理临时文件: {temp_file}")
                    except Exception as e:
                        print(f"⚠️  清理临时文件失败 {temp_file}: {e}")
            
            # 释放摄像头锁
            self.camera_lock = False
            print("🔓 摄像头锁已释放")
            
        except Exception as e:
            print(f"❌ 清理摄像头资源失败: {e}")
            success = False
            self.camera_lock = False  # 无论如何都要释放锁
            
        return success

    def get_img_records(self):
        """获取图片检测记录"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            username = request.args.get('username')
            search_label = request.args.get('search_label')
            
            result = self.db_manager.get_img_records(
                page=page, 
                page_size=page_size, 
                username=username, 
                search_label=search_label
            )
            
            return jsonify({
                "status": 200,
                "message": "获取记录成功",
                "records": result["records"],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"]
            })
            
        except Exception as e:
            print(f"获取图片记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"获取记录失败: {str(e)}",
                "records": [],
                "total": 0
            })

    def delete_img_record(self, record_id):
        """删除图片检测记录"""
        try:
            success = self.db_manager.delete_img_record(record_id)
            
            if success:
                return jsonify({
                    "status": 200,
                    "message": "删除记录成功"
                })
            else:
                return jsonify({
                    "status": 404,
                    "message": "记录不存在"
                })
                
        except Exception as e:
            print(f"删除图片记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"删除失败: {str(e)}"
            })

    def get_video_records(self):
        """获取视频检测记录"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            username = request.args.get('username')
            
            result = self.db_manager.get_video_records(
                page=page, 
                page_size=page_size, 
                username=username
            )
            
            return jsonify({
                "status": 200,
                "message": "获取记录成功",
                "records": result["records"],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"]
            })
            
        except Exception as e:
            print(f"获取视频记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"获取记录失败: {str(e)}",
                "records": [],
                "total": 0
            })

    def delete_video_record(self, record_id):
        """删除视频检测记录"""
        try:
            success = self.db_manager.delete_video_record(record_id)
            
            if success:
                return jsonify({
                    "status": 200,
                    "message": "删除记录成功"
                })
            else:
                return jsonify({
                    "status": 404,
                    "message": "记录不存在"
                })
                
        except Exception as e:
            print(f"删除视频记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"删除失败: {str(e)}"
            })

    def get_camera_records(self):
        """获取摄像头检测记录"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            username = request.args.get('username')
            
            result = self.db_manager.get_camera_records(
                page=page, 
                page_size=page_size, 
                username=username
            )
            
            return jsonify({
                "status": 200,
                "message": "获取记录成功",
                "records": result["records"],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"]
            })
            
        except Exception as e:
            print(f"获取摄像头记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"获取记录失败: {str(e)}",
                "records": [],
                "total": 0
            })

    def delete_camera_record(self, record_id):
        """删除摄像头检测记录"""
        try:
            success = self.db_manager.delete_camera_record(record_id)
            
            if success:
                return jsonify({
                    "status": 200,
                    "message": "删除记录成功"
                })
            else:
                return jsonify({
                    "status": 404,
                    "message": "记录不存在"
                })
                
        except Exception as e:
            print(f"删除摄像头记录失败: {e}")
            return jsonify({
                "status": 500,
                "message": f"删除失败: {str(e)}"
            })

    # 以下是用户管理方法
    def user_login(self):
        """用户登录接口"""
        try:
            data = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                return jsonify({"code": 400, "msg": "用户名和密码不能为空"})
            
            result = self.user_manager.login_user(username, password)
            return jsonify(result)
            
        except Exception as e:
            print(f"登录接口错误: {e}")
            return jsonify({"code": 500, "msg": f"服务器内部错误: {str(e)}"})
    
    def user_register(self):
        """用户注册接口"""
        try:
            data = request.get_json() or {}
            print(f"[DEBUG] 注册接口收到数据: {data}")
        
            # 提取并去除参数首尾空格
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            confirm = data.get('confirm', '').strip()
        
            # 调用用户管理的注册方法
            result = self.user_manager.register_user(
                username=username,
                password=password,
                confirm_password=confirm,
                name=data.get('name', username),
                sex=data.get('sex', ''),
                email=data.get('email', ''),
                tel=data.get('tel', ''),
                avatar=data.get('avatar', '/uploads/images/default_avatar.png')
            )
            return jsonify(result)
        
        except Exception as e:
            print(f"注册接口错误: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"code": 500, "msg": f"服务器内部错误: {str(e)}"})
    
    def get_all_users(self):
        """获取所有用户"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            search = request.args.get('search')
            
            result = self.user_manager.get_all_users(
                page=page,
                page_size=page_size,
                search=search
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"code": 500, "msg": str(e)})
    
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        try:
            result = self.user_manager.get_user_by_username(username)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"code": 500, "msg": str(e)})
    
    def update_user(self, user_id):
        """更新用户信息"""
        try:
            data = request.get_json() or {}
            
            # 构建更新数据
            update_data = {}
            for key in ['name', 'sex', 'email', 'tel', 'avatar', 'role']:
                if key in data and data[key] is not None:
                    update_data[key] = data[key]
            
            # 如果更新密码
            if 'password' in data and data['password'].strip():
                update_data['password'] = self.user_manager.hash_password(data['password'].strip())
            
            result = self.user_manager.update_user(user_id, update_data)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"code": 500, "msg": str(e)})
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            result = self.user_manager.delete_user(user_id)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"code": 500, "msg": str(e)})

    # 工具方法
    def download_file(self, url, save_dir):
        """下载文件到本地（项目内路径）"""
        os.makedirs(save_dir, exist_ok=True)
        try:
            # 处理URL中的参数，提取纯文件名
            filename = os.path.basename(url.split('?')[0])
            # 生成唯一文件名，避免重复
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            save_path = os.path.join(save_dir, unique_filename)
            
            with requests.get(url, stream=True, timeout=30, verify=False) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
            print(f"📥 文件已成功下载: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            return None

    def cleanup_temp_img(self):
        """清理图片检测临时文件"""
        try:
            img_path = self.data.get("inputImg", "")
            if os.path.exists(img_path) and 'test_temp' not in img_path:
                os.remove(img_path)
                print(f"🗑️  已清理临时图片: {img_path}")
        except Exception as e:
            print(f"清理临时图片失败: {e}")

    def convert_avi_to_mp4(self, temp_output):
        """FFmpeg转换视频格式（兼容Windows）"""
        try:
            ffmpeg_command = f"ffmpeg -i {temp_output} -vcodec libx264 {self.paths['output']} -y -loglevel error"
            process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            total_duration = self.get_video_duration(temp_output)

            for line in process.stderr:
                if "time=" in line:
                    try:
                        time_str = line.split("time=")[1].split(" ")[0]
                        h, m, s = map(float, time_str.split(":"))
                        processed_time = h * 3600 + m * 60 + s
                        if total_duration > 0:
                            progress = min(int((processed_time / total_duration) * 100), 100)
                            yield progress
                    except Exception:
                        continue
            process.wait()
        except Exception as e:
            print(f"视频格式转换失败: {e}")
        yield 100

    def get_video_duration(self, path):
        """获取视频总时长"""
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            return total_frames / fps if fps > 0 else 0
        except Exception:
            return 0

    def cleanup_files(self, file_paths):
        """批量清理临时文件"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"🗑️  已清理临时文件: {path}")
            except Exception as e:
                print(f"清理文件 {path} 失败: {e}")

    def cleanup_resources(self, cap, video_writer):
        """释放摄像头/视频写入器资源"""
        try:
            if cap and cap.isOpened():
                cap.release()
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"释放资源失败: {e}")


if __name__ == '__main__':
    # 初始化并启动Flask杂草检测服务
    try:
        weed_detection_app = VideoProcessingApp()
        weed_detection_app.run()
    except Exception as e:
        print(f"❌  Flask服务启动失败: {str(e)}")
        input("按回车键退出...")