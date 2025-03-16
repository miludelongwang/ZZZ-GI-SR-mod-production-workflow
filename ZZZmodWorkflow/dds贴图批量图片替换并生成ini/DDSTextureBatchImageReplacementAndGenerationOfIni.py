import os
import re
import shutil
from PIL import Image
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox

# ------------------------- 配置部分 -------------------------
dds_input_dir = "ddsInput"
image_input_dir = "ddsImages"
output_dir = "ddsOutput"
texconv_path = "texconv.exe"
ini_filename = "TextureMod.ini"

# TexConv参数
texconv_args = [
    "-srgb",
    "-f", "R8G8B8A8_UNORM_SRGB",
    "-y",
    "-m", "1"
]
# ----------------------------------------------------------

# ------------------------- 弹窗输入哈希值函数（循环验证）-----------------------
def get_hash_from_user():
    """通过弹窗获取用户输入的哈希值，循环直到输入有效或用户取消"""
    root = tk.Tk()
    root.withdraw()
    while True:
        user_hash = simpledialog.askstring(
            "输入哈希值",
            "请输入 IB_SlotCheck 的哈希值（8位十六进制，例如 c44d57b0）:",
            parent=root
        )
        if user_hash is None:
            root.destroy()
            return None
        if len(user_hash) == 8 and re.match(r"^[0-9a-fA-F]+$", user_hash):
            root.destroy()
            return user_hash.lower()
        else:
            messagebox.showerror("输入错误", "哈希值必须为8位十六进制字符（0-9, a-f）")
            root.destroy()
            root = tk.Tk()
            root.withdraw()

# ------------------------- 提取哈希对 -------------------------
def parse_input_hashes():
    """从ddsInput文件夹提取哈希对（hash1, hash2），忽略后缀名"""
    hash_pairs = []
    pattern = re.compile(r"(\w+)_(\w+)-R8G8B8A8_UNORM_SRGB\.\w+")
    for filename in os.listdir(dds_input_dir):
        match = pattern.match(filename)
        if match:
            hash1, hash2 = match.groups()
            hash_pairs.append((hash1, hash2))
    return hash_pairs

# ------------------------- 重命名并垂直翻转图片 -------------------------
def rename_and_flip_images(hash_pairs):
    """重命名并垂直翻转图片，返回临时文件列表（统一保存为PNG）"""
    temp_files = []
    image_files = sorted(
        [f for f in os.listdir(image_input_dir) if os.path.isfile(os.path.join(image_input_dir, f))],
        key=lambda x: x.lower()
    )
    
    if len(image_files) != len(hash_pairs):
        raise ValueError(f"图片数量不匹配：ddsImages有{len(image_files)}个，ddsInput有{len(hash_pairs)}个")

    temp_dir = os.path.join(output_dir, "_temp")
    os.makedirs(temp_dir, exist_ok=True)

    for idx, (old_name, (hash1, hash2)) in enumerate(zip(image_files, hash_pairs)):
        src_path = os.path.join(image_input_dir, old_name)
        new_name = f"{hash1}_{hash2}-R8G8B8A8_UNORM_SRGB.png"
        temp_path = os.path.join(temp_dir, new_name)
        
        try:
            with Image.open(src_path) as img:
                if img.mode in ("P", "RGBA", "LA"):
                    img = img.convert("RGB")
                flipped_img = img.transpose(Image.FLIP_TOP_BOTTOM)
                flipped_img.save(temp_path, format="PNG")
            temp_files.append(temp_path)
            print(f"[{idx+1}/{len(image_files)}] 处理完成：{old_name} -> {new_name}")
        except Exception as e:
            print(f"处理失败：{old_name} -> {new_name}（错误：{str(e)}）")
            temp_files.append(None)
    
    return temp_files

# ------------------------- 转换DDS -------------------------
def convert_to_dds(temp_files):
    """调用TexConv批量转换DDS，直接输出到output_dir"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 过滤掉None（处理失败的文件）
    valid_files = [f for f in temp_files if f is not None and os.path.exists(f)]
    
    cmd = [
        texconv_path,
        "-o", output_dir,
        *texconv_args,
        *valid_files
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("DDS转换完成！")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"TexConv转换失败：{e}")
        return None

# ------------------------- 生成INI文件 -------------------------
def generate_ini(dds_output_dir, slotcheck_hash):
    """生成INI文件（使用用户输入的哈希值）"""
    ini_path = os.path.join(output_dir, ini_filename)
    pattern = re.compile(r"(\w+)_(\w+)-R8G8B8A8_UNORM_SRGB\.dds")
    entries = []
    
    # 遍历DDS文件生成配置
    for filename in os.listdir(dds_output_dir):
        if not filename.endswith(".dds"):
            continue
        match = pattern.match(filename)
        if not match:
            continue
        hash1, hash2 = match.groups()
        entries.append(
            f"[TextureOverride_Texture_{hash1}]\n"
            f"hash = {hash1}\n"
            f"this = ResourceTexture_{hash1}\n\n"
            f"[ResourceTexture_{hash1}]\n"
            f"filename = {filename}\n"
        )
    
    # 写入INI文件
    with open(ini_path, "w") as f:
        f.write(f"[TextureOverride_IB_SlotCheck]\n")
        f.write(f"hash = {slotcheck_hash}\n")
        f.write("match_priority = 0\n")
        f.write("run = CommandListSkinTexture\n\n")
        f.write("\n".join(entries))
    print(f"INI文件已生成：{ini_path}")

# ------------------------- 主函数 -------------------------
def main():
    # 步骤0：用户输入哈希值
    slotcheck_hash = get_hash_from_user()
    if slotcheck_hash is None:
        print("用户取消输入，脚本终止。")
        return
    
    # 步骤1：提取哈希对
    try:
        hash_pairs = parse_input_hashes()
        if not hash_pairs:
            print("错误：ddsInput文件夹中未找到有效DDS文件！")
            return
    except Exception as e:
        print(f"提取哈希对失败：{str(e)}")
        return
    
    # 步骤2：重命名+翻转图片
    try:
        temp_files = rename_and_flip_images(hash_pairs)
    except ValueError as e:
        print(str(e))
        return
    
    # 步骤3：转换DDS
    dds_output_dir = convert_to_dds(temp_files)
    if not dds_output_dir:
        print("DDS转换失败，脚本终止。")
        return
    
    # 步骤4：生成INI
    try:
        generate_ini(dds_output_dir, slotcheck_hash)
    except Exception as e:
        print(f"生成INI文件失败：{str(e)}")
    
    # 步骤5：清理临时文件
    temp_dir = os.path.join(output_dir, "_temp")
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)  # 强制删除临时文件夹及内容
            print("临时文件已清理。")
        except Exception as e:
            print(f"清理临时文件失败：{str(e)}")

if __name__ == "__main__":
    main()