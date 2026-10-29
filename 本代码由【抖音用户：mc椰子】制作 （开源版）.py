# ==============================================
# 程序名称：多线程高速下载程序
# 版权所有：mc椰子
# 禁止二次分发、篡改后冒充原版
# 【设备运行支持】：本程序仅支持 Windows 11 25H2、Windows 11 26H2
# ==============================================
import customtkinter as ctk
import requests
import os
import sys
import threading
import time
from tkinter import messagebox, filedialog
import ctypes
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 系统版本校验：仅允许 Win11 25H2(26200) / 26H2(26300)
def check_os_support():
    build_num = sys.getwindowsversion().build
    allow_build = {26200, 26300}
    if build_num not in allow_build:
        messagebox.showerror("系统不兼容", "本程序仅能运行在 Windows 11 25H2、Windows 11 26H2！")
        sys.exit(0)

check_os_support()

# ===================== 基础配置 =====================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# 任务栏标识【原版不动】
myappid = "v2.99.7.5"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# 下载镜像版本列表（修复逗号语法错误）
VERSION_URL = {
    "抖音": "https://www.douyin.com/download/pc/obj/douyin-pc-web/douyin-pc-client/7044145585217083655/releases/495279540/8.7.0/win32-ia32/douyin-downloader-v8.7.0-win32-ia32-douyincold.exe",
    "QQ": "https://qqdl.gtimg.cn/qqfile/QQNTV2/9.9.36/release/e8e54bbb/QQ_9.9.36_260924_x64_01.exe?sign=a073876b586518050eae15eadfb28789&t=1793276308",
    "汽水音乐": "https://lf-luna-release.qishui.com/obj/luna-release/3.7.0/452316191/SodaMusic-v3.7.0-official-win32_x64.exe",
    "Steam": "https://media.cdn.queniuqe.com/client/installer/SteamSetup.exe"
}

class GlassInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("软件下载工具 | © mc椰子")
        self.geometry("640x540")
        self.resizable(False, False)
        self.attributes("-alpha", 0.92)

        self.select_ver = ctk.StringVar(value="抖音")
        self.install_path = ctk.StringVar(value="")
        self.agreement_check = ctk.BooleanVar(value=False)
        self.page_index = 0
        self.stop_download = False

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # 底部版权标签
        self.copyright_label = ctk.CTkLabel(self, text="v2.99.7.3.6\n© mc椰子 版权所有 | 仅支持 Windows 11 25H2 / 26H2", text_color="#777777", font=("Microsoft YaHei", 10))
        self.copyright_label.pack(side="bottom", pady=4)

        self.page1 = self.create_agreement_page()
        self.page2 = self.create_select_page()
        self.page3 = self.create_download_page()
        self.page4 = self.create_finish_page()

        self.show_page(0)

    def show_page(self, idx):
        self.page_index = idx
        for widget in self.container.winfo_children():
            widget.pack_forget()
        if idx == 0:
            self.page1.pack(fill="both", expand=True)
        elif idx == 1:
            self.page2.pack(fill="both", expand=True)
        elif idx == 2:
            self.page3.pack(fill="both", expand=True)
        elif idx == 3:
            self.page4.pack(fill="both", expand=True)

    def get_filename(self, url):
        cd = re.search(r'filename=([^&]+)', url)
        if cd:
            return cd.group(1)
        fname = url.split("?")[0].split("/")[-1]
        if not fname or "." not in fname:
            fname = "download.exe"
        return fname

    # 协议页
    def create_agreement_page(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="许可协议", font=("Microsoft YaHei", 18, "bold"))
        title.pack(pady=(20, 10))
        textbox = ctk.CTkTextbox(frame, height=260, wrap="word")
        textbox.pack(fill="both", expand=True, padx=20, pady=10)
        textbox.insert("end",
"欢迎使用本下载工具。本工具仅用于下载您已授权获取的软件安装包。\n"
"1. 本程序仅支持在 Windows 11 25H2、Windows 11 26H2 上运行。\n"
"2. 版权所有 © mc椰子，禁止二次分发、篡改后冒充原版。\n"
"3. 请确保您下载的文件来源合法，并拥有相应使用授权。\n"
"4. 下载过程中请勿关闭程序，避免文件损坏。\n"
"5. 程序会将文件保存到您指定的目录中。\n"
"6. 如遇链接失效，请更换有效下载地址后重新下载。\n"
"继续使用即表示您已阅读并同意上述条款。")
        textbox.configure(state="disabled")
        check = ctk.CTkCheckBox(frame, text="我已阅读并同意许可协议", variable=self.agreement_check)
        check.pack(pady=10)
        btn_next = ctk.CTkButton(frame, text="下一步", command=self.go_agree_next)
        btn_next.pack(pady=(10, 20))
        return frame

    def go_agree_next(self):
        if not self.agreement_check.get():
            messagebox.showwarning("提示", "请先同意许可协议。")
            return
        self.show_page(1)

    # 版本选择页
    def create_select_page(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="选择软件与保存路径", font=("Microsoft YaHei", 18, "bold"))
        title.pack(pady=(20, 10))
        ctk.CTkLabel(frame, text="请选择软件：").pack(anchor="w", padx=30, pady=(10, 5))
        menu = ctk.CTkOptionMenu(frame, values=list(VERSION_URL.keys()), variable=self.select_ver)
        menu.pack(fill="x", padx=30, pady=5)
        ctk.CTkLabel(frame, text="保存路径：").pack(anchor="w", padx=30, pady=(15, 5))
        entry = ctk.CTkEntry(frame, textvariable=self.install_path)
        entry.pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(frame, text="浏览...", width=120, command=self.browse_folder).pack(anchor="w", padx=30, pady=5)
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(btn_frame, text="上一步", width=120, command=lambda: self.show_page(0)).pack(side="left")
        ctk.CTkButton(btn_frame, text="下一步", command=self.go_select_next).pack(side="right")
        return frame

    def browse_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.install_path.set(p)

    def go_select_next(self):
        ver = self.select_ver.get()
        savep = self.install_path.get().strip()
        if not VERSION_URL[ver]:
            messagebox.showwarning("提示", "该软件还没有配置下载链接！")
            return
        if not savep:
            messagebox.showwarning("提示", "请先选择保存文件夹！")
            return
        self.show_page(2)

    # 下载页面
    def create_download_page(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="正在下载", font=("Microsoft YaHei", 18, "bold"))
        title.pack(pady=(20, 10))
        self.info_text = ctk.CTkLabel(frame, text="等待开始下载...")
        self.info_text.pack(fill="x", padx=30, pady=10)
        self.progress = ctk.CTkProgressBar(frame)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=30, pady=10)
        self.start_btn = ctk.CTkButton(frame, text="开始下载", command=self.start_dl_thread)
        self.start_btn.pack(pady=(20, 10))
        self.cancel_btn = ctk.CTkButton(frame, text="取消下载", fg_color="#d9534f", command=self.cancel_dl)
        self.cancel_btn.pack(pady=10)
        return frame

    # 完成页面
    def create_finish_page(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="下载完成", font=("Microsoft YaHei", 18, "bold"))
        title.pack(pady=(40, 20))
        ctk.CTkLabel(frame, text="文件已经保存到你选择的目录").pack(pady=10)
        ctk.CTkButton(frame, text="打开保存目录", command=self.open_dir).pack(pady=(30,10))
        ctk.CTkButton(frame, text="完成", command=self.destroy).pack(pady=10)
        return frame

    def open_dir(self):
        p = self.install_path.get().strip()
        if os.path.exists(p):
            os.startfile(p)
        else:
            messagebox.showwarning("提示", "路径不存在！")

    def start_dl_thread(self):
        self.stop_download = False
        self.start_btn.configure(state="disabled")
        t = threading.Thread(target=self.download_main, daemon=True)
        t.start()

    def cancel_dl(self):
        self.stop_download = True
        self.info_text.configure(text="正在取消下载...")

    def download_main(self):
        ver = self.select_ver.get()
        url = VERSION_URL[ver]
        save_dir = self.install_path.get().strip()
        filename = self.get_filename(url)
        fullpath = os.path.join(save_dir, filename)
        retry_max = 2
        retry_count = 0
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        while retry_count <= retry_max:
            try:
                self.after(0, lambda:self.info_text.configure(text=f"正在下载：{ver}，尝试 {retry_count+1}/{retry_max+1}"))
                resp = requests.get(url, stream=True, headers=headers, timeout=25, verify=False)
                resp.raise_for_status()
                total_len = int(resp.headers.get("Content-Length",0))
                downloaded = 0
                start_time = time.time()
                with open(fullpath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if self.stop_download:
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_len > 0:
                                percent = downloaded / total_len
                                speed = downloaded / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                                speed_mb = speed / 1024 / 1024
                                dl_mb = downloaded / 1024 / 1024
                                total_mb = total_len / 1024 / 1024
                                info_str = f"{percent*100:.1f}% | {dl_mb:.1f}MB / {total_mb:.1f}MB | 速度：{speed_mb:.2f} MB/s"
                                self.after(0, lambda v=percent, txt=info_str: (self.progress.set(v), self.info_text.configure(text=txt)))
                            else:
                                dl_mb = downloaded / 1024 / 1024
                                info_str = f"未知总大小 | 已下载：{dl_mb:.1f}MB | 速度：{speed_mb:.2f} MB/s"
                                self.after(0, lambda txt=info_str: self.info_text.configure(text=txt))
                if self.stop_download:
                    os.remove(fullpath)
                    self.after(0,lambda:messagebox.showinfo("提示","下载已取消，临时文件已清理"))
                    break
                self.after(0, lambda:self.show_page(3))
                return
            except requests.exceptions.RequestException:
                retry_count +=1
                if retry_count <= retry_max:
                    self.after(0,lambda:self.info_text.configure(text=f"网络异常，准备重试 {retry_count}/{retry_max}"))
                else:
                    self.after(0,lambda:messagebox.showerror("下载失败","多次连接失败，链接或者网络有问题"))
            except Exception as e:
                self.after(0,lambda:messagebox.showerror("错误",f"{str(e)}"))
                break
        self.after(0,lambda:self.start_btn.configure(state="normal"))

if __name__ == "__main__":
    app = GlassInstaller()
    app.mainloop()
