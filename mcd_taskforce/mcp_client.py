"""麦当劳中国 MCP Server 的 Streamable HTTP 客户端。

零第三方依赖（仅标准库），Python 3.8+ 可跑。
Token 一律从环境变量 MCD_MCP_TOKEN 读取，不落盘、不进代码。
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_MCP_URL = "https://mcp.mcd.cn"
PROTOCOL_VERSION = "2024-11-05"


class MCPError(Exception):
    """MCP 调用异常。"""


class MCDMCPClient:
    """麦当劳 MCP Server 客户端。

    用法::

        client = MCDMCPClient()               # 从环境变量读 Token
        client.initialize()
        tools = client.list_tools()
        result = client.call_tool("query-meals", {"storeId": "123"})
    """

    def __init__(self, token=None, url=None, timeout=30):
        self.url = (url or os.environ.get("MCD_MCP_URL") or DEFAULT_MCP_URL).rstrip("/")
        self.token = token or os.environ.get("MCD_MCP_TOKEN")
        self.timeout = timeout
        self._id = 0
        self._initialized = False

    # ---------- JSON-RPC 基础 ----------

    def _next_id(self):
        self._id += 1
        return self._id

    def _post(self, payload):
        if not self.token:
            raise MCPError(
                "未检测到 MCD_MCP_TOKEN。请先到 https://open.mcd.cn/mcp "
                "用手机号登录并在控制台激活领取 Token，然后: "
                "export MCD_MCP_TOKEN=<你的Token>"
            )
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, method="POST")
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "ignore")[:300]
            raise MCPError("HTTP {}: {}".format(exc.code, detail))
        except urllib.error.URLError as exc:
            raise MCPError("网络错误: {}".format(exc.reason))
        return self._parse_response(raw)

    @staticmethod
    def _parse_response(raw):
        """MCP Streamable HTTP 可能返回纯 JSON 或 SSE，两种都兼容。"""
        text = raw.strip()
        if not text:
            raise MCPError("空响应")
        if text.startswith("event:") or text.startswith("data:"):
            for line in text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[len("data:"):].strip())
            raise MCPError("无法解析 SSE 响应")
        return json.loads(text)

    def _rpc(self, method, params=None):
        payload = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            payload["params"] = params
        resp = self._post(payload)
        if "error" in resp:
            raise MCPError("RPC 错误 {}: {}".format(
                resp["error"].get("code"), resp["error"].get("message")))
        return resp.get("result", {})

    # ---------- MCP 协议 ----------

    def initialize(self):
        result = self._rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "mcd-taskforce", "version": "1.0.0"},
        })
        # initialized 通知（无 id，不需要响应）
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._initialized = True
        return result

    def list_tools(self):
        if not self._initialized:
            self.initialize()
        return self._rpc("tools/list").get("tools", [])

    def call_tool(self, name, arguments=None):
        if not self._initialized:
            self.initialize()
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}})

    def ping(self):
        """连通性自检，返回 True/False。"""
        try:
            self.initialize()
            return True
        except MCPError:
            return False
