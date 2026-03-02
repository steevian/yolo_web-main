import os
import fileinput
from pathlib import Path

# ===================== 核心配置（无需修改，已适配你的路径） =====================
PROJECT_ROOT = r"D:\cyd\Desktop\yolo_web-main"
# 排除无关目录（避免修改Git/依赖/编译文件）
EXCLUDE_DIRS = {".git", "node_modules", "dist", "target", "__pycache__", "venv", "env"}
# 文件夹重命名映射
FOLDER_RENAME_MAP = {
    "yolo_weedDetection_detection_vue": "yolo_weed_detection_vue",
    "yolo_weedDetection_detection_flask": "yolo_weed_detection_flask",
    "weeddetection": "weeddetection",
    "weedDetection": "weedDetection"
}
# 文本替换映射（全覆盖所有变体）
TEXT_REPLACE_MAP = [
    ("WeedDetection", "WeedDetection"),  # 大驼峰（类名/组件名）
    ("weedDetection", "weedDetection"),  # 小驼峰（变量/路径）
    ("weeddetection", "weeddetection"),  # 全小写（文件夹/路径）
    ("Weeddetection", "Weeddetection")   # 边缘变体（兜底）
]
# 支持的文本文件类型（避免修改二进制文件）
SUPPORTED_EXTENSIONS = {".java", ".py", ".vue", ".ts", ".js", ".yml", ".yaml", ".properties", ".json", ".md", ".txt"}

# ===================== 核心功能（无需修改） =====================
def rename_folders():
    """递归重命名所有目标文件夹"""
    print("【1/3】开始重命名文件夹...")
    folder_paths = []
    # 先收集所有需要重命名的文件夹（先深后浅，避免外层影响内层）
    for root, dirs, _ in os.walk(PROJECT_ROOT, topdown=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for dir_name in dirs:
            if dir_name in FOLDER_RENAME_MAP:
                old_path = os.path.join(root, dir_name)
                new_name = FOLDER_RENAME_MAP[dir_name]
                new_path = os.path.join(root, new_name)
                folder_paths.append((old_path, new_path))
    # 执行重命名
    for old_path, new_path in folder_paths:
        if not os.path.exists(new_path):
            os.rename(old_path, new_path)
            print(f"✅ 重命名：{old_path} → {new_path}")
    print("文件夹重命名完成！")

def replace_text_in_files():
    """递归替换所有文件内的关键词"""
    print("\n【2/3】开始替换文件内文本...")
    file_count = 0
    for root, _, files in os.walk(PROJECT_ROOT):
        if any(excl in root for excl in EXCLUDE_DIRS):
            continue
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix not in SUPPORTED_EXTENSIONS:
                continue
            # 替换文本并写回文件
            try:
                with fileinput.FileInput(file_path, inplace=True, encoding="utf-8") as f:
                    for line in f:
                        for old_text, new_text in TEXT_REPLACE_MAP:
                            line = line.replace(old_text, new_text)
                        print(line, end="")
                file_count += 1
            except Exception as e:
                print(f"⚠️ 跳过无法处理的文件：{file_path} → {e}")
    print(f"文本替换完成！共处理 {file_count} 个文件")

def verify_modification():
    """验证是否有旧关键词残留"""
    print("\n【3/3】验证修改结果...")
    residual_files = []
    for root, _, files in os.walk(PROJECT_ROOT):
        if any(excl in root for excl in EXCLUDE_DIRS):
            continue
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in SUPPORTED_EXTENSIONS:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if any(old in content for old, _ in TEXT_REPLACE_MAP):
                        residual_files.append(file_path)
    if residual_files:
        print(f"❌ 发现 {len(residual_files)} 个文件仍有旧关键词：")
        for f in residual_files:
            print(f"  - {f}")
    else:
        print("✅ 所有文件无旧关键词残留！")

# ===================== 执行入口 =====================
if __name__ == "__main__":
    confirm = input(f"即将修改项目：{PROJECT_ROOT}\n输入 'yes' 确认执行（否则退出）：")
    if confirm.lower() != "yes":
        print("❌ 用户取消操作")
        exit(0)
    try:
        rename_folders()
        replace_text_in_files()
        verify_modification()
        print("\n🎉 本地修改全部完成！请按步骤验证项目功能。")
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{e}")