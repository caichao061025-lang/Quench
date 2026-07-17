"""
终端 — 浅色现代命令行
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading, queue
from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT_L, SUCCESS, DANGER, TEXT, TEXT2, INPUT_BG, FONT

T_BG   = '#ffffff'
T_OUT  = '#1f2328'
T_ERR  = '#cf222e'
T_INFO = '#0550ae'
T_DIM  = '#8b949e'
T_CMD  = '#1f2328'


class TerminalPanel:
    def __init__(self, parent, main_window):
        self.main = main_window
        self.history = []
        self.hi = -1
        self._queue = queue.Queue()
        self._running = False
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        # ── 输出区 ──
        of = tk.Frame(self.frame, bg=T_BG, highlightbackground=BORDER,
                      highlightthickness=1)
        of.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 2))

        self.out = tk.Text(of, wrap=tk.WORD, font=(FONT, 10),
                           bg=T_BG, fg=T_OUT, insertbackground=T_OUT,
                           selectbackground=ACCENT_L, selectforeground=TEXT,
                           relief='flat', borderwidth=0, padx=12, pady=10,
                           state=tk.DISABLED)
        vs = ttk.Scrollbar(of, orient=tk.VERTICAL, command=self.out.yview)
        self.out.configure(yscrollcommand=vs.set)
        self.out.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vs.pack(fill=tk.Y, side=tk.RIGHT)

        self.out.tag_configure('cmd', foreground='#0550ae', font=(FONT, 10, 'bold'))
        self.out.tag_configure('out', foreground=T_OUT)
        self.out.tag_configure('err', foreground=T_ERR)
        self.out.tag_configure('info', foreground=T_INFO)
        self.out.tag_configure('dim', foreground=T_DIM)

        self.out.bind('<Button-1>', lambda e: self.cmd_entry.focus_set())
        self.out.bind('<ButtonRelease-1>', lambda e: self.cmd_entry.focus_set())

        # ── 输入行 ──
        inf = tk.Frame(self.frame, bg=BG, height=38)
        inf.pack(fill=tk.X, padx=8, pady=(2, 8))
        inf.pack_propagate(False)

        tk.Label(inf, text='$', bg=BG, fg=ACCENT, font=(FONT, 12, 'bold')).pack(
            side=tk.LEFT, padx=(8, 6))

        self.cmd_entry = tk.Entry(inf, font=(FONT, 10),
                                  bg=CARD, fg=TEXT, insertbackground=TEXT,
                                  relief='flat', borderwidth=1,
                                  highlightbackground=BORDER, highlightthickness=1,
                                  highlightcolor=ACCENT)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 4))
        self.cmd_entry.bind('<Return>', self._on_enter)
        self.cmd_entry.bind('<Up>', self._on_up)
        self.cmd_entry.bind('<Down>', self._on_down)
        self.cmd_entry.bind('<Control-c>', lambda e: self.cmd_entry.delete(0, tk.END))

        ttk.Button(inf, text='执行', command=self._exec, width=6,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(inf, text='清屏', command=self.clear, width=6).pack(side=tk.LEFT)

        # 欢迎
        self._w('Chopper 远程终端\n', 'info')
        self._w('在左侧选择一个 Shell，然后在下方输入命令按回车执行\n', 'dim')
        self._w('─' * 50 + '\n\n', 'dim')

        self._running = True
        self._process()
        self.frame.after(200, self.cmd_entry.focus_set)

    def _w(self, text, tag='out'):
        self.out.config(state=tk.NORMAL)
        self.out.insert(tk.END, text, tag)
        self.out.see(tk.END)
        self.out.config(state=tk.DISABLED)

    def focus_input(self):
        self.cmd_entry.focus_set()

    def _on_enter(self, e):
        self._exec()

    def _exec(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        if not self.main.connector:
            self._w('[!] 请先选择一个 Shell\n', 'err'); return

        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.hi = len(self.history)
        self.cmd_entry.delete(0, tk.END)

        self._w('$ ' + cmd + '\n', 'cmd')
        threading.Thread(target=self._do, args=(cmd,), daemon=True).start()

    def _do(self, cmd):
        r = self.main.connector.exec_cmd(cmd)
        self._queue.put(r)

    def _process(self):
        try:
            while True:
                r = self._queue.get_nowait()
                if 'error' in r:
                    self._w('[错误] ' + r['error'] + '\n', 'err')
                else:
                    ot = r.get('output', '')
                    if ot: self._w(ot.rstrip() + '\n', 'out')
                    if r.get('retval', 0):
                        self._w('[返回码 %d] ' % r['retval'], 'err')
                    self._w('[%.2fs]\n' % r.get('_elapsed', 0), 'dim')
        except queue.Empty:
            pass
        if self._running:
            self.frame.after(200, self._process)

    def _on_up(self, e):
        if not self.history: return
        if self.hi > 0:
            self.hi -= 1
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.history[self.hi])

    def _on_down(self, e):
        if self.hi < len(self.history) - 1:
            self.hi += 1
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.history[self.hi])
        else:
            self.hi = len(self.history)
            self.cmd_entry.delete(0, tk.END)

    def clear(self):
        self.out.config(state=tk.NORMAL)
        self.out.delete('1.0', tk.END)
        self.out.config(state=tk.DISABLED)
        self._w('终端已清空\n', 'dim')
        self.cmd_entry.focus_set()

