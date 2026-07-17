"""
文件管理 — 浅色现代文件浏览器
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading, os, base64, datetime
from ui.theme import BG, CARD, BORDER, ACCENT, ACCENT_L, SUCCESS, DANGER, TEXT, TEXT2, INPUT_BG, FONT, make_text


class FileManagerPanel:
    def __init__(self, parent, main_window):
        self.main = main_window
        self.current_path = '.'
        self._sort_col = 'name'
        self._sort_asc = True
        self.frame = ttk.Frame(parent)
        self.frame.pack_propagate(False)
        self._build()

    def _build(self):
        # ── 工具栏 ──
        bar = tk.Frame(self.frame, bg=BG, height=40)
        bar.pack(fill=tk.X, padx=8, pady=(8, 4))
        bar.pack_propagate(False)

        self.path_var = tk.StringVar(value='.')
        pe = tk.Entry(bar, textvariable=self.path_var, font=(FONT, 10),
                      bg=CARD, fg=TEXT, insertbackground=TEXT,
                      relief='flat', borderwidth=1,
                      highlightbackground=BORDER, highlightthickness=1,
                      highlightcolor=ACCENT)
        pe.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 6))
        pe.bind('<Return>', lambda e: self.refresh())

        for t, c in [('跳转', self.refresh), ('上级', self._go_up),
                     ('根目录', self._go_root), ('刷新', self.refresh)]:
            ttk.Button(bar, text=t, command=c, style='Small.TButton',
                       width=6).pack(side=tk.LEFT, padx=2)

        # ── 文件列表 ──
        cols = ('name', 'type', 'size', 'mtime', 'perms')
        self.tree = ttk.Treeview(self.frame, columns=cols, show='headings',
                                 selectmode='extended')
        self.tree.heading('name', text='文件名', command=lambda: self._sort('name'))
        self.tree.heading('type', text='类型', command=lambda: self._sort('type'))
        self.tree.heading('size', text='大小', command=lambda: self._sort('size'))
        self.tree.heading('mtime', text='修改时间', command=lambda: self._sort('mtime'))
        self.tree.heading('perms', text='权限')

        self.tree.column('name', width=300, minwidth=160)
        self.tree.column('type', width=55, minwidth=50, anchor=tk.CENTER)
        self.tree.column('size', width=80, minwidth=70, anchor=tk.E)
        self.tree.column('mtime', width=145, minwidth=130)
        self.tree.column('perms', width=70, minwidth=60, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8, 0), pady=(0, 8))

        ys = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        xs = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 8), pady=(0, 8))
        xs.pack(fill=tk.X, side=tk.BOTTOM, padx=(8, 0))

        self.tree.tag_configure('dir', foreground=ACCENT)
        self.tree.tag_configure('file', foreground=TEXT)

        self.tree.bind('<Double-1>', self._on_dbl)
        self.tree.bind('<Button-3>', self._on_rclick)

    # ═══════ 导航 ═══════
    def refresh(self, path=None):
        if not self.main.connector: return
        if path is not None:
            self.current_path = path
        else:
            self.current_path = self.path_var.get() or '.'
        self.path_var.set(self.current_path)
        self.main.set_status('正在列出 %s ...' % self.current_path)
        threading.Thread(target=self._do_list, args=(self.current_path,), daemon=True).start()

    def _do_list(self, path):
        r = self.main.connector.list_dir(path)
        self.main.root.after(0, self._on_list, path, r)

    def _on_list(self, path, r):
        self.current_path = path
        self.path_var.set(path)
        self.tree.delete(*self.tree.get_children())
        if 'error' in r:
            self.main.set_status('错误: %s' % r['error']); return
        items = r.get('items', [])
        for it in items:
            n, ft = it['name'], it['type']
            sz = fmt_size(it.get('size', 0)) if ft == 'file' else '-'
            mt = fmt_time(it.get('mtime', 0))
            self.tree.insert('', tk.END,
                             values=(n, ft.upper(), sz, mt, it.get('perms', '---')),
                             tags=(ft,))
        self.main.set_status('%s  -  %d 项 (%.2fs)' % (path, len(items), r.get('_elapsed', 0)))

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.path_var.set('.')
        self.current_path = '.'

    def _go_up(self):
        p = self.current_path.rstrip('/')
        if not p or p == '.': self.refresh('.'); return
        pp = os.path.dirname(p)
        if not pp or pp == p: pp = 'C:/'
        self.refresh(pp)

    def _go_root(self):
        self.refresh('C:/')

    # ═══════ 排序 ═══════
    def _sort(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        rows.sort(key=lambda x: x[0], reverse=not self._sort_asc)
        for i, (_, k) in enumerate(rows):
            self.tree.move(k, '', i)

    # ═══════ 双击 ═══════
    def _on_dbl(self, event):
        it = self.tree.focus()
        if not it: return
        vals = self.tree.item(it, 'values')
        if not vals: return
        n, ft = vals[0], vals[1]
        fp = os.path.join(self.current_path, n).replace('\\', '/')
        if ft == 'DIR':
            self.refresh(fp)
        else:
            self._edit_file(fp)

    # ═══════ 右键菜单 ═══════
    def _on_rclick(self, event):
        sel = self.tree.selection()
        menu = tk.Menu(self.frame, tearoff=0, bg=CARD, fg=TEXT,
                       activebackground=ACCENT_L, activeforeground=TEXT,
                       font=(FONT, 10))
        if sel:
            menu.add_command(label='读取', command=self._read_selected)
            menu.add_command(label='编辑', command=lambda: self._edit_file(self._get_first()))
            menu.add_separator()
            menu.add_command(label='重命名', command=self._rename_selected)
            menu.add_command(label='删除', command=self._delete_selected)
            menu.add_separator()
            menu.add_command(label='修改权限', command=self._chmod_selected)
        menu.add_separator()
        menu.add_command(label='上传文件', command=self._upload_file)
        menu.add_command(label='下载所选', command=self._download_selected)
        menu.add_separator()
        menu.add_command(label='新建文件', command=self._new_file)
        menu.add_command(label='新建目录', command=self._new_dir)
        menu.tk_popup(event.x_root, event.y_root)

    # ═══════ 路径工具 ═══════
    def _get_paths(self):
        out = []
        for s in self.tree.selection():
            n = self.tree.item(s, 'values')[0]
            out.append(os.path.join(self.current_path, n).replace('\\', '/'))
        return out

    def _get_first(self):
        ps = self._get_paths()
        return ps[0] if ps else ''

    # ═══════ 读取 ═══════
    def _read_selected(self):
        for p in self._get_paths():
            threading.Thread(target=self._do_read, args=(p,), daemon=True).start()

    def _do_read(self, p):
        self.main.set_status('正在读取 %s ...' % p)
        r = self.main.connector.read_file(p)
        self.main.root.after(0, self._show_viewer, p, r)

    def _show_viewer(self, path, r):
        if 'error' in r:
            self.main.set_status('错误: %s' % r['error']); return
        raw = r.get('content', '')
        txt = base64.b64decode(raw).decode('utf-8', errors='replace') if raw else ''
        sz = r.get('size', 0)

        win = tk.Toplevel(self.frame, bg=CARD)
        win.title(path)
        win.geometry('900x640')
        f, t, _s = _scr(win)                # 先创建可写的 Text
        f.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        t.insert('1.0', txt)
        t.config(state=tk.DISABLED)          # 插入完再设为只读
        ttk.Button(win, text='关闭', command=win.destroy).pack(pady=(0, 8))
        self.main.set_status('已读取 %s  (%s)' % (path, fmt_size(sz)))

    # ═══════ 编辑 ═══════
    def _edit_file(self, path):
        self.main.set_status('正在读取 %s ...' % path)
        threading.Thread(target=self._do_fetch_edit, args=(path,), daemon=True).start()

    def _do_fetch_edit(self, path):
        r = self.main.connector.read_file(path)
        self.main.root.after(0, self._open_editor, path, r)

    def _open_editor(self, path, r):
        if 'error' in r:
            messagebox.showerror('错误', r['error'], parent=self.frame); return
        raw = r.get('content', '')
        content = base64.b64decode(raw).decode('utf-8', errors='replace') if raw else ''

        win = tk.Toplevel(self.frame, bg=CARD)
        win.title('编辑: ' + os.path.basename(path))
        win.geometry('900x640')
        f, t, _s = _scr(win)
        f.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        t.insert('1.0', content)
        t.focus_set()

        def do_save():
            txt = t.get('1.0', 'end-1c')
            threading.Thread(target=self._do_save, args=(path, txt, win), daemon=True).start()

        bf = tk.Frame(win, bg=CARD)
        bf.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(bf, text='保存  Ctrl+S', command=do_save,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(bf, text='取消', command=win.destroy).pack(side=tk.LEFT)
        win.bind('<Control-s>', lambda e: do_save())

    def _do_save(self, path, content, win):
        r = self.main.connector.write_file(path, content)
        self.main.root.after(0, self._on_saved, path, win, r)

    def _on_saved(self, path, win, r):
        if 'error' in r:
            messagebox.showerror('保存失败', r['error'], parent=win)
        else:
            self.main.set_status('已保存 %s  (%d 字节)' % (path, r.get('written', 0)))
            win.destroy()
            self.refresh(self.current_path)

    # ═══════ 其余操作 ═══════
    def _delete_selected(self):
        ps = self._get_paths()
        if not ps: return
        if not messagebox.askyesno('确认删除', '删除？\n\n'+'\n'.join(ps), parent=self.frame): return
        for p in ps:
            threading.Thread(target=self._do_del, args=(p,), daemon=True).start()

    def _do_del(self, p):
        r = self.main.connector.delete(p)
        self.main.root.after(0, self.refresh)
        self.main.root.after(100, lambda: self.main.set_status(
            '已删除 %s' % p if 'error' not in r else '错误: %s' % r['error']))

    def _rename_selected(self):
        p = self._get_first()
        if not p: return
        nn = simpledialog.askstring('重命名', '新名称:', initialvalue=os.path.basename(p), parent=self.frame)
        if nn:
            threading.Thread(target=self._do_ren, args=(p, nn), daemon=True).start()

    def _do_ren(self, p, nn):
        r = self.main.connector.rename(p, nn)
        self.main.root.after(0, self.refresh)
        self.main.root.after(100, lambda: self.main.set_status(
            '已重命名 %s -> %s' % (p, nn) if 'error' not in r else '错误: %s' % r['error']))

    def _chmod_selected(self):
        p = self._get_first()
        if not p: return
        m = simpledialog.askstring('修改权限', 'Mode (0755/0644):', initialvalue='0755', parent=self.frame)
        if m:
            threading.Thread(target=self._do_chmod, args=(p, m), daemon=True).start()

    def _do_chmod(self, p, m):
        r = self.main.connector.chmod(p, m)
        self.main.root.after(0, self.refresh)
        self.main.root.after(100, lambda: self.main.set_status(
            'Chmod %s -> %s' % (p, m) if 'error' not in r else '错误: %s' % r['error']))

    def _upload_file(self):
        lf = filedialog.askopenfilename(title='选择要上传的文件', parent=self.frame)
        if not lf: return
        rf = os.path.join(self.current_path, os.path.basename(lf)).replace('\\', '/')
        threading.Thread(target=self._do_up, args=(lf, rf), daemon=True).start()

    def _do_up(self, lf, rf):
        self.main.set_status('正在上传 %s -> %s ...' % (lf, rf))
        r = self.main.connector.upload(rf, lf)
        self.main.root.after(0, self.refresh)
        self.main.root.after(100, lambda: self.main.set_status(
            '已上传 %s' % rf if 'error' not in r else '错误: %s' % r['error']))

    def _download_selected(self):
        ps = self._get_paths()
        if not ps: return
        ld = filedialog.askdirectory(title='保存到', parent=self.frame)
        if not ld: return
        for p in ps:
            threading.Thread(target=self._do_down, args=(p, ld), daemon=True).start()

    def _do_down(self, rp, ld):
        self.main.set_status('正在下载 %s ...' % rp)
        r = self.main.connector.read_file(rp)
        if 'error' not in r:
            lp = os.path.join(ld, os.path.basename(rp))
            raw = r.get('content', '')
            data = base64.b64decode(raw) if raw else b''
            with open(lp, 'wb') as f: f.write(data)
            self.main.root.after(0, lambda: self.main.set_status('已下载 %s' % rp))
        else:
            self.main.root.after(0, lambda: self.main.set_status('下载失败: %s' % r['error']))

    def _new_file(self):
        nm = simpledialog.askstring('新建文件', '文件名:', parent=self.frame)
        if not nm: return
        p = os.path.join(self.current_path, nm).replace('\\', '/')
        threading.Thread(target=self._do_write_open, args=(p, ''), daemon=True).start()

    def _do_write_open(self, p, c):
        r = self.main.connector.write_file(p, c)
        if 'error' not in r:
            self.main.root.after(0, lambda: self.refresh())
            self.main.root.after(400, self._edit_file, p)
        else:
            self.main.root.after(0, lambda: messagebox.showerror('创建失败', r['error'], parent=self.frame))

    def _new_dir(self):
        nm = simpledialog.askstring('新建目录', '目录名:', parent=self.frame)
        if not nm: return
        p = os.path.join(self.current_path, nm).replace('\\', '/')
        threading.Thread(target=self._do_mkdir, args=(p,), daemon=True).start()

    def _do_mkdir(self, p):
        r = self.main.connector.send({'action': 'write', 'path': p + '/._', 'content': ''})
        self.main.root.after(0, self.refresh)
        self.main.root.after(100, lambda: self.main.set_status(
            '已创建 %s' % p if 'error' not in r else '错误: %s' % r['error']))


# ═══════ 工具函数 ═══════
def fmt_size(sz):
    if sz < 1024:    return '%d B' % sz
    if sz < 1024**2: return '%.1f KB' % (sz/1024)
    if sz < 1024**3: return '%.1f MB' % (sz/1024**2)
    return '%.1f GB' % (sz/1024**3)

def fmt_time(ts):
    if not ts: return '-'
    try: return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    except: return str(ts)

def _scr(parent, **kw):
    f = tk.Frame(parent, bg=CARD)
    f.grid_rowconfigure(0, weight=1); f.grid_columnconfigure(0, weight=1)
    t = make_text(f, **kw)
    s = ttk.Scrollbar(f, orient=tk.VERTICAL, command=t.yview)
    t.configure(yscrollcommand=s.set)
    t.grid(row=0, column=0, sticky='nsew')
    s.grid(row=0, column=1, sticky='ns')
    return f, t, s
