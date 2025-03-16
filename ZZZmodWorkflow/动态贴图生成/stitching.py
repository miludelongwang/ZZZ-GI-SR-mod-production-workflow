#####拼接图片#####

from PIL import Image
import os

# ========== 用户配置区 ==========
input_folder = "./out"     # 输入文件夹
output_path = "./stitchingOutput.jpg"  # 输出路径
columns = 4                  # 每行column张（必须定义）
rows = 6                     # 每列rows张（必须定义）
imageNumber = 25                   # 需要imageNumber张图片
# ================================

# 自动创建文件夹
if not os.path.exists(input_folder):
    os.makedirs(input_folder)
    print(f"已自动创建文件夹：{input_folder}")

print(f"当前工作目录：{os.getcwd()}")

# 读取图片
try:
    images = [Image.open(os.path.join(input_folder, f)) 
            for f in sorted(os.listdir(input_folder))
            if f.endswith(('.png', '.jpg', '.jpeg'))]
except FileNotFoundError:
    print(f"错误：文件夹 {os.path.abspath(input_folder)} 不存在")
    exit()

# 校验图片数量
assert len(images) == imageNumber, f"需要192张图片，当前找到{len(images)}张"

# 获取基准尺寸
img_width, img_height = images[0].size

# 创建画布（修正变量使用）
canvas = Image.new('RGB', 
                  (columns * img_width, rows * img_height))

# 拼接图片
for row in range(rows):
    for col in range(columns):
        index = row * columns + col
        position = (col * img_width, row * img_height)
        canvas.paste(images[index], position)

# 保存结果
canvas.save(output_path, quality=95)
print(f"拼接完成！保存至：{os.path.abspath(output_path)}")

# 释放内存
for img in images:
    img.close()