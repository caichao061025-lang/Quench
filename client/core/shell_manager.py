"""
Shell 管理器 - 多 Webshell 配置管理

支持添加、删除、修改、切换不同的 Webshell
配置文件默认存放在 EXE 同目录下（打包后）或 client/ 下（源码运行）
"""
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional


def _get_default_config_path() -> str:
    """获取默认配置文件的存储路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：EXE 同目录下的 config.json
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'config.json')
    else:
        # 源码运行：client/ 目录下的 config.json
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')


@dataclass
class ShellConfig:
    """单个 Webshell 的配置"""
    name: str           # 显示名称
    url: str            # Webshell URL
    password: str       # 连接密码
    note: str = ''      # 备注
    encoding: str = 'utf-8'  # 字符编码

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> 'ShellConfig':
        return ShellConfig(
            name=d.get('name', ''),
            url=d.get('url', ''),
            password=d.get('password', ''),
            note=d.get('note', ''),
            encoding=d.get('encoding', 'utf-8'),
        )


class ShellManager:
    """管理多个 Shell 配置"""

    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = _get_default_config_path()
        self.config_file = config_file
        self.shells: list[ShellConfig] = []
        self._load()

    def _load(self):
        """从 JSON 文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.shells = [ShellConfig.from_dict(s) for s in data.get('shells', [])]
            except (json.JSONDecodeError, Exception):
                self.shells = []
        else:
            self.shells = []

    def _save(self):
        """保存配置到 JSON 文件（不抛异常）"""
        data = {'shells': [s.to_dict() for s in self.shells]}
        try:
            dirname = os.path.dirname(self.config_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            # 权限不足或磁盘满时静默忽略，shell 仍在内存中可用
            pass

    def add(self, config: ShellConfig):
        """添加一个 Shell 配置"""
        self.shells.append(config)
        self._save()

    def remove(self, index: int):
        """删除指定索引的 Shell"""
        if 0 <= index < len(self.shells):
            self.shells.pop(index)
            self._save()

    def update(self, index: int, config: ShellConfig):
        """更新指定索引的 Shell"""
        if 0 <= index < len(self.shells):
            self.shells[index] = config
            self._save()

    def get(self, index: int) -> Optional[ShellConfig]:
        """获取指定索引的 Shell"""
        if 0 <= index < len(self.shells):
            return self.shells[index]
        return None

    def get_all(self) -> list[ShellConfig]:
        return self.shells

    def count(self) -> int:
        return len(self.shells)
