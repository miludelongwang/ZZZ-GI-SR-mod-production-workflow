#####调整图片尺寸#####

from PIL import Image, ImageOps
import os
import tempfile
import re

# ========== 用户配置区域 ==========
input_folder = "./out"       # 需要处理的图片目录
target_width = 876                 # 目标宽度（像素）
target_height = 1237               # 目标高度（像素）
keep_aspect_ratio = False          # 是否保持宽高比
background_color = (255, 255, 255) # 填充背景色（RGB）
resample_method = Image.LANCZOS    # 重采样方法
file_exts = ('.jpg', '.png', '.jpeg', '.webp')  # 支持的文件格式
# =================================

def resize_image(img):
    """核心缩放逻辑"""
    original_width, original_height = img.size
    
    if keep_aspect_ratio:
        # 保持比例的缩放计算
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        
        new_size = (
            int(original_width * scale_ratio),
            int(original_height * scale_ratio)
        )
        
        # 创建缩放后的图像
        resized = img.resize(new_size, resample_method)
        
        # 创建带背景的画布
        final_img = Image.new("RGB", (target_width, target_height), background_color)
        
        # 计算居中位置
        paste_position = (
            (target_width - new_size[0]) // 2,
            (target_height - new_size[1]) // 2
        )
        
        # 粘贴缩放后的图像
        final_img.paste(resized, paste_position)
        return final_img
    else:
        # 直接拉伸到目标尺寸
        return img.resize((target_width, target_height), resample_method)

def natural_sort_key(s):
    """自然排序键函数"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def batch_resize_images():
    processed = 0
    
    # 获取自然排序的文件列表
    files = sorted([f for f in os.listdir(input_folder)
                   if f.lower().endswith(file_exts)],
                   key=natural_sort_key)
    
    for filename in files:
        if not filename.lower().endswith(file_exts):
            continue
            
        input_path = os.path.join(input_folder, filename)
        temp_path = None
        
        try:
            with Image.open(input_path) as img:
                # 获取文件扩展名
                file_ext = os.path.splitext(filename)[1]
                
                # 创建带扩展名的临时文件
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_ext,
                    dir=os.path.dirname(input_path)
                ) as tmp_file:
                    temp_path = tmp_file.name

                # 处理透明通道
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert("RGB")

                # 执行缩放
                final_img = resize_image(img)
                
                # 保留EXIF信息
                exif = img.info.get('exif')
                
                # 根据扩展名设置保存格式
                save_format = 'JPEG' if file_ext.lower() in ('.jpg', '.jpeg') else file_ext[1:].upper()
                
                # 保存到临时文件
                final_img.save(
                    temp_path,
                    format=save_format,
                    exif=exif,
                    quality=95,
                    subsampling=0 if save_format == 'JPEG' else -1
                )
                
                # 覆盖原始文件
                os.replace(temp_path, input_path)
                processed += 1
                print(f"✅ 已覆盖：{filename}")

        except Exception as e:
            print(f"❌ 处理 {filename} 失败: {str(e)}")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    print(f"\n处理完成！成功覆盖 {processed} 张图片")
    print(f"输出尺寸：{target_width}x{target_height} 像素")

if __name__ == "__main__":
    print("警告：此操作将直接覆盖原始文件！")
    try:
        batch_resize_images()
    except Exception as e:
        print(f"运行时错误：{str(e)}")