from PIL import Image
import os
import tempfile
import re
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import traceback

# ========== 全局配置 ==========
file_exts = ('.jpg', '.png', '.jpeg', '.webp')  # 支持的文件格式
# =============================

def safe_open_image(path):
    """安全打开图片文件，处理特殊字符"""
    try:
        return Image.open(path)
    except Exception as e:
        print(f"无法打开文件 [{path}]: {str(e)}")
        return None

def select_input_folder():
    """弹窗选择图片目录"""
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(
        title="请选择需要处理的图片目录",
        mustexist=True
    )
    root.destroy()
    return folder if folder else None

def natural_sort_key(s):
    """自然排序键函数，用于实现人类直觉排序"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def get_crop_settings():
    """弹窗获取裁剪设置"""
    root = tk.Tk()
    root.withdraw()
    
    # 第一步：选择裁剪模式
    mode = simpledialog.askinteger(
        "裁剪模式",
        "请选择裁剪模式:\n\n"
        "1. 比例裁剪 (如16:9)\n"
        "2. 固定尺寸裁剪\n\n"
        "请输入数字 (1-2):",
        minvalue=1,
        maxvalue=2
    )
    
    if mode is None:  # 用户取消
        return None, None, None
    
    # 第二步：获取具体参数
    if mode == 1:
        # 比例模式
        while True:
            ratio_input = simpledialog.askstring(
                "比例设置",
                "请输入裁剪比例（格式：宽度:高度）\n示例：16:9"
            )
            if ratio_input is None:  # 用户取消
                return None, None, None
            
            try:
                w, h = map(int, ratio_input.split(':'))
                if w <= 0 or h <= 0:
                    raise ValueError
                crop_ratio = (w, h)
                target_size = None
                break
            except:
                messagebox.showerror("错误", "无效的比例格式，请重新输入")
    else:
        # 固定尺寸模式
        while True:
            width = simpledialog.askinteger("宽度设置", "请输入目标宽度（像素）:", minvalue=1)
            if width is None: return None, None, None
            
            height = simpledialog.askinteger("高度设置", "请输入目标高度（像素）:", minvalue=1)
            if height is None: return None, None, None
            
            crop_ratio = None
            target_size = (width, height)
            break
    
    # 第三步：选择定位模式
    position = simpledialog.askinteger(
        "定位方式",
        "请选择裁剪定位:\n\n"
        "1. 左边 (垂直居中)\n"
        "2. 中间\n"
        "3. 右边 (垂直居中)\n"
        "4. 自定义坐标\n"
        "5. 左上角\n"
        "6. 右下角\n\n"
        "请输入数字 (1-6):",
        minvalue=1,
        maxvalue=6
    )
    
    return crop_ratio, target_size, position

def get_crop_position(img_width, img_height, crop_w, crop_h, position_mode):
    """根据定位模式计算坐标"""
    if position_mode == 1:   # 左边垂直居中
        return (0, (img_height - crop_h)//2)
    elif position_mode == 2: # 中间
        return ((img_width - crop_w)//2, (img_height - crop_h)//2)
    elif position_mode == 3: # 右边垂直居中
        return (img_width - crop_w, (img_height - crop_h)//2)
    elif position_mode == 4: # 自定义坐标
        left = simpledialog.askinteger("左边距", "左边距 (像素):", 
                                      minvalue=0, maxvalue=img_width-crop_w)
        top = simpledialog.askinteger("上边距", "上边距 (像素):", 
                                     minvalue=0, maxvalue=img_height-crop_h)
        return (left, top) if left is not None and top is not None else None
    elif position_mode == 5: # 左上角
        return (0, 0)
    elif position_mode == 6: # 右下角
        return (img_width - crop_w, img_height - crop_h)

def calculate_crop_box(img_width, img_height, crop_ratio, target_size, position_mode):
    """计算裁剪区域"""
    try:
        # 计算裁剪尺寸
        if crop_ratio:
            ratio = crop_ratio[0] / crop_ratio[1]
            if img_width / img_height > ratio:
                crop_h = img_height
                crop_w = int(crop_h * ratio)
            else:
                crop_w = img_width
                crop_h = int(crop_w / ratio)
        else:
            crop_w = min(target_size[0], img_width)
            crop_h = min(target_size[1], img_height)

        # 获取定位坐标
        position = get_crop_position(img_width, img_height, crop_w, crop_h, position_mode)
        if position is None:
            return None

        left, top = position
        return (left, top, left + crop_w, top + crop_h)
    except Exception as e:
        messagebox.showerror("计算错误", f"区域计算失败: {str(e)}")
        return None

def batch_crop_images(input_folder):
    """批量裁剪主逻辑"""
    if not input_folder or not os.path.isdir(input_folder):
        messagebox.showerror("错误", "无效的目录路径")
        return

    try:
        files = sorted([f for f in os.listdir(input_folder) 
                      if f.lower().endswith(file_exts)],
                      key=natural_sort_key)
    except Exception as e:
        messagebox.showerror("错误", f"读取目录失败: {str(e)}")
        return

    # 获取裁剪设置
    crop_ratio, target_size, position_mode = get_crop_settings()
    if not all([crop_ratio or target_size, position_mode]):
        messagebox.showinfo("信息", "操作已取消")
        return

    processed = 0
    for filename in files:
        # 处理特殊字符文件名
        safe_filename = filename.encode('utf-8', 'surrogateescape').decode('utf-8')
        input_path = os.path.join(input_folder, safe_filename)
        temp_path = None
        
        try:
            print(f"\n=== 正在处理: {safe_filename} ===")
            
            # 安全打开图片
            img = safe_open_image(input_path)
            if not img:
                continue
                
            with img:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp_file:
                    temp_path = tmp_file.name
                
                # 计算裁剪区域
                original_width, original_height = img.size
                print(f"原始尺寸: {original_width}x{original_height}")
                crop_box = calculate_crop_box(
                    original_width, original_height,
                    crop_ratio, target_size, position_mode
                )
                
                # 严格验证裁剪框
                if not crop_box:
                    print(f"⏭️ 跳过：未获取到有效裁剪区域")
                    continue
                
                if (crop_box[0] < 0 or crop_box[1] < 0 or
                    crop_box[2] > original_width or crop_box[3] > original_height):
                    print(f"⚠️ 无效裁剪框：{crop_box}，已自动修正")
                    crop_box = (
                        max(0, crop_box[0]),
                        max(0, crop_box[1]),
                        min(original_width, crop_box[2]),
                        min(original_height, crop_box[3])
                    )
                
                print(f"最终裁剪区域: {crop_box}")
                
                # 执行裁剪
                cropped = img.crop(crop_box)
                
                # 保存文件
                save_args = {'quality': 95}
                if img.format == 'JPEG':
                    save_args['subsampling'] = 0
                
                # 保留元数据（兼容处理）
                exif = img.info.get('exif', b'')
                cropped.save(temp_path, exif=exif, **save_args)
                
                # 覆盖原始文件
                os.replace(temp_path, input_path)
                processed += 1
                print(f"✅ 处理成功 | 新尺寸: {cropped.size[0]}x{cropped.size[1]}")

        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            traceback.print_exc()
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")

    messagebox.showinfo("完成", f"成功处理 {processed}/{len(files)} 张图片")

if __name__ == "__main__":
    # 初始化GUI
    root = tk.Tk()
    root.withdraw()
    
    # 显示警告
    if not messagebox.askokcancel("警告", "此操作将直接覆盖原始文件！\n请确认已做好备份！"):
        exit()
    
    # 选择目录
    input_folder = select_input_folder()
    if not input_folder:
        messagebox.showinfo("信息", "操作已取消")
        exit()
    
    # 执行裁剪
    try:
        batch_crop_images(input_folder)
    except Exception as e:
        messagebox.showerror("致命错误", f"程序崩溃: {str(e)}")
    finally:
        root.destroy()