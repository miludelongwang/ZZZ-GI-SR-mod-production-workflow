import os
import re
import tkinter as tk
from tkinter import filedialog, simpledialog

def natural_sort_key(s):
    """自然排序键函数（处理数字序号排序）"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def rename_images(folder_path, prefix, suffix):
    """批量重命名图片文件（按自然顺序）
    参数：
        folder_path - 图片目录路径
        prefix - 新文件名前缀
        suffix - 新文件名后缀
    """
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    
    # 过滤图片文件并自然排序
    image_files = [
        f for f in files 
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.dds'))
    ]
    image_files = sorted(image_files, key=natural_sort_key)
    
    # 初始化序号（从0开始的三位数字）
    sequence_number = 0
    
    for image_file in image_files:
        # 分解文件名和扩展名
        file_name, file_extension = os.path.splitext(image_file)
        
        # 构造新文件名（带三位序号）
        new_name = f"{prefix}{sequence_number:03d}{suffix}{file_extension}"
        
        # 构造完整路径
        old_path = os.path.join(folder_path, image_file)
        new_path = os.path.join(folder_path, new_name)
        
        try:
            # 执行重命名
            os.rename(old_path, new_path)
            print(f"成功重命名：{old_path} → {new_path}")
            sequence_number += 1  # 递增序号
            
        except Exception as e:
            print(f"重命名失败：{old_path} → 错误：{str(e)}")
            continue

def get_user_input():
    """通过弹窗获取用户输入"""
    root = tk.Tk()
    root.withdraw()
    
    # 选择文件夹
    folder = filedialog.askdirectory(
        title="请选择要重命名的图片目录",
        mustexist=True
    )
    if not folder:
        return None, None, None
    
    # 输入前缀
    prefix = simpledialog.askstring(
        "文件名前缀",
        "请输入文件名前缀：\n（留空则不添加前缀）",
        parent=root
    ) or ""
    
    # 输入后缀
    suffix = simpledialog.askstring(
        "文件名后缀",
        "请输入文件名后缀：\n（留空则不添加后缀）",
        parent=root
    ) or ""
    
    root.destroy()
    return folder, prefix, suffix

if __name__ == "__main__":
    print("=== 批量重命名程序 ===")
    
    # 获取用户输入
    folder_path, prefix, suffix = get_user_input()
    if not folder_path:
        print("操作已取消")
        exit()
    
    print(f"目标目录：{os.path.abspath(folder_path)}")
    print(f"文件名格式：{prefix}[序号]{suffix}.扩展名")
    
    # 执行重命名
    rename_images(folder_path, prefix, suffix)
    print("处理完成！")
    
    # 显示完成提示
    tk.messagebox.showinfo("完成", "文件重命名操作已完成")
