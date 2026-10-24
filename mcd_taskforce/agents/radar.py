"""雷达员 Radar —— 活动日历监控。

盯麦当劳活动日历 + 当前时间，提示近期可薅的羊毛。
"""


class Radar:
    ROLE = "雷达员"
    MOTTO = "风浪越大，鱼越贵；活动越多，省得越狠。"

    def __init__(self):
        pass

    def run(self, plan, client=None, use_mock=False):
        from .. import mock_data

        if use_mock or client is None:
            campaigns = mock_data.MOCK_CAMPAIGNS
            now = "2026-10-24T16:40:00+08:00"
        else:
            resp = client.call_tool("campaign-calendar", {})
            campaigns = self._extract_campaigns(resp) or mock_data.MOCK_CAMPAIGNS
            now_resp = client.call_tool("now-time-info", {})
            now = self._extract_now(now_resp) or "unknown"

        active = [c for c in campaigns if c.get("status") == "进行中"]
        upcoming = [c for c in campaigns if c.get("status") == "未开始"]

        tips = []
        if any("周三" in c["name"] or "周三" in c.get("desc", "") for c in active):
            tips.append("今天是周六，会员日是下周三，提前领券防身")
        for c in active:
            tips.append("进行中: {} —— {}".format(c["name"], c["desc"]))

        return {
            "agent": self.ROLE,
            "now": now,
            "active": active,
            "upcoming": upcoming,
            "tips": tips,
        }

    @staticmethod
    def _extract_campaigns(resp):
        content = resp.get("content", []) if isinstance(resp, dict) else []
        import json
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    data = json.loads(block.get("text", "{}"))
                except ValueError:
                    continue
                if "campaigns" in data:
                    return data["campaigns"]
        return None

    @staticmethod
    def _extract_now(resp):
        content = resp.get("content", []) if isinstance(resp, dict) else []
        import json
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    data = json.loads(block.get("text", "{}"))
                except ValueError:
                    continue
                return data.get("datetime")
        return None

    def brief(self, result):
        lines = ["【雷达员情报】"]
        lines.append("  当前时间: {}".format(result["now"]))
        for c in result["active"]:
            lines.append("  [进行中] {} ({}) {}".format(
                c["name"], c["date"], c["desc"]))
        for c in result["upcoming"]:
            lines.append("  [预告]   {} ({}) {}".format(
                c["name"], c["date"], c["desc"]))
        for t in result["tips"]:
            lines.append("  TIP: {}".format(t))
        return "\n".join(lines)
