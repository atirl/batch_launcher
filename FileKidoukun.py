#============================================================
# ファイル起動くん
# 2026/09/17 作成 atirl
# 2026/09/30 ショートカットを起動できるように修正
# 2026/10/15 複数フォルダ対応・あとpy追加
#============================================================

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime

#============================================================
# 基本設定
#============================================================

APP_NAME = "ファイル起動くん"
TARGET_FOLDER_NAME = "実行対象"
LOG_FILE_NAME = "kidoukun_log.txt"
TARGET_PATH_FILE_NAME = "target_folder.txt"

ALLOWED_EXTENSIONS = {".bat", ".exe", ".vbs", ".lnk", ".py"}

MAX_FILES = 75
MAX_FOLDERS = 10
COLUMN_LIMIT = 15

#============================================================
# アプリケーションの場所
#============================================================

def get_app_directory():
    #exe化対応
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_DIRECTORY = get_app_directory()

DEFAULT_TARGET_DIRECTORY = os.path.join(
    APP_DIRECTORY, TARGET_FOLDER_NAME
)

LOG_FILE_PATH = os.path.join(
    APP_DIRECTORY, LOG_FILE_NAME
)

TARGET_PATH_FILE = os.path.join(
    APP_DIRECTORY, TARGET_PATH_FILE_NAME
)

# 登録対象フォルダ一覧
TARGET_DIRECTORIES = [DEFAULT_TARGET_DIRECTORY]


#============================================================
# 関数
#============================================================
"""ログ書き込み"""
def write_log(message):

    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{now}  {message}\n")
    except Exception:
        pass


#============================================================
# 対象フォルダ設定の保存
#============================================================
"""登録した対象フォルダを1行につき1パスで保存"""
def save_target_directories():
    
    try:
        with open(TARGET_PATH_FILE, "w", encoding="utf-8") as f:
            for path in TARGET_DIRECTORIES:
                f.write(path + "\n")

    except Exception as e:
        write_log(
            f"対象フォルダ設定の保存に失敗しました。エラー: {e}"
        )
        messagebox.showerror(
            APP_NAME,
            f"対象フォルダ設定を保存できませんでした。\n\n{e}"
        )


#============================================================
# 対象フォルダ設定の読み込み
#============================================================
"""
対象フォルダ設定を読み込む。

新形式：1行につき1フォルダ
旧形式：従来どおり1行だけのパスも読み込み可能
設定ファイルがない場合：./実行対象を使用する
"""
def load_target_directories():

    global TARGET_DIRECTORIES

    if not os.path.exists(TARGET_PATH_FILE):
        TARGET_DIRECTORIES = [DEFAULT_TARGET_DIRECTORY]
        return

    try:
        with open(TARGET_PATH_FILE, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip()]

        normalized_paths = []

        for path in paths:
            if not os.path.isabs(path):
                path = os.path.join(APP_DIRECTORY, path)

            path = os.path.abspath(path)

            # 重複登録を防止（Windowsのパスを想定）
            if not any(
                os.path.normcase(p) == os.path.normcase(path)
                for p in normalized_paths
            ):
                normalized_paths.append(path)

            if len(normalized_paths) >= MAX_FOLDERS:
                break

        TARGET_DIRECTORIES = (
            normalized_paths
            if normalized_paths
            else [DEFAULT_TARGET_DIRECTORY]
        )

    except Exception as e:
        write_log(
            f"対象フォルダ設定の読み込みに失敗しました。エラー: {e}"
        )
        TARGET_DIRECTORIES = [DEFAULT_TARGET_DIRECTORY]


#============================================================
# 対象ファイル取得
#============================================================
"""
登録した全フォルダの直下から対象ファイルを取得(サブフォルダは取得しない、混乱の元なので…)
取得した全フォルダから、ファイル名順にソート。
戻り値：
    [(フォルダパス, ファイル名), ...]
"""
def get_target_files():

    files = []

    for directory in TARGET_DIRECTORIES:

        if not os.path.isdir(directory):
            write_log(
                f"対象フォルダが存在しないためスキップしました: "
                f"{directory}"
            )
            continue

        try:
            for name in os.listdir(directory):
                full_path = os.path.join(directory, name)

                if not os.path.isfile(full_path):
                    continue

                extension = os.path.splitext(name)[1].lower()

                if extension in ALLOWED_EXTENSIONS:
                    files.append((directory, name))

        except Exception as e:
            messagebox.showerror(
                APP_NAME,
                "対象フォルダの読み込みに失敗しました。\n\n"
                f"フォルダ:\n{directory}\n\n{e}"
            )
            write_log(
                f"対象フォルダの読み込みに失敗しました: "
                f"{directory} / {e}"
            )
            return None

    # ファイル名順。同名の場合はフォルダパス順。
    files.sort(
        key=lambda item: (
            item[1].lower(),
            item[0].lower()
        )
    )

    return files


