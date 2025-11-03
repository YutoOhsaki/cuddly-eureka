#!/usr/bin/env python3
"""
Windows Task Manager Tool
シンプルで使いやすいタスク管理アプリケーション
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime


class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("タスク管理ツール")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # タスクデータ
        self.tasks = []
        self.data_file = "tasks.json"

        # UIのセットアップ
        self.setup_ui()

        # 既存のタスクを読み込み
        self.load_tasks()

    def setup_ui(self):
        """UIコンポーネントをセットアップ"""
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')

        # ヘッダーフレーム
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="📋 タスク管理ツール",
            font=("メイリオ", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # 入力フレーム
        input_frame = tk.Frame(self.root, bg="#ecf0f1", height=80)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        input_frame.pack_propagate(False)

        # タスク入力欄
        self.task_entry = tk.Entry(
            input_frame,
            font=("メイリオ", 12),
            bg="white",
            relief=tk.FLAT,
            borderwidth=2
        )
        self.task_entry.pack(side=tk.LEFT, padx=10, pady=20, fill=tk.BOTH, expand=True)
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        self.task_entry.focus()

        # 追加ボタン
        add_button = tk.Button(
            input_frame,
            text="➕ タスクを追加",
            font=("メイリオ", 11, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_task,
            padx=20
        )
        add_button.pack(side=tk.LEFT, padx=10, pady=20)

        # タスクリストフレーム
        list_frame = tk.Frame(self.root, bg="#ecf0f1")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # スクロールバー
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # タスクリスト
        self.task_listbox = tk.Listbox(
            list_frame,
            font=("メイリオ", 11),
            bg="white",
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor="#3498db",
            highlightbackground="#bdc3c7",
            yscrollcommand=scrollbar.set,
            activestyle='none'
        )
        self.task_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.task_listbox.yview)

        # ボタンフレーム
        button_frame = tk.Frame(self.root, bg="#f0f0f0", height=70)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        button_frame.pack_propagate(False)

        # 完了ボタン
        complete_button = tk.Button(
            button_frame,
            text="✓ 完了/未完了",
            font=("メイリオ", 10, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_complete,
            width=15
        )
        complete_button.pack(side=tk.LEFT, padx=5, pady=15)

        # 削除ボタン
        delete_button = tk.Button(
            button_frame,
            text="🗑 削除",
            font=("メイリオ", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.delete_task,
            width=15
        )
        delete_button.pack(side=tk.LEFT, padx=5, pady=15)

        # 全削除ボタン
        clear_button = tk.Button(
            button_frame,
            text="🗑 全て削除",
            font=("メイリオ", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_all_tasks,
            width=15
        )
        clear_button.pack(side=tk.LEFT, padx=5, pady=15)

        # ステータスバー
        self.status_bar = tk.Label(
            self.root,
            text="タスク: 0件",
            font=("メイリオ", 9),
            bg="#34495e",
            fg="white",
            anchor=tk.W,
            padx=10
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def add_task(self):
        """新しいタスクを追加"""
        task_text = self.task_entry.get().strip()

        if not task_text:
            messagebox.showwarning("警告", "タスクを入力してください。")
            return

        task = {
            "text": task_text,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.tasks.append(task)
        self.update_task_list()
        self.task_entry.delete(0, tk.END)
        self.save_tasks()

    def toggle_complete(self):
        """選択されたタスクの完了状態を切り替え"""
        selection = self.task_listbox.curselection()

        if not selection:
            messagebox.showwarning("警告", "タスクを選択してください。")
            return

        index = selection[0]
        self.tasks[index]["completed"] = not self.tasks[index]["completed"]
        self.update_task_list()
        self.task_listbox.selection_set(index)
        self.save_tasks()

    def delete_task(self):
        """選択されたタスクを削除"""
        selection = self.task_listbox.curselection()

        if not selection:
            messagebox.showwarning("警告", "削除するタスクを選択してください。")
            return

        index = selection[0]
        task_text = self.tasks[index]["text"]

        if messagebox.askyesno("確認", f"「{task_text}」を削除しますか？"):
            del self.tasks[index]
            self.update_task_list()
            self.save_tasks()

    def clear_all_tasks(self):
        """全てのタスクを削除"""
        if not self.tasks:
            messagebox.showinfo("情報", "削除するタスクがありません。")
            return

        if messagebox.askyesno("確認", "全てのタスクを削除しますか？"):
            self.tasks.clear()
            self.update_task_list()
            self.save_tasks()

    def update_task_list(self):
        """タスクリストを更新"""
        self.task_listbox.delete(0, tk.END)

        for i, task in enumerate(self.tasks):
            status = "✓" if task["completed"] else "○"
            text = task["text"]

            if task["completed"]:
                display_text = f"{status} {text}"
                self.task_listbox.insert(tk.END, display_text)
                self.task_listbox.itemconfig(i, fg="#95a5a6")
            else:
                display_text = f"{status} {text}"
                self.task_listbox.insert(tk.END, display_text)
                self.task_listbox.itemconfig(i, fg="#2c3e50")

        # ステータスバーを更新
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task["completed"])
        self.status_bar.config(
            text=f"タスク: {total}件 (完了: {completed}件, 未完了: {total - completed}件)"
        )

    def save_tasks(self):
        """タスクをJSONファイルに保存"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("エラー", f"タスクの保存に失敗しました: {e}")

    def load_tasks(self):
        """JSONファイルからタスクを読み込み"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
                self.update_task_list()
            except Exception as e:
                messagebox.showerror("エラー", f"タスクの読み込みに失敗しました: {e}")
                self.tasks = []


def main():
    """メイン関数"""
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
