##### 图片与背景合成 #####
from PIL import Image
import os
import tempfile
import re

# ============== 用户配置区域 ==============
BACKGROUND_PATH = "./background.png"    # 背景图片路径
FOREGROUND_FOLDER = "./out"             # 前景图目录（直接覆盖）
EXPECTED_BG_SIZE = (904, 1260)         # 预期背景尺寸（宽×高）
EXPECTED_FG_SIZE = (876, 1237)         # 预期前景尺寸（宽×高）
# ========================================

def natural_sort_key(s):
    """自然排序键函数（处理数字序号排序）
    参数：s - 文件名
    返回：混合类型的排序键列表
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

def validate_image(img, expected_size, img_type):
    """验证图片尺寸是否符合预期
    参数：
        img - PIL图像对象
        expected_size - 期望的(宽度, 高度)
        img_type - 图片类型描述（用于错误提示）
    """
    actual_size = img.size
    if actual_size != expected_size:
        raise ValueError(
            f"{img_type}尺寸不符！应为{expected_size}，实际为{actual_size}"
        )

def batch_composite():
    """批量合成图片到背景（按自然顺序）"""
    try:
        # 加载并验证背景图
        bg = Image.open(BACKGROUND_PATH).convert("RGBA")
        validate_image(bg, EXPECTED_BG_SIZE, "背景图片")
        print(f"✅ 背景验证通过 | 尺寸：{bg.size[0]}x{bg.size[1]}")

        # 计算居中位置
        paste_x = (EXPECTED_BG_SIZE[0] - EXPECTED_FG_SIZE[0]) // 2
        paste_y = (EXPECTED_BG_SIZE[1] - EXPECTED_FG_SIZE[1]) // 2
        paste_position = (paste_x, paste_y)

        # 获取自然排序的前景文件列表
        files = sorted(
            [f for f in os.listdir(FOREGROUND_FOLDER) 
             if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
            key=natural_sort_key
        )
        print(f"找到 {len(files)} 张待处理前景图")

        processed = 0
        for filename in files:
            fg_path = os.path.join(FOREGROUND_FOLDER, filename)
            temp_path = None
            
            try:
                with Image.open(fg_path) as fg:
                    # 验证前景尺寸
                    validate_image(fg, EXPECTED_FG_SIZE, f"前景图[{filename}]")
                    
                    # 创建临时文件（保留原始扩展名）
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=os.path.splitext(filename)[1],
                        dir=FOREGROUND_FOLDER
                    ) as tmp_file:
                        temp_path = tmp_file.name

                    # 转换前景为RGBA模式（保留透明度）
                    if fg.mode != 'RGBA':
                        fg = fg.convert('RGBA')

                    # 创建合成图像
                    composite = bg.copy()
                    composite.paste(fg, paste_position, mask=fg)
                    
                    # 转换为RGB模式保存（兼容所有格式）
                    if composite.mode == 'RGBA':
                        composite = composite.convert('RGB')
                    
                    # 保存到临时文件
                    save_params = {
                        'quality': 95,
                        'subsampling': 0 if filename.lower().endswith(('.jpg', '.jpeg')) else -1
                    }
                    composite.save(temp_path, **save_params)
                    
                    # 原子替换原文件
                    os.replace(temp_path, fg_path)
                    processed += 1
                    print(f"✅ 已合成：{filename}")

            except Exception as e:
                print(f"❌ 处理失败 {filename}: {str(e)}")
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                continue

        print(f"\n处理完成！成功合成 {processed}/{len(files)} 张图片")

    except Exception as e:
        print(f"❌ 全局错误：{str(e)}")
        if 'bg' in locals():
            bg.close()

if __name__ == "__main__":
    print("=== 图片合成程序 ===")
    print(f"背景文件：{os.path.abspath(BACKGROUND_PATH)}")
    print(f"前景目录：{os.path.abspath(FOREGROUND_FOLDER)}")
    print(f"目标尺寸：{EXPECTED_BG_SIZE} → {EXPECTED_FG_SIZE}")
    print("⚠️ 警告：此操作将直接覆盖前景文件！")
    
    if not os.path.exists(BACKGROUND_PATH):
        print(f"错误：背景图片 {BACKGROUND_PATH} 不存在")
    else:
        batch_composite()