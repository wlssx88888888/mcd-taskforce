"""编排器 Orchestrator —— 麦门特工队的大脑。

流水线: 队长拆单 → 营养师配餐 → 省钱特工凑券 → 雷达员情报 → 下单员预览。
真实模式走麦当劳 MCP；无 Token 时自动降级 mock 数据，demo 永远可跑。
"""

from .agents import Captain, Nutritionist, Saver, Radar, Orderer
from .mcp_client import MCDMCPClient, MCPError


class TaskForce:
    """麦门特工队。

    用法::

        from mcd_taskforce import TaskForce
        tf = TaskForce()                    # 自动读 MCD_MCP_TOKEN，无则 mock
        report = tf.run("加班餐，30块以内，多来点蛋白")
        print(report["brief"])
    """

    def __init__(self, client=None, use_mock=None, verbose=True):
        self.verbose = verbose
        if client is not None:
            self.client = client
            self.use_mock = bool(use_mock)
        else:
            try:
                self.client = MCDMCPClient()
                self.client.initialize()
                self.use_mock = False
            except MCPError:
                self.client = None
                self.use_mock = True
        self.captain = Captain()
        self.nutritionist = Nutritionist()
        self.saver = Saver()
        self.radar = Radar()
        self.orderer = Orderer()

    # ---------- 流水线 ----------

    def run(self, mission, confirm_order=False, store=None):
        """执行一次任务，返回完整报告 dict。"""
        self._log("队长接单: {}".format(mission))
        plan = self.captain.run(mission, self.client, self.use_mock)
        self._log(self.captain.brief(plan))

        picks_result = self.nutritionist.run(plan, self.client, self.use_mock)
        self._log(self.nutritionist.brief(picks_result))

        saver_result = self.saver.run(plan, picks_result["picks"],
                                      self.client, self.use_mock)
        self._log(self.saver.brief(saver_result))

        radar_result = self.radar.run(plan, self.client, self.use_mock)
        self._log(self.radar.brief(radar_result))

        order_result = self.orderer.run(
            plan, picks_result["picks"], saver_result["payable"],
            self.client, self.use_mock, confirm=confirm_order, store=store)
        self._log(self.orderer.brief(order_result))

        brief = "\n\n".join([
            self.captain.brief(plan),
            self.nutritionist.brief(picks_result),
            self.saver.brief(saver_result),
            self.radar.brief(radar_result),
            self.orderer.brief(order_result),
        ])

        return {
            "mission": mission,
            "mode": "mock" if self.use_mock else "live",
            "plan": plan,
            "nutrition": picks_result,
            "saving": saver_result,
            "radar": radar_result,
            "order": order_result,
            "brief": brief,
        }

    # ---------- 工具 ----------

    def tools(self):
        """列出麦当劳 MCP 当前可用工具（mock 模式返回内置工具名）。"""
        if self.use_mock:
            return sorted(self._mock_tool_names())
        return [t.get("name") for t in self.client.list_tools()]

    @staticmethod
    def _mock_tool_names():
        """mock 模式下的内置工具名清单（对齐麦当劳 MCP 常用子集）。"""
        return list(_MOCK_TOOLS)

    def _log(self, text):
        if self.verbose:
            print(text)


_MOCK_TOOLS = [
    "auto-bind-coupons", "available-coupons", "calculate-price",
    "campaign-calendar", "create-order", "list-nutrition-foods",
    "now-time-info", "order-list", "query-meal-detail", "query-meals",
    "query-my-account", "query-my-coupons", "query-nearby-stores",
    "query-order", "query-store-coupons",
]
