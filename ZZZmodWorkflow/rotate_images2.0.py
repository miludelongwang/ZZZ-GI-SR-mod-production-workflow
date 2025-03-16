import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
from PIL import Image
import threading
import queue

# 操作映射字典
OPERATIONS = {
    "顺时针旋转90°": Image.Transpose.ROTATE_90,
    "顺时针旋转180°": Image.Transpose.ROTATE_180,
    "顺时针旋转270°": Image.Transpose.ROTATE_270,
    "水平翻转": Image.Transpose.FLIP_LEFT_RIGHT,
    "垂直翻转": Image.Transpose.FLIP_TOP_BOTTOM
}

class ProcessingWindow(tk.Toplevel):
    """显示处理进度和日志的窗口"""
    def __init__(self, parent, total_files):
        super().__init__(parent)
        self.title("图片处理进度")
        self.geometry("600x400")
        
        # 初始化计数器
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0
        
        # 进度条
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, 
                                      length=400, mode='determinate')
        self.progress.pack(pady=10)
        self.progress['maximum'] = total_files
        
        # 日志显示区域
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.log_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.log_area.tag_config('success', foreground='green')
        self.log_area.tag_config('skip', foreground='blue')
        self.log_area.tag_config('error', foreground='red')
        
        # 状态标签
        self.status_var = tk.StringVar()
        status_label = ttk.Label(self, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # 队列用于线程间通信
        self.message_queue = queue.Queue()
        self.after(100, self.process_messages)

    def process_messages(self):
        """处理来自工作线程的消息"""
        while not self.message_queue.empty():
            msg_type, filename, details = self.message_queue.get()
            self.update_display(msg_type, filename, details)
        self.after(100, self.process_messages)

    def update_display(self, msg_type, filename, details=""):
        """更新日志和进度"""
        # 更新计数器
        if msg_type == 'success':
            self.success_count += 1
        elif msg_type == 'error':
            self.error_count += 1
        elif msg_type == 'skip':
            self.skip_count += 1
        
        # 更新进度条
        if msg_type in ('success', 'error'):
            self.progress['value'] += 1
        
        # 构建日志消息
        messages = {
            'start': f"开始处理 {filename}",
            'success': f"成功处理: {filename}",
            'skip': f"跳过非图片文件: {filename}",
            'error': f"处理失败: {filename} - {details}"
        }
        
        # 添加带颜色的日志
        self.log_area.insert(tk.END, messages[msg_type] + "\n", msg_type)
        self.log_area.see(tk.END)
        
        # 更新状态标签
        self.status_var.set(f"已处理 {self.progress['value']}/{self.progress['maximum']} 个文件")

    def show_summary(self):
        """显示处理结果统计窗口"""
        summary_window = tk.Toplevel(self)
        summary_window.title("处理结果统计")
        
        # 统计信息表格
        headers = ["类型", "数量", "比例"]
        total = self.progress['maximum']
        data = [
            ("成功处理", self.success_count, f"{self.success_count/total:.1%}"),
            ("处理失败", self.error_count, f"{self.error_count/total:.1%}"),
            ("跳过文件", self.skip_count, f"{self.skip_count/total:.1%}"),
            ("总计", total, "100%")
        ]
        
        # 创建表格
        for col, header in enumerate(headers):
            tk.Label(summary_window, text=header, relief="ridge").grid(row=0, column=col, sticky="nsew")
        
        for row, (label, count, percentage) in enumerate(data, start=1):
            tk.Label(summary_window, text=label, relief="groove").grid(row=row, column=0, sticky="nsew")
            tk.Label(summary_window, text=str(count), relief="groove").grid(row=row, column=1, sticky="nsew")
            tk.Label(summary_window, text=percentage, relief="groove").grid(row=row, column=2, sticky="nsew")
        
        # 添加复制按钮
        copy_btn = ttk.Button(
            summary_window,
            text="复制结果",
            command=lambda: self.copy_summary(data)
        )
        copy_btn.grid(row=row+1, columnspan=3, pady=5)
        
        # 设置网格自适应
        for col in range(3):
            summary_window.columnconfigure(col, weight=1)
    
    def copy_summary(self, data):
        """复制统计结果到剪贴板"""
        report = "图片处理结果报告\n"
        report += "-"*30 + "\n"
        report += "类型\t数量\t比例\n"
        for item in data:
            report += f"{item[0]}\t{item[1]}\t{item[2]}\n"
        self.clipboard_clear()
        self.clipboard_append(report)
        messagebox.showinfo("已复制", "统计结果已复制到剪贴板")

def select_directory():
    """弹窗选择图片目录"""
    root = tk.Tk()
    root.withdraw()
    dir_path = filedialog.askdirectory(title="选择图片目录")
    root.destroy()
    return dir_path

def select_operation(parent):
    """弹窗选择操作类型"""
    class OperationDialog(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.operation = None
            self.title("选择操作")
            
            ttk.Label(self, text="请选择要执行的操作:").pack(pady=5)
            self.combobox = ttk.Combobox(self, values=list(OPERATIONS.keys()), state="readonly")
            self.combobox.current(0)
            self.combobox.pack(padx=20, pady=10)
            
            ttk.Button(self, text="确定", command=self.on_confirm).pack(pady=5)
        
        def on_confirm(self):
            self.operation = self.combobox.get()
            self.destroy()
    
    dialog = OperationDialog(parent)
    parent.wait_window(dialog)
    return dialog.operation

def process_images(dir_path, operation, progress_window):
    """处理目录中的所有图片（在工作线程中运行）"""
    transpose_method = OPERATIONS[operation]
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    
    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        if not filename.lower().endswith(supported_exts):
            progress_window.message_queue.put(('skip', filename, ""))
            continue
        
        try:
            progress_window.message_queue.put(('start', filename, ""))
            with Image.open(filepath) as img:
                img.transpose(transpose_method).save(filepath, format=img.format)
            progress_window.message_queue.put(('success', filename, ""))
        except Exception as e:
            progress_window.message_queue.put(('error', filename, str(e)))
    
    # 处理完成后显示统计
    progress_window.after(0, progress_window.show_summary)

def main():
    """主函数流程控制"""
    root = tk.Tk()
    root.withdraw()
    
    # 选择目录
    dir_path = select_directory()
    if not dir_path:
        return
    
    # 选择操作
    operation = select_operation(root)
    if not operation:
        return
    
    # 统计图片数量
    supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    total_files = sum(1 for f in os.listdir(dir_path) if f.lower().endswith(supported_exts))
    
    if total_files == 0:
        messagebox.showwarning("警告", "所选目录中没有支持的图片文件！")
        return
    
    # 创建进度窗口
    progress_window = ProcessingWindow(root, total_files)
    
    # 在工作线程中处理图片
    processing_thread = threading.Thread(
        target=process_images,
        args=(dir_path, operation, progress_window),
        daemon=True
    )
    processing_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()