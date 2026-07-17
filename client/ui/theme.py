"""
Modern Light Theme — 现代化浅色主题
"""
import tkinter as tk
from tkinter import ttk

# ═══════ 色板 ═══════
BG       = '#f0f2f5'   # 页面底色（浅灰）
CARD     = '#ffffff'   # 卡片白
BORDER   = '#d8dee4'   # 边框浅灰
ACCENT   = '#0550ae'   # 主色蓝
ACCENT_L = '#ddf4ff'   # 浅蓝（选中/悬停）
SUCCESS  = '#1a7f37'   # 绿
WARN     = '#9a6700'   # 橙
DANGER   = '#cf222e'   # 红
TEXT     = '#1f2328'   # 主文字黑
TEXT2    = '#656d76'   # 次文字灰
INPUT_BG = '#f6f8fa'   # 输入框底色
TERM_BG  = '#f6f8fa'   # 终端底色

FONT = 'Microsoft YaHei UI'


def apply_theme(root: tk.Tk):
    """全局应用浅色现代主题"""
    root.configure(bg=BG)

    style = ttk.Style(root)
    avail = style.theme_names()
    base = 'clam' if 'clam' in avail else 'default'
    style.theme_use(base)

    # ── 全局默认 ──
    style.configure('.', font=(FONT, 10), background=BG, foreground=TEXT)

    # ── Frame ──
    style.configure('TFrame', background=BG)
    style.configure('Card.TFrame', background=CARD)
    style.configure('Sidebar.TFrame', background='#e8ecf0')

    # ── Label ──
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('Card.TLabel', background=CARD, foreground=TEXT)
    style.configure('Muted.TLabel', foreground=TEXT2, font=(FONT, 10))
    style.configure('Title.TLabel', font=(FONT, 14, 'bold'), foreground=TEXT)

    # ── Button ──
    style.configure('TButton', background=CARD, foreground=TEXT,
                    borderwidth=0, relief='flat', padding=(14, 7),
                    font=(FONT, 10))
    style.map('TButton', background=[('active', '#e8ecf0'), ('pressed', '#d0d7de')])

    # 主按钮
    style.configure('Primary.TButton', background=ACCENT, foreground='#ffffff',
                    borderwidth=0, relief='flat', padding=(16, 8),
                    font=(FONT, 10))
    style.map('Primary.TButton', background=[('active', '#0550ae'), ('pressed', '#033d8b')])

    # 小按钮
    style.configure('Small.TButton', background=CARD, foreground=TEXT2,
                    borderwidth=0, relief='flat', padding=(8, 4),
                    font=(FONT, 9))
    style.map('Small.TButton', background=[('active', '#e8ecf0')])

    # ── Entry ──
    style.configure('TEntry', fieldbackground=CARD, foreground=TEXT,
                    borderwidth=1, relief='solid', padding=(8, 6),
                    font=(FONT, 10))
    style.map('TEntry', bordercolor=[('focus', ACCENT)])

    # ── Treeview ──
    style.configure('Treeview', background=CARD, foreground=TEXT,
                    fieldbackground=CARD, borderwidth=0,
                    font=(FONT, 10), rowheight=30)
    style.configure('Treeview.Heading', background='#f0f2f5', foreground=TEXT2,
                    borderwidth=0, relief='flat',
                    font=(FONT, 9), padding=(10, 6))
    style.map('Treeview', background=[('selected', ACCENT_L)],
              foreground=[('selected', TEXT)])
    style.map('Treeview.Heading', background=[('active', '#e8ecf0')])

    # ── Notebook Tab ──
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', background='#f0f2f5', foreground=TEXT2,
                    borderwidth=0, padding=(20, 10), font=(FONT, 10))
    style.map('TNotebook.Tab',
              background=[('selected', CARD), ('active', '#e8ecf0')],
              foreground=[('selected', TEXT)])

    # ── PanedWindow ──
    style.configure('TPanedwindow', background=BG)
    style.configure('Sash', sashthickness=1)

    # ── Scrollbar ──
    style.configure('TScrollbar', background='#d8dee4', troughcolor='#f0f2f5',
                    borderwidth=0, arrowsize=14)
    style.map('TScrollbar', background=[('active', '#c0c8d0')])

    # ── Checkbutton ──
    style.configure('TCheckbutton', background=BG, foreground=TEXT, font=(FONT, 10))

    # ── Separator ──
    style.configure('TSeparator', background=BORDER)

    # ── LabelFrame ──
    style.configure('TLabelframe', background=CARD, foreground=TEXT2,
                    borderwidth=1, relief='solid', bordercolor=BORDER,
                    font=(FONT, 10))
    style.configure('TLabelframe.Label', background=CARD, foreground=TEXT2,
                    font=(FONT, 10))

    # ── 菜单 ──
    root.option_add('*Menu.background', CARD)
    root.option_add('*Menu.foreground', TEXT)
    root.option_add('*Menu.activeBackground', ACCENT_L)
    root.option_add('*Menu.activeForeground', TEXT)
    root.option_add('*Menu.borderWidth', 1)
    root.option_add('*Menu.relief', 'solid')
    root.option_add('*Menu.font', (FONT, 10))


def make_text(parent, **kw):
    return tk.Text(parent, bg=CARD, fg=TEXT, insertbackground=TEXT,
                   selectbackground=ACCENT_L, selectforeground=TEXT,
                   relief='flat', borderwidth=0, padx=10, pady=10,
                   font=(FONT, 10), **kw)


def make_card(parent, **kw):
    return ttk.Frame(parent, style='Card.TFrame', **kw)
