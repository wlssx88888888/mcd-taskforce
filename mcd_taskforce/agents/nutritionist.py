"""营养师 Nutritionist —— 营养配餐专家。

基于麦当劳 MCP 餐品营养数据，按任务单目标筛选组合。
"""


class Nutritionist:
    ROLE = "营养师"
    MOTTO = "每一口都算数。"

    def __init__(self):
        pass

    def run(self, plan, client=None, use_mock=False):
        """按任务单挑选餐品组合。

        策略:
        - 低卡: 优先 kcal/元 比高的餐品，总热量受预算约束
        - 高蛋白: 优先 protein 高的
        - 高饱腹: 优先 kcal 高且蛋白充足的
        - 均衡: 主食+小食+饮品各一
        """
        from .. import mock_data

        if use_mock or client is None:
            meals = mock_data.MOCK_MEALS
        else:
            resp = client.call_tool("list-nutrition-foods", {})
            meals = self._extract_meals(resp) or mock_data.MOCK_MEALS

        budget = plan["budget"]
        goals = plan["goal"]

        mains = [m for m in meals if m["category"] in ("主食", "早餐")]
        drinks = [m for m in meals if m["category"] == "饮品"]
        sides = [m for m in meals if m["category"] in ("小食", "甜品")]

        picks = self._select(mains, drinks, sides, goals, budget)

        total_kcal = sum(p["kcal"] for p in picks)
        total_protein = sum(p["protein"] for p in picks)
        total_price = round(sum(p["price"] for p in picks), 1)

        return {
            "agent": self.ROLE,
            "picks": picks,
            "total_kcal": total_kcal,
            "total_protein": total_protein,
            "subtotal": total_price,
            "comment": self._comment(goals, total_kcal, total_protein, budget),
        }

    @staticmethod
    def _select(mains, drinks, sides, goals, budget):
        """预算感知的性价比贪心选餐。

        每种营养目标有独立的排序键；先保主食，再用剩余预算
        贪心加饮品/小食，保证不超预算。
        """
        picks = []
        if not mains:
            mains = drinks or sides

        def remaining():
            return round(budget - sum(p["price"] for p in picks), 1)

        if "低卡" in goals:
            mains.sort(key=lambda m: m["kcal"] / m["price"])
            picks.append(mains[0])
            drinks.sort(key=lambda m: m["kcal"] / m["price"])
        elif "高蛋白" in goals:
            mains.sort(key=lambda m: -(m["protein"] / m["price"]))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["protein"] / m["price"]))
        elif "高饱腹" in goals:
            mains.sort(key=lambda m: -(m["kcal"] + m["protein"] * 5))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["kcal"] / m["price"]))
        else:  # 均衡
            mains.sort(key=lambda m: -(m["protein"] * 2 - m["kcal"] / 100.0))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["protein"] / m["price"]))

        # 剩余预算贪心：先饮品后小食，加满为止
        for extra in drinks + sides:
            if remaining() >= extra["price"]:
                picks.append(extra)

        # 保险：仍超预算就砍最贵的，保主食
        while len(picks) > 1 and remaining() < 0:
            picks.sort(key=lambda p: -p["price"])
            picks.pop(0)
        return picks

    @staticmethod
    def _extract_meals(resp):
        """从 MCP 返回中解析餐品列表（兼容 list-nutrition-foods / query-meals）。"""
        content = resp.get("content", []) if isinstance(resp, dict) else []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                import json
                try:
                    data = json.loads(block.get("text", "{}"))
                except ValueError:
                    continue
                for key in ("foods", "meals"):
                    if key in data:
                        return data[key]
        return None

    @staticmethod
    def _comment(goals, kcal, protein, budget):
        if "低卡" in goals:
            return "本组合热量 {} 千卡，蛋白质 {} g，控制在 {} 元内，减脂期友好。".format(kcal, protein, budget)
        if "高蛋白" in goals:
            return "蛋白质合计 {} g，训练后补给充足。".format(protein)
        if "高饱腹" in goals:
            return "热量 {} 千卡，饱腹感强，适合扛饿。".format(kcal)
        return "营养均衡组合：{} 千卡 / 蛋白 {} g。".format(kcal, protein)

    def brief(self, result):
        lines = ["【营养师配餐】"]
        for p in result["picks"]:
            lines.append("  {} {} {}元 {}千卡 蛋白{}g".format(
                p["name"], "(" + p["category"] + ")", p["price"],
                p["kcal"], p["protein"]))
        lines.append("  小计: {} 元 | 热量 {} 千卡 | 蛋白 {} g".format(
            result["subtotal"], result["total_kcal"], result["total_protein"]))
        lines.append("  点评: {}".format(result["comment"]))
        return "\n".join(lines)
