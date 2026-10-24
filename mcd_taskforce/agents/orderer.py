"""下单员 Orderer —— 订单预览与执行。

安全设计：默认只生成订单预览（dry-run），绝不自动真实下单。
真实下单必须显式传 confirm=True，把决定权留给用户。
"""


class Orderer:
    ROLE = "下单员"
    MOTTO = "我的手只碰你点头的订单。"

    def __init__(self):
        pass

    def run(self, plan, picks, payable, client=None, use_mock=False,
            confirm=False, store=None):
        """生成订单预览；confirm=True 时才真正调用 create-order。"""
        from .. import mock_data

        order = {
            "agent": self.ROLE,
            "store": store or mock_data.MOCK_STORE,
            "items": [{"code": p["code"], "name": p["name"],
                       "price": p["price"]} for p in picks],
            "payable": payable,
            "status": "preview" if not confirm else "submitted",
        }

        if confirm and not use_mock and client is not None:
            resp = client.call_tool("create-order", {
                "storeId": order["store"]["storeId"],
                "items": [{"code": i["code"], "quantity": 1} for i in order["items"]],
            })
            order["mcp_response"] = resp
            order["status"] = "submitted"
        elif confirm:
            order["note"] = "mock 模式：模拟下单成功（未真实扣款）"

        return order

    def brief(self, result):
        lines = ["【下单员预览】"]
        lines.append("  门店: {}".format(result["store"]["name"]))
        for i in result["items"]:
            lines.append("  - {} {}元".format(i["name"], i["price"]))
        lines.append("  应付: {} 元".format(result["payable"]))
        lines.append("  状态: {}".format(
            "已提交（真实订单）" if result["status"] == "submitted" else "预览（未下单）"))
        if result.get("note"):
            lines.append("  " + result["note"])
        return "\n".join(lines)
