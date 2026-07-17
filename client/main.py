#!/usr/bin/env python3
"""
淬火 (Quench) - Webshell 管理工具
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.theme import apply_theme
from ui.main_window import MainWindow

def main():
    app = MainWindow()
    apply_theme(app.root)
    app.run()

if __name__ == '__main__':
    main()
