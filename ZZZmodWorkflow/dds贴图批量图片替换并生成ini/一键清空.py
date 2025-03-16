import os
import shutil
import json
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

CONFIG_FILE = "clear_config.json"

class FolderManager:
    def __init__(self, tree_widget=None):
        self.tree = tree_widget
        self.folders = self.load_config()
        self.refresh_tree()
    
    def load_config(self):
        """加载保存的配置"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            messagebox.showerror("配置错误", f"加载配置失败: {str(e)}")
        return []
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.folders, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("配置错误", f"保存配置失败: {str(e)}")
            return False
    
    def add_folder(self):
        """添加单个文件夹"""
        folder = filedialog.askdirectory(
            title="选择要添加的文件夹",
            mustexist=True
        )
        if folder:
            folder = os.path.normpath(folder)
            if folder not in self.folders:
                self.folders.append(folder)
                if self.save_config():
                    self.refresh_tree()
                    messagebox.showinfo("成功", f"已添加文件夹：\n{folder}")

    def remove_folders(self):
        """批量移除选中项（支持多选）"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要移除的文件夹")
            return
        
        # 获取所有选中路径
        removed_paths = [
            self.tree.item(item, "values")[0]
            for item in selected_items
        ]
        
        # 更新数据源
        self.folders = [p for p in self.folders if p not in removed_paths]
        
        if self.save_config():
            self.refresh_tree()
            messagebox.showinfo("完成", f"已移除 {len(removed_paths)} 个文件夹")

    def refresh_tree(self):
        """刷新Treeview显示"""
        self.tree.delete(*self.tree.get_children())
        for path in self.folders:
            self.tree.insert("", 'end', values=(path,))

def create_gui():
    """创建管理界面"""
    root = tk.Tk()
    root.title("文件夹管理工具")
    root.geometry("600x400")
    
    # 列表框架
    list_frame = ttk.Frame(root)
    list_frame.pack(pady=10, fill='both', expand=True)
    
    # 文件夹列表（保持多选模式）
    tree = ttk.Treeview(
        list_frame, 
        columns=('path'), 
        show='headings',
        selectmode='extended'  # 保留多选模式
    )
    tree.heading('path', text='文件夹路径')
    tree.column('path', width=550)
    
    # 滚动条
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # 布局
    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    # 初始化管理器
    manager = FolderManager(tree)
    
    # 按钮框架
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)
    
    # 功能按钮
    ttk.Button(btn_frame, text="添加文件夹", 
              command=manager.add_folder).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="移除选中", 
              command=manager.remove_folders).pack(side='left', padx=5)
    
    # 操作按钮
    ttk.Button(root, text="清空所有文件夹", 
              command=lambda: clear_folders(manager.folders, root)).pack(pady=10)
    ttk.Button(root, text="退出", command=root.destroy).pack()
    
    return root

def clear_folders(folders, parent):
    """执行清空操作"""
    if not folders:
        messagebox.showwarning("警告", "没有选择任何文件夹")
        return
    
    confirm = messagebox.askyesno(
        "危险操作",
        "即将永久清空以下文件夹:\n\n" + 
        "\n".join(folders) + 
        "\n\n请确认已做好备份！\n确定要继续吗？",
        parent=parent
    )
    
    if confirm:
        success = []
        failed = []
        for folder in folders:
            try:
                for filename in os.listdir(folder):
                    path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(path) or os.path.islink(path):
                            os.remove(path)
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
                    except Exception as e:
                        failed.append(f"{path} - {str(e)}")
                success.append(folder)
            except Exception as e:
                failed.append(f"{folder} - {str(e)}")
        
        result = []
        if success:
            result.append("成功清空:")
            result.extend(success)
        if failed:
            result.append("\n失败列表:")
            result.extend(failed)
        
        messagebox.showinfo("操作结果", "\n".join(result))

if __name__ == "__main__":
    gui = create_gui()
    gui.mainloop()