#============================================================
# ファイル実行
#============================================================
"""
指定フォルダ内のファイルを実行する
現在の対象はbat,vbs,exe,lnk,py
"""
def execute_file(directory, file_name):

    full_path = os.path.join(directory, file_name)
    extension = os.path.splitext(file_name)[1].lower()

    try:
        if extension == ".bat":
            subprocess.Popen(
                ["cmd.exe", "/c", full_path],
                cwd=directory
            )

        elif extension == ".vbs":
            subprocess.Popen(
                ["wscript.exe", full_path],
                cwd=directory
            )

        elif extension == ".exe":
            subprocess.Popen(
                [full_path],
                cwd=directory
            )

        elif extension == ".lnk":
            os.startfile(full_path)

        elif extension == ".py":
            subprocess.Popen(
                ["python", full_path],
                cwd=directory
            )

        write_log(
            f"「{file_name}」を実行しました。"
            f" 対象フォルダ: {directory}"
        )

    except Exception as e:
        write_log(
            f"「{file_name}」の実行に失敗しました。エラー: {e}"
        )

        messagebox.showerror(
            APP_NAME,
            f"「{file_name}」の実行に失敗しました。\n\n{e}"
        )


#============================================================
# メニューボタン押下
#============================================================

def menu_button_clicked(directory, file_name):
    write_log(
        f"「{file_name}」ボタンを押下しました。"
        f" 対象フォルダ: {directory}"
    )

    result = messagebox.askyesno(
        APP_NAME,
        f"「{file_name}」を起動しますか？\n\n"
        f"フォルダ:\n{directory}"
    )

    if result:
        write_log("「はい」ボタンを押下しました。実行します。")
        execute_file(directory, file_name)
    else:
        write_log("「いいえ」ボタンを押下しました。キャンセルします。")


#============================================================
# ログをメモ帳で開く
#============================================================

def open_log():
    write_log("「実行ログ」ボタンを押下しました")

    try:
        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, "w", encoding="utf-8"):
                pass

        subprocess.Popen(["notepad.exe", LOG_FILE_PATH])

    except Exception as e:
        messagebox.showerror(
            APP_NAME,
            f"ログファイルを開けませんでした。\n\n{e}"
        )


