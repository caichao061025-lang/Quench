"""
数据库 — 浅色现代 SQL 面板
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from ui.theme import (BG, CARD, BORDER, ACCENT, ACCENT_L, SUCCESS, DANGER,
                      TEXT, TEXT2, INPUT_BG, FONT, make_text)


class DatabasePanel:
    def __init__(self, parent, main_window):
        self.main = main_window
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        # ── 连接配置 ──
        card = tk.Frame(self.frame, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.X, padx=8, pady=(8, 4))

        inner = tk.Frame(card, bg=CARD, padx=16, pady=12)
        inner.pack(fill=tk.X)

        tk.Label(inner, text='数据库连接', bg=CARD, fg=TEXT,
                 font=(FONT, 11, 'bold')).pack(anchor='w', pady=(0, 8))

        r1 = tk.Frame(inner, bg=CARD)
        r1.pack(fill=tk.X, pady=2)
        for lbl, var, w in [('主机', 'localhost', 16), ('端口', '3306', 7),
                            ('用户', 'root', 14), ('密码', '', 14)]:
            tk.Label(r1, text=lbl, bg=CARD, fg=TEXT2, font=(FONT, 10)).pack(side=tk.LEFT)
            e = tk.Entry(r1, font=(FONT, 10), width=w,
                         bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                         relief='flat', borderwidth=1,
                         highlightbackground=BORDER, highlightthickness=1,
                         highlightcolor=ACCENT)
            e.pack(side=tk.LEFT, padx=(2, 10), ipady=3)
            setattr(self, '_%s' % lbl, e)

        r2 = tk.Frame(inner, bg=CARD)
        r2.pack(fill=tk.X, pady=4)
        tk.Label(r2, text='数据库', bg=CARD, fg=TEXT2, font=(FONT, 10)).pack(side=tk.LEFT)
        self._数据库 = tk.Entry(r2, font=(FONT, 10), width=18,
                           bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                           relief='flat', borderwidth=1,
                           highlightbackground=BORDER, highlightthickness=1,
                           highlightcolor=ACCENT)
        self._数据库.pack(side=tk.LEFT, padx=(2, 8), ipady=3)

        ttk.Button(r2, text='执行查询', command=self._exec,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(r2, text='数据库列表', command=self._list_dbs,
                   style='Small.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(r2, text='表列表', command=self._list_tbls,
                   style='Small.TButton').pack(side=tk.LEFT, padx=2)

        # ── SQL 编辑区 ──
        sf = tk.Frame(self.frame, bg=CARD, highlightbackground=BORDER,
                      highlightthickness=1, height=90)
        sf.pack(fill=tk.X, padx=8, pady=4)
        sf.pack_propagate(False)

        self.sql = make_text(sf, height=4, wrap=tk.NONE)
        vs = ttk.Scrollbar(sf, orient=tk.VERTICAL, command=self.sql.yview)
        self.sql.configure(yscrollcommand=vs.set)
        self.sql.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vs.pack(fill=tk.Y, side=tk.RIGHT)
        self.sql.bind('<Control-Return>', lambda e: self._exec())
        self.sql.bind('<F5>', lambda e: self._exec())

        # ── 结果表格 ──
        rf = tk.Frame(self.frame, bg=BG)
        rf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 8))

        self.tree = ttk.Treeview(rf, show='headings', selectmode='extended')
        vs = ttk.Scrollbar(rf, orient=tk.VERTICAL, command=self.tree.yview)
        xs = ttk.Scrollbar(rf, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=xs.set)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vs.pack(fill=tk.Y, side=tk.RIGHT)
        xs.pack(fill=tk.X, side=tk.BOTTOM)

        self._res_lbl = tk.Label(self.frame, text='就绪', bg=BG, fg=TEXT2,
                                 font=(FONT, 9), anchor='w')
        self._res_lbl.pack(fill=tk.X, padx=12, pady=(0, 4))

    # ═══════ 查询 ═══════
    def _exec(self):
        if not self.main.connector:
            messagebox.showinfo('提示', '请先选择一个 Shell'); return
        sql = self.sql.get('1.0', 'end-1c').strip()
        if not sql:
            messagebox.showinfo('提示', '请输入 SQL'); return

        h = self._主机.get().strip()
        p = self._端口.get().strip()
        u = self._用户.get().strip()
        pw = self._密码.get().strip()
        db = self._数据库.get().strip()

        if not h:
            messagebox.showinfo('提示', '请输入主机地址'); return

        self._res_lbl.config(text='执行中...', fg=WARN)
        threading.Thread(target=self._do_q, args=(h, p, u, pw, db, sql), daemon=True).start()

    def _do_q(self, h, p, u, pw, db, sql):
        r = self.main.connector.db_query(h, p, u, pw, db, sql)
        self.main.root.after(0, self._show, r)

    def _show(self, r):
        self.tree.delete(*self.tree.get_children())
        for c in self.tree['columns']:
            self.tree.heading(c, text='')
        self.tree['columns'] = []

        if 'error' in r:
            self._res_lbl.config(text='错误: %s' % r['error'], fg=DANGER); return

        cols = r.get('columns', [])
        rows = r.get('rows', [])
        cnt = r.get('count', 0)
        el = r.get('_elapsed', 0)

        if not cols or not rows:
            self._res_lbl.config(text='%d 行 (%.2fs)' % (cnt, el), fg=TEXT2); return

        self.tree['columns'] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, minwidth=60)
        for row in rows:
            self.tree.insert('', tk.END, values=[str(row.get(c, '')) for c in cols])
        self._res_lbl.config(text='%d 行 (%.2fs)' % (cnt, el), fg=SUCCESS)

    def _list_dbs(self):
        self.sql.delete('1.0', tk.END)
        self.sql.insert('1.0', 'SHOW DATABASES')
        self._exec()

    def _list_tbls(self):
        self.sql.delete('1.0', tk.END)
        self.sql.insert('1.0', 'SHOW TABLES')
        self._exec()

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        for c in self.tree['columns']:
            self.tree.heading(c, text='')
        self.tree['columns'] = []
        self.sql.delete('1.0', tk.END)
        self._res_lbl.config(text='就绪', fg=TEXT2)
