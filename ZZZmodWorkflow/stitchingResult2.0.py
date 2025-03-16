from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import threading
import queue

class StitchingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图片拼接工具")
        self.root.geometry("800x600")

        # 创建界面组件
        self.create_widgets()
        self.setup_queue()
        
    def create_widgets(self):
        """创建界面组件"""
        # 控制面板
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, fill=tk.X)

        ttk.Button(control_frame, text="选择输入文件夹", 
                  command=self.select_input_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="设置行列", 
                  command=self.set_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="开始拼接", 
                  command=self.start_stitching).pack(side=tk.LEFT, padx=5)

        # 日志显示
        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.log_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 初始化参数
        self.input_folder = ""
        self.rows = 4
        self.cols = 4
        self.output_path = ""
        
    def setup_queue(self):
        """设置消息队列"""
        self.message_queue = queue.Queue()
        self.root.after(100, self.process_messages)

    def process_messages(self):
        """处理队列消息"""
        while not self.message_queue.empty():
            msg_type, content = self.message_queue.get()
            self.update_log(msg_type, content)
        self.root.after(100, self.process_messages)

    def update_log(self, msg_type, content):
        """更新日志"""
        tag = "info"
        if msg_type == "error":
            tag = "error"
            self.log_area.tag_config("error", foreground="red")
        elif msg_type == "success":
            tag = "success"
            self.log_area.tag_config("success", foreground="green")
            
        self.log_area.insert(tk.END, content + "\n", tag)
        self.log_area.see(tk.END)
        self.status_var.set(content)

    def select_input_folder(self):
        """选择输入文件夹"""
        self.input_folder = filedialog.askdirectory(title="选择图片文件夹")
        if self.input_folder:
            self.message_queue.put(("info", f"已选择输入文件夹：{self.input_folder}"))

    def set_grid(self):
        """设置行列数弹窗"""
        class GridDialog(tk.Toplevel):
            def __init__(self, parent):
                super().__init__(parent)
                self.parent = parent
                self.title("设置行列数")
                self.grid_values = (4, 4)  # 默认值

                ttk.Label(self, text="行数：").grid(row=0, column=0, padx=5, pady=5)
                self.row_spin = ttk.Spinbox(self, from_=1, to=20, width=5)
                self.row_spin.grid(row=0, column=1, padx=5, pady=5)
                self.row_spin.set(4)

                ttk.Label(self, text="列数：").grid(row=1, column=0, padx=5, pady=5)
                self.col_spin = ttk.Spinbox(self, from_=1, to=20, width=5)
                self.col_spin.grid(row=1, column=1, padx=5, pady=5)
                self.col_spin.set(4)

                ttk.Button(self, text="确定", command=self.on_confirm).grid(row=2, columnspan=2, pady=10)

            def on_confirm(self):
                try:
                    rows = int(self.row_spin.get())
                    cols = int(self.col_spin.get())
                    if rows < 1 or cols < 1:
                        raise ValueError
                    self.grid_values = (rows, cols)
                    self.destroy()
                except:
                    messagebox.showerror("错误", "请输入有效的正整数")

        dialog = GridDialog(self.root)
        self.root.wait_window(dialog)
        if hasattr(dialog, 'grid_values'):
            self.rows, self.cols = dialog.grid_values
            self.message_queue.put(("info", f"已设置行列数：{self.rows}行 {self.cols}列"))

    def start_stitching(self):
        """开始拼接"""
        if not self.input_folder:
            messagebox.showerror("错误", "请先选择输入文件夹")
            return

        # 选择输出路径
        self.output_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG 文件", "*.jpg"), ("PNG 文件", "*.png")]
        )
        if not self.output_path:
            return

        # 启动处理线程
        threading.Thread(
            target=self.stitch_images,
            daemon=True
        ).start()

    def stitch_images(self):
        """执行拼接操作"""
        try:
            # 读取图片
            image_files = sorted([
                f for f in os.listdir(self.input_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ])
            
            total_needed = self.rows * self.cols
            images = []
            blank_count = 0

            # 获取基准尺寸
            first_image = Image.open(os.path.join(self.input_folder, image_files[0]))
            img_width, img_height = first_image.size
            first_image.close()

            # 创建空白图片
            blank_image = Image.new('RGB', (img_width, img_height), (255, 255, 255))

            # 加载图片并处理数量
            for i, filename in enumerate(image_files):
                if i >= total_needed:
                    break
                try:
                    img = Image.open(os.path.join(self.input_folder, filename))
                    images.append(img)
                    self.message_queue.put(("info", f"已加载图片：{filename}"))
                except Exception as e:
                    images.append(blank_image.copy())
                    blank_count += 1
                    self.message_queue.put(("error", f"加载失败：{filename} - 已用空白替代"))

            # 补充空白图片
            while len(images) < total_needed:
                images.append(blank_image.copy())
                blank_count += 1

            # 创建画布
            canvas = Image.new('RGB', 
                (self.cols * img_width, self.rows * img_height),
                (255, 255, 255))

            # 拼接图片
            for row in range(self.rows):
                for col in range(self.cols):
                    index = row * self.cols + col
                    if index >= len(images):
                        continue
                    position = (col * img_width, row * img_height)
                    canvas.paste(images[index], position)
                    self.message_queue.put(("info", 
                        f"正在拼接：第{row+1}行 第{col+1}列"))

            # 保存结果
            canvas.save(self.output_path, quality=95)
            self.message_queue.put(("success", 
                f"拼接完成！保存至：{self.output_path}\n"
                f"使用空白图片数量：{blank_count}"))

            # 释放资源
            for img in images:
                img.close()
            blank_image.close()

        except Exception as e:
            self.message_queue.put(("error", f"发生错误：{str(e)}"))
            if 'canvas' in locals():
                canvas.close()

if __name__ == "__main__":
    app = StitchingApp()
    app.root.mainloop()