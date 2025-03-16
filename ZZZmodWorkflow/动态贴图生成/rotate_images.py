##### 旋转图片 #####
import os
import re
from PIL import Image
import tempfile

def natural_sort_key(s):
    """自然排序键函数（处理数字序号排序）
    参数：s - 文件名
    返回：混合类型的排序键列表
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def rotate_images_180(folder_path):
    """批量旋转图片180度（按自然顺序）
    参数：
        folder_path - 图片目录路径
    """
    # 支持的图片格式（可扩展）
    image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    
    # 获取自然排序的文件列表
    files = sorted([f for f in os.listdir(folder_path)
                   if f.lower().endswith(image_exts)],
                   key=natural_sort_key)
    
    print(f"找到 {len(files)} 张待处理图片")
    
    processed = 0
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        temp_path = None
        
        try:
            # 创建临时文件（保留原始扩展名）
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(filename)[1],
                dir=folder_path
            ) as tmp_file:
                temp_path = tmp_file.name
            
            # 打开并旋转图片
            with Image.open(file_path) as img:
                # 旋转180度（expand=True保持原图尺寸）
                rotated = img.rotate(180, expand=False)
                
                # 保留元数据
                exif = img.info.get('exif')
                
                # 保存到临时文件
                rotated.save(
                    temp_path,
                    exif=exif,
                    quality=95,
                    subsampling=0 if img.format == 'JPEG' else -1
                )
                
            # 原子替换原文件
            os.replace(temp_path, file_path)
            processed += 1
            print(f"✅ 已旋转：{filename}")
            
        except Exception as e:
            print(f"❌ 处理失败 {filename}: {str(e)}")
            # 清理临时文件
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            continue

    print(f"\n处理完成！成功旋转 {processed}/{len(files)} 张图片")

if __name__ == "__main__":
    target_folder = "./out"  # 要处理的目录
    
    print("=== 图片批量旋转程序 ===")
    print(f"目标目录：{os.path.abspath(target_folder)}")
    print(f"旋转角度：180度")
    print(f"注意：此操作将直接覆盖原始文件！")
    
    rotate_images_180(target_folder)