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
from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT_L, SUCCESS, WARN, DANGER, TEXT, TEXT2, INPUT_BG, FONT


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
        self._shell_alive = {}    # index -> bool, 跟踪每个 shell 是否存活

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
            # 状态标记：绿 ● 存活，红 ● 失效， 未检测
            if i == self.current_shell_index and i in self._shell_alive:
                m = '  ●  ' if self._shell_alive[i] else '  ✕  '
            elif i == self.current_shell_index:
                m = '  ◌  '   # 正在检测中
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
        self._refresh_shell_list()

        # 如果已知该 shell 已失效，直接显示错误，不再尝试连接
        if idx in self._shell_alive and not self._shell_alive[idx]:
            self._clear_all_panels()
            self.status_label.config(text=f'已失效: {s.name}  ·  {s.url}')
            self._set_status_dot('off')
            return

        self.status_label.config(text=f'连接中: {s.name}  ·  {s.url}')
        self._set_status_dot('busy')
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
        try:
            if mode == 'add':
                self.shell_manager.add(cfg)
                self._refresh_shell_list()
                idx = self.shell_manager.count() - 1
                self.shell_listbox.selection_clear(0, tk.END)
                self.shell_listbox.selection_set(idx)
                self.shell_listbox.see(idx)
                # selection_set 不触发 <<ListboxSelect>>，必须显式调用
                self._on_shell_select(None)
            else:
                self.shell_manager.update(self.current_shell_index, cfg)
                self._shell_alive.pop(self.current_shell_index, None)
                self.connector = Connector(cfg.url, cfg.password)
                self._refresh_shell_list()
                self._init_panels()
        except Exception as e:
            messagebox.showerror('错误', f'操作失败: {e}', parent=self.root)

    def _delete_shell(self):
        if self.current_shell_index < 0:
            messagebox.showinfo('提示', '请先选择一个 Shell', parent=self.root); return
        s = self.shell_manager.get(self.current_shell_index)
        ok = messagebox.askyesno('确认删除', f'删除 "{s.name}"？', parent=self.root)
        if not ok: return
        removed_idx = self.current_shell_index
        self.shell_manager.remove(removed_idx)
        # 重建 _shell_alive 索引
        new_alive = {}
        for idx, alive in self._shell_alive.items():
            if idx > removed_idx:
                new_alive[idx - 1] = alive
            elif idx < removed_idx:
                new_alive[idx] = alive
        self._shell_alive = new_alive
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
        idx = self.current_shell_index
        if 'pong' in r:
            self._shell_alive[idx] = True
            messagebox.showinfo('连接成功', 'Webshell 响应正常\n服务器时间: ' + r.get('time', ''), parent=self.root)
            self._set_status_dot('on')
        else:
            self._shell_alive[idx] = False
            messagebox.showerror('连接失败', r.get('error', '未知错误'), parent=self.root)
            self._set_status_dot('off')
        self._refresh_shell_list()

    # ═══════ 面板管理 ═══════
    def _init_panels(self):
        """初始化面板（异步，不阻塞 UI）"""
        if not self.connector: return
        self.terminal_panel.clear()
        self.file_panel.clear()
        self.file_panel.current_path = '.'
        self.file_panel.path_var.set('.')
        connector = self.connector
        threading.Thread(target=self._do_init, args=(connector,), daemon=True).start()

    def _do_init(self, connector):
        info = connector.get_info()
        self.root.after(0, self._on_init, connector, info)

    def _on_init(self, connector, info):
        # 如果用户在此期间切换了其他 Shell，忽略此次结果
        if connector is not self.connector:
            return
        idx = self.current_shell_index
        if 'error' in info:
            self._shell_alive[idx] = False
            self.status_label.config(text='连接失败: %s' % info.get('error', '未知'))
            self._set_status_dot('off')
            self._refresh_shell_list()
            return
        self._shell_alive[idx] = True
        cwd = info.get('cwd', '.')
        self.file_panel.current_path = cwd
        self.file_panel.path_var.set(cwd)
        self.file_panel.refresh(cwd)
        self._set_status_dot('on')
        s = self.shell_manager.get(idx)
        self.status_label.config(text=f'已连接: {s.name}  ·  {s.url}')
        self._refresh_shell_list()

    def _clear_all_panels(self):
        self.file_panel.clear()
        self.terminal_panel.clear()
        self.database_panel.clear()

    def set_status(self, text):
        self.status_label.config(text=text)

    def _show_about(self):
        messagebox.showinfo('关于', '淬火 Quench\nWebshell 管理工具\n\n仅用于授权安全测试', parent=self.root)

    def _on_close(self):
        if not messagebox.askokcancel('退出', '确定退出？', parent=self.root):
            return
        # 停止终端轮询循环，避免 destroy 后 after 仍在调度导致无法退出
        try:
            self.terminal_panel._running = False
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ═══════ Shell 编辑对话框 ═══════
class ShellEditDialog(tk.Toplevel):
    def __init__(self, parent, title='添加 Shell', config=None, callback=None):
        super().__init__(parent)
        self.title(title)
        self.cb = callback
        self._finished = False        # 防重复触发
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        self._build(config)

        # 居中
        self.update_idletasks()
        w, h = 460, 380
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry('%dx%d+%d+%d' % (w, h, max(px, 0), max(py, 0)))

        self.protocol('WM_DELETE_WINDOW', self._cancel)
        self.bind('<Escape>', lambda e: self._cancel())

        self.lift()
        self.focus_force()
        # grab 延后，确保窗口就绪；保存 after ID 以便关闭时取消
        self._grab_after_id = self.after(50, lambda: self._safe(lambda: self.grab_set()))

    def _safe(self, fn):
        try:
            fn()
        except Exception:
            pass

    def _build(self, cfg):
        f = tk.Frame(self, bg=CARD, padx=20, pady=16)
        f.pack(fill=tk.BOTH, expand=True)

        title_text = '添加 Shell' if cfg is None else '编辑 Shell'
        tk.Label(f, text=title_text, bg=CARD, fg=TEXT,
                 font=(FONT, 14, 'bold')).pack(anchor='w', pady=(0, 12))

        for label, var_name, default in [
            ('名称', 'name', '靶机-1'),
            ('URL',   'url',  'http://'),
            ('密码', 'password', 'test'),
            ('备注', 'note', ''),
        ]:
            row = tk.Frame(f, bg=CARD)
            row.pack(fill=tk.X, pady=(6, 0))

            tk.Label(row, text=label, bg=CARD, fg=TEXT2,
                     font=(FONT, 9), width=5, anchor='w').pack(side=tk.LEFT)

            val = cfg.__getattribute__(var_name) if cfg else default
            v = tk.StringVar(value=val)
            show_char = '●' if var_name == 'password' else ''
            e = tk.Entry(row, textvariable=v, font=(FONT, 10),
                         bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                         relief='solid', borderwidth=1,
                         show=show_char)
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(4, 0))
            e.bind('<Return>', lambda e, dlg=self: dlg._ok())
            setattr(self, '_%s' % var_name, v)
            setattr(self, '_entry_%s' % var_name, e)

        # 按钮区
        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill=tk.X, pady=(20, 0))

        btn_cancel = tk.Button(bf, text='取消', command=self._cancel,
                               font=(FONT, 10), bg=CARD, fg=TEXT2,
                               relief='flat', padx=16, pady=6,
                               activebackground='#e8ecf0', activeforeground=TEXT,
                               borderwidth=1)
        btn_cancel.pack(side=tk.RIGHT, padx=(6, 0))

        btn_ok = tk.Button(bf, text='确定', command=self._ok,
                           font=(FONT, 10, 'bold'), bg=ACCENT, fg='#ffffff',
                           relief='flat', padx=20, pady=6,
                           activebackground='#0969da', activeforeground='#ffffff',
                           borderwidth=0)
        btn_ok.pack(side=tk.RIGHT)
        # 把焦点放到第一个输入框
        self._entry_name.focus_set()

    def _ok(self):
        if self._finished:
            return
        n = self._name.get().strip()
        u = self._url.get().strip()
        p = self._password.get().strip()
        nt = self._note.get().strip()
        if not n or not u or not p:
            messagebox.showwarning('提示', '名称、URL、密码不能为空', parent=self)
            return
        self._finish(ShellConfig(name=n, url=u, password=p, note=nt))

    def _cancel(self):
        if self._finished:
            return
        self._finish(None)

    def _finish(self, result):
        self._finished = True
        # 取消延后的 grab_set，避免在已销毁的窗口上设置 grab
        if hasattr(self, '_grab_after_id') and self._grab_after_id:
            try:
                self.after_cancel(self._grab_after_id)
            except Exception:
                pass
            self._grab_after_id = None
        self._safe(lambda: self.grab_release())
        cb = self.cb
        self.cb = None
        if cb:
            try:
                cb(result)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror('错误', f'操作失败: {e}', parent=self.master)
        # destroy 放在 after 中，确保当前事件处理完毕
        self.after(10, self.destroy)