#============================================================
# 対象フォルダ指定画面
#============================================================
"""
ファイル取得対象のフォルダ指定ウインドウ
10個まで登録可
"""
def select_target_folder():
    write_log("「対象フォルダ指定」ボタンを押下しました")

    setting_window = tk.Toplevel(root)
    setting_window.title("対象フォルダ指定")
    setting_window.resizable(False, False)
    setting_window.transient(root)
    setting_window.grab_set()

    tk.Label(
        setting_window,
        text=f"対象フォルダを指定してください（最大{MAX_FOLDERS}個）。",
        font=("Meiryo", 10)
    ).pack(padx=20, pady=(15, 5))

    tk.Label(
        setting_window,
        text="登録したフォルダのファイルをまとめて表示します。",
        font=("Meiryo", 9)
    ).pack(padx=20, pady=(0, 10))

    # 登録済みフォルダ一覧
    list_frame = tk.Frame(setting_window)
    list_frame.pack(padx=20, pady=5)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    folder_listbox = tk.Listbox(
        list_frame,
        width=75,
        height=8,
        font=("Meiryo", 9),
        selectmode=tk.SINGLE,
        yscrollcommand=scrollbar.set
    )
    folder_listbox.pack(side="left")
    scrollbar.config(command=folder_listbox.yview)

    count_var = tk.StringVar()
    count_label = tk.Label(
        setting_window,
        textvariable=count_var,
        font=("Meiryo", 9)
    )
    count_label.pack(pady=(3, 5))

    # 設定画面内で編集する一時リスト
    edit_directories = list(TARGET_DIRECTORIES)

    def refresh_folder_list():
        folder_listbox.delete(0, tk.END)

        for path in edit_directories:
            folder_listbox.insert(tk.END, path)

        count_var.set(
            f"登録数：{len(edit_directories)} / {MAX_FOLDERS}"
        )

    refresh_folder_list()

    # フォルダ追加
    def add_folder():
        if len(edit_directories) >= MAX_FOLDERS:
            messagebox.showwarning(
                APP_NAME,
                f"登録できるフォルダは最大{MAX_FOLDERS}個です。",
                parent=setting_window
            )
            return

        initial_dir = next(
            (
                p for p in reversed(edit_directories)
                if os.path.isdir(p)
            ),
            APP_DIRECTORY
        )

        selected = filedialog.askdirectory(
            title="追加するフォルダを選択してください",
            initialdir=initial_dir,
            parent=setting_window
        )

        if not selected:
            return

        selected = os.path.abspath(selected)

        if any(
            os.path.normcase(p) == os.path.normcase(selected)
            for p in edit_directories
        ):
            messagebox.showwarning(
                APP_NAME,
                "このフォルダはすでに登録されています。",
                parent=setting_window
            )
            return

        edit_directories.append(selected)
        refresh_folder_list()

        folder_listbox.selection_clear(0, tk.END)
        folder_listbox.selection_set(tk.END)
        folder_listbox.see(tk.END)

    # フォルダ削除
    def remove_folder():
        selection = folder_listbox.curselection()

        if not selection:
            messagebox.showwarning(
                APP_NAME,
                "削除するフォルダを選択してください。",
                parent=setting_window
            )
            return

        index = selection[0]
        removed = edit_directories.pop(index)

        write_log(f"対象フォルダの削除を指定しました: {removed}")

        refresh_folder_list()

        if edit_directories:
            new_index = min(index, len(edit_directories) - 1)
            folder_listbox.selection_set(new_index)

    edit_button_frame = tk.Frame(setting_window)
    edit_button_frame.pack(pady=5)

    tk.Button(
        edit_button_frame,
        text="フォルダ追加",
        width=14,
        command=add_folder
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        edit_button_frame,
        text="選択フォルダ削除",
        width=16,
        command=remove_folder
    ).grid(row=0, column=1, padx=5)

    # 設定確定orキャンセルボタン
    button_frame = tk.Frame(setting_window)
    button_frame.pack(pady=(10, 15))

    def apply_folders():
        global TARGET_DIRECTORIES

        if not edit_directories:
            messagebox.showwarning(
                APP_NAME,
                "対象フォルダを1個以上登録してください。",
                parent=setting_window
            )
            return

        # 存在しないフォルダが含まれる場合は確認
        missing = [
            p for p in edit_directories
            if not os.path.isdir(p)
        ]

        if missing:
            result = messagebox.askyesno(
                APP_NAME,
                "存在しないフォルダが含まれています。\n\n"
                + "\n".join(missing)
                + "\n\nこのまま設定を保存しますか？",
                parent=setting_window
            )

            if not result:
                return

        TARGET_DIRECTORIES = list(edit_directories)

        save_target_directories()

        write_log(
            f"対象フォルダを設定しました。登録数: "
            f"{len(TARGET_DIRECTORIES)}"
        )

        setting_window.destroy()
        reload_menu()

    tk.Button(
        button_frame,
        text="設定",
        width=12,
        height=2,
        command=apply_folders
    ).grid(row=0, column=0, padx=10)

    tk.Button(
        button_frame,
        text="キャンセル",
        width=12,
        height=2,
        command=setting_window.destroy
    ).grid(row=0, column=1, padx=10)

    setting_window.bind("<Escape>", lambda event: setting_window.destroy())


#============================================================
# 再読込
#============================================================

def reload_menu():
    write_log("「再読込」ボタンを押下しました")

    files = get_target_files()

    if files is None:
        messagebox.showerror(
            APP_NAME,
            "対象フォルダの読み込みに失敗したため、再読込できません。"
        )
        return

    total_count = len(files)

    # MAXFILESを超えた場合は警告
    if total_count > MAX_FILES:
        overflow = total_count - MAX_FILES

        messagebox.showwarning(
            APP_NAME,
            f"最大の{MAX_FILES}個を超えています！\n\n"
            f"対象ファイル数：{total_count}個\n"
            f"表示上限：{MAX_FILES}個\n\n"
            f"超過分{overflow}ファイルは表示されません！"
        )

        write_log(
            f"対象ファイルが上限を超えています！"
            f" 全{total_count}個、表示上限{MAX_FILES}個、"
            f"超過{overflow}個"
        )

    display_files = files[:MAX_FILES]

    create_menu(display_files)

    write_log(
        f"対象フォルダを再読込しました。"
        f" 取得数: {total_count}、表示数: {len(display_files)}"
    )


#============================================================
# メイン画面
#============================================================

