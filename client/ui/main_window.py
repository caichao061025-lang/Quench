"""
主窗口 — 现代化浅色 UI
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.shell_manager import ShellManager, ShellConfig
from core.connector import Connector
from ui.file_manager import FileManagerPanel
from ui.terminal import TerminalPanel
from ui.database import DatabasePanel
from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT_L, SUCCESS, DANGER, TEXT, TEXT2, INPUT_BG, FONT


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('淬火 Quench')
        self.root.geometry('1280x780')
        self.root.minsize(1000, 580)
        self.root.configure(bg=BG)

        self.shell_manager = ShellManager()
        self.connector = None
        self.current_shell_index = -1

        self._build()
        self._refresh_shell_list()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build(self):
        # ── 菜单栏 ──
        menubar = tk.Menu(self.root, bg=CARD, fg=TEXT, activebackground=ACCENT_L,
                          activeforeground=TEXT, borderwidth=0, relief='flat',
                          font=(FONT, 10))
        self.root.config(menu=menubar, bg=BG)

        sm = tk.Menu(menubar, tearoff=0, bg=CARD, fg=TEXT, activebackground=ACCENT_L,
                     activeforeground=TEXT, font=(FONT, 10))
        sm.add_command(label='添加 Shell    Ctrl+N', command=self._add_shell_dialog)
        sm.add_command(label='编辑当前', command=self._edit_shell_dialog)
        sm.add_command(label='删除当前', command=self._delete_shell)
        sm.add_separator()
        sm.add_command(label='测试连接', command=self._test_connection)
        sm.add_separator()
        sm.add_command(label='退出    Ctrl+Q', command=self._on_close)
        menubar.add_cascade(label='Shell', menu=sm)

        hm = tk.Menu(menubar, tearoff=0, bg=CARD, fg=TEXT, activebackground=ACCENT_L,
                     activeforeground=TEXT, font=(FONT, 10))
        hm.add_command(label='关于', command=self._show_about)
        menubar.add_cascade(label='帮助', menu=hm)

        self.root.bind('<Control-n>', lambda e: self._add_shell_dialog())
        self.root.bind('<Control-q>', lambda e: self._on_close())

        # ── 主布局 ──
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_workspace()
        self._build_statusbar()

    # ═══════ 侧边栏 ═══════
    def _build_sidebar(self):
        bar = tk.Frame(self.paned, bg='#e8ecf0', width=230, highlightthickness=0)
        self.paned.add(bar, weight=0)

        # Logo
        hdr = tk.Frame(bar, bg='#e8ecf0', height=60)
        hdr.pack(fill=tk.X, padx=16, pady=(14, 4))
        hdr.pack_propagate(False)
        tk.Label(hdr, text='淬火', bg='#e8ecf0', fg=ACCENT,
                 font=(FONT, 18, 'bold')).pack(side=tk.LEFT)
        tk.Label(hdr, text='Quench', bg='#e8ecf0', fg=TEXT2,
                 font=(FONT, 9)).pack(side=tk.LEFT, padx=(4, 0), pady=(8, 0))

        # 分隔线
        tk.Frame(bar, bg=BORDER, height=1).pack(fill=tk.X, padx=12)

        # Shell 计数
        self.sidebar_count = tk.Label(bar, text='未配置 Shell', bg='#e8ecf0',
                                      fg=TEXT2, font=(FONT, 9), anchor='w')
        self.sidebar_count.pack(fill=tk.X, padx=16, pady=(14, 4))

        # 列表
        lf = tk.Frame(bar, bg='#e8ecf0')
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        self.shell_listbox = tk.Listbox(lf, bg=CARD, fg=TEXT,
                                        selectbackground=ACCENT_L,
                                        selectforeground=TEXT,
                                        activestyle='none',
                                        highlightthickness=0, borderwidth=0,
                                        font=(FONT, 11), relief='flat')
        self.shell_listbox.pack(fill=tk.BOTH, expand=True)
        self.shell_listbox.bind('<<ListboxSelect>>', self._on_shell_select)

        # 按钮
        bf = tk.Frame(bar, bg='#e8ecf0')
        bf.pack(fill=tk.X, padx=12, pady=12)
        ttk.Button(bf, text='添加', command=self._add_shell_dialog,
                   style='Primary.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(bf, text='删除', command=self._delete_shell).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text='测试连接', command=self._test_connection).pack(fill=tk.X, pady=2)

    # ═══════ 工作区 ═══════
    def _build_workspace(self):
        ws = ttk.Frame(self.paned)
        self.paned.add(ws, weight=1)

        self.notebook = ttk.Notebook(ws)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=2)

        self.file_panel = FileManagerPanel(self.notebook, self)
        self.terminal_panel = TerminalPanel(self.notebook, self)
        self.database_panel = DatabasePanel(self.notebook, self)

        self.notebook.add(self.file_panel.frame, text='  文件管理  ')
        self.notebook.add(self.terminal_panel.frame, text='  终端  ')
        self.notebook.add(self.database_panel.frame, text='  数据库  ')

        self._tab_map = {1: self.terminal_panel}
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

    def _on_tab_changed(self, event):
        idx = self.notebook.index('current')
        p = self._tab_map.get(idx)
        if p and hasattr(p, 'focus_input'):
            self.root.after(100, p.focus_input)

    # ═══════ 状态栏 ═══════
    def _build_statusbar(self):
        sf = tk.Frame(self.root, bg=CARD, height=32)
        sf.pack(fill=tk.X, side=tk.BOTTOM)
        sf.pack_propagate(False)

        tk.Frame(sf, bg=BORDER, height=1).pack(fill=tk.X)

        self.status_dot = tk.Canvas(sf, width=8, height=8, bg=CARD, highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(12, 0), pady=4)
        self._set_status_dot('off')

        self.status_label = tk.Label(sf, text='就绪 — 请添加 Shell', bg=CARD, fg=TEXT2,
                                     font=(FONT, 9), anchor='w')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 8))

        self.time_label = tk.Label(sf, text='', bg=CARD, fg=TEXT2, font=(FONT, 9))
        self.time_label.pack(side=tk.RIGHT, padx=12)

    def _set_status_dot(self, state):
        self.status_dot.delete('all')
        c = SUCCESS if state == 'on' else (WARN if state == 'busy' else TEXT2)
        self.status_dot.create_oval(1, 1, 7, 7, fill=c, outline='')

    # ═══════ Shell 列表 ═══════
    def _refresh_shell_list(self):
        self.shell_listbox.delete(0, tk.END)
        for i, s in enumerate(self.shell_manager.get_all()):
            m = '  ●  ' if i == self.current_shell_index else '     '
            self.shell_listbox.insert(tk.END, m + s.name)
        n = self.shell_manager.count()
        self.sidebar_count.config(text=f'{n} 个 Shell' if n else '未配置 Shell')

    def _on_shell_select(self, event):
        sel = self.shell_listbox.curselection()
        if not sel: return
        idx = sel[0]
        if idx >= self.shell_manager.count(): return
        self.current_shell_index = idx
        s = self.shell_manager.get(idx)
        self.connector = Connector(s.url, s.password)
        self.status_label.config(text=f'已连接: {s.name}  ·  {s.url}')
        self._set_status_dot('on')
        self._refresh_shell_list()
        self._init_panels()

    # ═══════ Shell 对话框 ═══════
    def _add_shell_dialog(self):
        ShellEditDialog(self.root, '添加 Shell', callback=lambda c: self._on_dialog_done('add', c))

    def _edit_shell_dialog(self):
        if self.current_shell_index < 0:
            messagebox.showinfo('提示', '请先选择一个 Shell', parent=self.root); return
        s = self.shell_manager.get(self.current_shell_index)
        ShellEditDialog(self.root, '编辑 Shell', config=s, callback=lambda c: self._on_dialog_done('edit', c))

    def _on_dialog_done(self, mode, cfg):
        if cfg is None: return
        if mode == 'add':
            self.shell_manager.add(cfg)
            self._refresh_shell_list()
            idx = self.shell_manager.count() - 1
            self.shell_listbox.selection_clear(0, tk.END)
            self.shell_listbox.selection_set(idx)
            self.shell_listbox.see(idx)
            self._on_shell_select(None)
        else:
            self.shell_manager.update(self.current_shell_index, cfg)
            self.connector = Connector(cfg.url, cfg.password)
            self._refresh_shell_list()
            self._init_panels()

    def _delete_shell(self):
        if self.current_shell_index < 0:
            messagebox.showinfo('提示', '请先选择一个 Shell', parent=self.root); return
        s = self.shell_manager.get(self.current_shell_index)
        ok = messagebox.askyesno('确认删除', f'删除 "{s.name}"？', parent=self.root)
        if not ok: return
        self.shell_manager.remove(self.current_shell_index)
        self.current_shell_index = -1
        self.connector = None
        self._refresh_shell_list()
        self._clear_all_panels()
        self.status_label.config(text='就绪 — 请添加 Shell')
        self._set_status_dot('off')

    def _test_connection(self):
        if not self.connector:
            messagebox.showinfo('提示', '请先选择一个 Shell', parent=self.root); return
        self._set_status_dot('busy')
        self.status_label.config(text='正在测试连接...')
        threading.Thread(target=self._do_ping, daemon=True).start()

    def _do_ping(self):
        r = self.connector.ping()
        self.root.after(0, lambda: self._on_ping(r))

    def _on_ping(self, r):
        if 'pong' in r:
            messagebox.showinfo('连接成功', 'Webshell 响应正常\n服务器时间: ' + r.get('time', ''), parent=self.root)
            self._set_status_dot('on')
        else:
            messagebox.showerror('连接失败', r.get('error', '未知错误'), parent=self.root)
            self._set_status_dot('off')

    # ═══════ 面板管理 ═══════
    def _init_panels(self):
        if not self.connector: return
        self.terminal_panel.clear()
        info = self.connector.get_info()
        cwd = info.get('cwd', '.') if 'error' not in info else '.'
        self.file_panel.current_path = cwd
        self.file_panel.path_var.set(cwd)
        self.file_panel.refresh(cwd)

    def _clear_all_panels(self):
        self.file_panel.clear()
        self.terminal_panel.clear()
        self.database_panel.clear()

    def set_status(self, text):
        self.status_label.config(text=text)

    def _show_about(self):
        messagebox.showinfo('关于', '淬火 Quench\nWebshell 管理工具\n\n仅用于授权安全测试', parent=self.root)

    def _on_close(self):
        if messagebox.askokcancel('退出', '确定退出？', parent=self.root):
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ═══════ Shell 编辑对话框 ═══════
class ShellEditDialog(tk.Toplevel):
    def __init__(self, parent, title='添加 Shell', config=None, callback=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.cb = callback
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)
        self.geometry('460x320')

        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry('+%d+%d' % (px + (pw-460)//2, py + (ph-320)//2))

        self._build(config)
        self.lift()
        self.focus_force()
        self.grab_set()
        self.wait_window()

    def _build(self, cfg):
        f = tk.Frame(self, bg=CARD, padx=24, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        title_text = '添加 Shell' if cfg is None else '编辑 Shell'
        tk.Label(f, text=title_text, bg=CARD, fg=TEXT,
                 font=(FONT, 14, 'bold')).pack(anchor='w', pady=(0, 16))

        for label, var_name, default, show in [
            ('名称', 'name', '靶机-1', None),
            ('URL', 'url', 'http://', None),
            ('密码', 'password', 'test', '●'),
            ('备注', 'note', '', None),
        ]:
            tk.Label(f, text=label, bg=CARD, fg=TEXT2,
                     font=(FONT, 9)).pack(anchor='w', pady=(6, 2))

            fr = tk.Frame(f, bg=INPUT_BG, highlightbackground=BORDER,
                          highlightthickness=1)
            fr.pack(fill=tk.X)

            val = cfg.__getattribute__(var_name) if cfg else default
            v = tk.StringVar(value=val)
            e = tk.Entry(fr, textvariable=v, font=(FONT, 10),
                         bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                         relief='flat', borderwidth=0,
                         show='●' if (show and var_name == 'password') else '')
            e.pack(fill=tk.X, expand=True, ipady=6, padx=8)

            setattr(self, '_%s' % var_name, v)
            if show and var_name == 'password':
                setattr(self, '_pw_entry', e)

        # 显示密码
        self._show_pw = tk.BooleanVar(value=False)
        pw_row = [w for w in f.winfo_children()
                  if isinstance(w, tk.Label) and w.cget('text') == '密码'][0]
        # 用简单的方式: 直接在密码框frame后放checkbox
        # skip the complexity, just toggle

        # 按钮
        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill=tk.X, pady=(18, 0))
        ttk.Button(bf, text='取消', command=self._cancel).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(bf, text='保存', command=self._ok, style='Primary.TButton').pack(side=tk.RIGHT)

    def _ok(self):
        n = self._name.get().strip()
        u = self._url.get().strip()
        p = self._password.get().strip()
        nt = self._note.get().strip()
        if not n or not u or not p:
            messagebox.showwarning('提示', '名称、URL、密码不能为空', parent=self)
            return
        self.result = ShellConfig(name=n, url=u, password=p, note=nt)
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.destroy()
