# -*- coding: utf-8 -*-
# @Time : 2024-12-26 12:10
# @Author : 林枫
# @File : predictImg.py
import json
import time
import torch
from ultralytics import YOLO


class ImagePredictor:
    def __init__(self, weights_path, img_path, save_path="./runs/result.jpg", conf=0.5, detect_type="weed"):
        """
        初始化ImagePredictor类 - 杂草检测版（移除所有作物病害逻辑）
        :param weights_path: 权重文件路径（杂草检测模型）
        :param img_path: 输入图像路径
        :param save_path: 结果保存路径
        :param conf: 置信度阈值
        :param detect_type: 检测类型（固定为weed，杂草检测）
        """
        # 强制CPU+单精度(float32)，兼容无GPU环境
        self.model = YOLO(weights_path)
        self.model.to(device='cpu', dtype=torch.float32)
        
        self.conf = conf
        self.img_path = img_path
        self.save_path = save_path
        self.detect_type = detect_type  # 检测类型标记为杂草
        
        # 核心：杂草检测类别配置
        # 重要：这里需要根据您的weed_best.pt模型的实际类别设置
        # 如果您的模型只有1个类别（杂草），则设置为["杂草"]
        # 如果您的模型有多个类别，如["狗尾草", "稗草", "马齿苋"]等，请按实际情况设置
        self.weed_labels = ["杂草"]  # 默认单类别
        
        # 尝试获取模型的实际类别名称
        try:
            # YOLO模型的names属性包含了所有类别名称
            if hasattr(self.model, 'names') and self.model.names:
                self.weed_labels = list(self.model.names.values())
                print(f"模型类别加载成功: {len(self.weed_labels)} 个类别")
                print(f"类别列表: {self.weed_labels}")
            else:
                print("警告：模型没有类别名称，使用默认类别")
        except Exception as e:
            print(f"获取模型类别失败: {e}")

    def predict(self):
        """
        预测图像并保存结果 - 杂草检测专属，移除所有作物病害处理
        """
        start_time = time.time()
        # 核心推理：关闭半精度，强制CPU，保留原核心参数
        results = self.model(
            source=self.img_path, 
            conf=self.conf, 
            half=False,
            save_conf=True,
            device='cpu'
        )
        end_time = time.time()
        elapsed_time = end_time - start_time

        # 初始化返回结果（数值型，适配后端）
        all_results = {
            'labels': [],
            'confidences': [],
            'boxes': [],  # 新增：检测框坐标
            'allTime': elapsed_time  # 浮点数耗时（秒）
        }

        try:
            # 校验检测结果是否为空
            if len(results) == 0 or not hasattr(results[0], 'boxes'):
                print("未检测到杂草，请更换图片重试！")
                return {
                    'labels': '预测失败',
                    'confidences': 0.0,
                    'boxes': [],
                    'allTime': elapsed_time
                }

            result = results[0]
            
            # 检查是否有检测框
            if result.boxes is None or len(result.boxes) == 0:
                print("未检测到杂草，请更换图片重试！")
                return {
                    'labels': '预测失败',
                    'confidences': 0.0,
                    'boxes': [],
                    'allTime': elapsed_time
                }

            # 提取标签、置信度和坐标
            labels = result.boxes.cls.cpu().numpy()  # 类别ID
            confidences = result.boxes.conf.cpu().numpy()  # 置信度
            boxes = result.boxes.xyxy.cpu().numpy()  # 坐标[x1, y1, x2, y2]
            
            print(f"检测到 {len(labels)} 个目标")
            print(f"坐标形状: {boxes.shape}")
            
            # 校验标签/置信度/坐标是否为空
            if len(labels) == 0 or len(confidences) == 0 or len(boxes) == 0:
                print("未检测到杂草，请更换图片重试！")
                return {
                    'labels': '预测失败',
                    'confidences': 0.0,
                    'boxes': [],
                    'allTime': elapsed_time
                }

            # 映射杂草标签（根据模型类别数适配）
            label_names = []
            boxes_list = []
            
            for i, (cls, conf, box) in enumerate(zip(labels, confidences, boxes)):
                cls_int = int(cls)
                
                # 获取类别名称
                if cls_int < len(self.weed_labels):
                    label_name = self.weed_labels[cls_int]
                else:
                    label_name = f"杂草{cls_int}"  # 兜底
                
                label_names.append(label_name)
                
                # 转换坐标格式：numpy数组转Python列表
                box_list = box.tolist()
                boxes_list.append(box_list)
                
                # 调试输出
                print(f"目标 {i+1}: {label_name}, 置信度: {conf:.4f}, 坐标: {box_list}")

            # 置信度转为浮点数（适配后端BigDecimal）
            conf_values = [float(conf) for conf in confidences]

            # 组装结果
            all_results['labels'] = label_names
            all_results['confidences'] = conf_values
            all_results['boxes'] = boxes_list
            
            # 保存检测结果图片
            result.save(filename=self.save_path)
            
            print(f"检测完成，保存结果到: {self.save_path}")
            print(f"返回boxes数量: {len(boxes_list)}")

            return all_results

        except Exception as e:
            import traceback
            print(f"杂草检测过程中发生异常: {e}")
            traceback.print_exc()
            return {
                'labels': '预测失败',
                'confidences': 0.0,
                'boxes': [],
                'allTime': elapsed_time
            }


if __name__ == '__main__':
    # 测试：杂草检测模型推理
    predictor = ImagePredictor(
        "../weights/yolov11n.pt",  # 杂草检测模型（官方/自定义均可）
        "../test_weed.jpg",        # 测试杂草图片
        save_path="../runs/result.jpg",
        conf=0.5
    )
    result = predictor.predict()
    labels_str = json.dumps(result['labels'], ensure_ascii=False)
    confidences_str = json.dumps(result['confidences'], ensure_ascii=False)
    boxes_str = json.dumps(result['boxes'], ensure_ascii=False)
    print("杂草检测标签:", labels_str)
    print("置信度（数值）:", confidences_str)
    print("检测框坐标:", boxes_str)
    print("耗时（秒）:", result['allTime'])