def create_menu(files):
    # 既存ウィジェットを削除
    for widget in root.winfo_children():
        widget.destroy()

    # タイトル
    tk.Label(
        root,
        text=APP_NAME,
        font=("Meiryo", 16, "bold")
    ).pack(pady=(15, 5))

    # 対象フォルダ表示
    folder_text = (
        f"登録フォルダ数：{len(TARGET_DIRECTORIES)}個"
    )

    tk.Label(
        root,
        text=folder_text,
        font=("Meiryo", 9)
    ).pack(padx=15, pady=(0, 3))

    tk.Label(
        root,
        text=f"表示ファイル数：{len(files)} / {MAX_FILES}",
        font=("Meiryo", 9)
    ).pack(padx=15, pady=(0, 10))


    # メニューボタン
    # 15行 × 5列、最大75個
    menu_frame = tk.Frame(root)
    menu_frame.pack(padx=15, pady=5)

    if files:
        button_width = min(
            max(len(file_name) for _, file_name in files),
            42
        )
    else:
        button_width = 1

    # 同名ファイルが複数ある場合フォルダ名併記
    name_counts = {}

    for _, file_name in files:
        key = file_name.lower()
        name_counts[key] = name_counts.get(key, 0) + 1

    for index, (directory, file_name) in enumerate(files):
        column = index // COLUMN_LIMIT
        row = index % COLUMN_LIMIT

        if name_counts[file_name.lower()] > 1:
            display_name = (
                f"{file_name} [{os.path.basename(directory)}]"
            )
        else:
            display_name = file_name

        button = tk.Button(
            menu_frame,
            text=display_name,
            width=button_width,
            height=1,
            borderwidth=2,
            relief="solid",
            font=("Meiryo", 9),
            command=lambda d=directory, f=file_name:
                menu_button_clicked(d, f)
        )

        button.grid(
            row=row,
            column=column,
            padx=4,
            pady=3,
            sticky="ew"
        )

    # 下部ボタン
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(pady=(15, 15))

    tk.Button(
        bottom_frame,
        text="対象設定",
        width=9,
        height=2,
        font=("Meiryo", 10),
        command=select_target_folder
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        bottom_frame,
        text="再読込",
        width=9,
        height=2,
        font=("Meiryo", 10),
        command=reload_menu
    ).grid(row=0, column=1, padx=5)

    tk.Button(
        bottom_frame,
        text="実行ログ",
        width=9,
        height=2,
        font=("Meiryo", 10),
        command=open_log
    ).grid(row=0, column=2, padx=5)

    tk.Button(
        bottom_frame,
        text="終了",
        width=9,
        height=2,
        font=("Meiryo", 10),
        command=exit_application
    ).grid(row=0, column=3, padx=5)


#============================================================
# アプリ起動＋読み込み（読み込みも別途関数化するかも）
#============================================================

def initialize():
    write_log("アプリケーションを起動しました")

    load_target_directories()

    # すべての登録フォルダが存在しない場合は設定を促す
    if not any(
        os.path.isdir(p) for p in TARGET_DIRECTORIES
    ):
        result = messagebox.askyesno(
            APP_NAME,
            "登録された対象フォルダが見つかりません。\n\n"
            "対象フォルダを指定しますか？"
        )

        if result:
            create_menu([])
            root.after(100, select_target_folder)
            return

        write_log(
            "対象フォルダが見つからないため終了します"
        )
        root.destroy()
        return

    files = get_target_files()

    if files is None:
        write_log(
            "対象フォルダの読み込みに失敗したため終了します"
        )
        root.destroy()
        return

    total_count = len(files)

    if total_count > MAX_FILES:
        overflow = total_count - MAX_FILES

        messagebox.showwarning(
            APP_NAME,
            f"最大の{MAX_FILES}個を超えています。\n\n"
            f"対象ファイル数：{total_count}個\n"
            f"表示上限：{MAX_FILES}個\n\n"
            f"超過分{overflow}ファイルは表示されません。"
        )

        write_log(
            f"起動時に上限超過を検出。全{total_count}個、"
            f"表示上限{MAX_FILES}個、超過{overflow}個"
        )

    if total_count == 0:
        write_log("実行対象ファイルがありません")

    create_menu(files[:MAX_FILES])

#============================================================
# アプリ終了
#============================================================

def exit_application():
    write_log("「終了」ボタンを押下しました")
    write_log("アプリケーションを終了します")
    root.destroy()

#============================================================
# メイン
#============================================================

root = tk.Tk()
root.title(APP_NAME)
root.minsize(300, 300)
root.option_add("*Font", ("Meiryo", 10))
root.protocol("WM_DELETE_WINDOW", exit_application)

initialize()
root.mainloop()
