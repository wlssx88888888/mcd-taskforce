"""营养师 Nutritionist —— 营养配餐专家。

基于麦当劳 MCP 餐品营养数据，按任务单目标筛选组合。
真实模式直接吃 MCP list-nutrition-foods 的 160 个餐品真实营养表。
"""

from .. import live_data


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
            meals = live_data.nutrition_to_meals(resp) or mock_data.MOCK_MEALS

        budget = plan["budget"]
        goals = plan["goal"]
        has_price = any(m.get("price") for m in meals)

        mains = [m for m in meals if m["category"] in ("主食", "早餐")]
        drinks = [m for m in meals if m["category"] == "饮品"]
        sides = [m for m in meals if m["category"] in ("小食", "甜品")]

        picks = self._select(mains, drinks, sides, goals, budget, has_price)

        total_kcal = sum(p["kcal"] for p in picks)
        total_protein = sum(p["protein"] for p in picks)
        priced = [p for p in picks if p.get("price")]
        total_price = round(sum(p["price"] for p in priced), 1) if len(priced) == len(picks) else None

        return {
            "agent": self.ROLE,
            "picks": picks,
            "total_kcal": total_kcal,
            "total_protein": total_protein,
            "subtotal": total_price,
            "has_price": has_price,
            "comment": self._comment(goals, total_kcal, total_protein, budget),
        }

    @staticmethod
    def _select(mains, drinks, sides, goals, budget, has_price=True):
        """营养目标优先的选餐；有价格时叠加预算感知贪心。

        真实营养表不带价格（price=None），此时退化为纯营养策略，
        价格交给省钱特工的 calculate-price 按门店实算。
        """
        picks = []
        if not mains:
            mains = drinks or sides

        def price_of(m):
            return m.get("price") if m.get("price") else 0.0

        def remaining():
            return round(budget - sum(price_of(p) for p in picks), 1)

        if "低卡" in goals:
            mains.sort(key=lambda m: m["kcal"] / max(price_of(m), 1.0))
            picks.append(mains[0])
            drinks.sort(key=lambda m: m["kcal"] / max(price_of(m), 1.0))
        elif "高蛋白" in goals:
            mains.sort(key=lambda m: -(m["protein"] / max(price_of(m), 1.0)))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["protein"] / max(price_of(m), 1.0)))
        elif "高饱腹" in goals:
            mains.sort(key=lambda m: -(m["kcal"] + m["protein"] * 5))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["kcal"] / max(price_of(m), 1.0)))
        else:  # 均衡
            mains.sort(key=lambda m: -(m["protein"] * 2 - m["kcal"] / 100.0))
            picks.append(mains[0])
            drinks.sort(key=lambda m: -(m["protein"] / max(price_of(m), 1.0)))

        # 剩余预算贪心：先饮品后小食，加满为止（无价格时全部纳入）
        for extra in drinks + sides:
            if not has_price or remaining() >= price_of(extra):
                picks.append(extra)

        # 保险：仍超预算就砍最贵的，保主食
        while len(picks) > 1 and remaining() < 0:
            picks.sort(key=lambda p: -price_of(p))
            picks.pop(0)

        # 无价格模式：控制组合规模，1 主食 + ≤2 饮品 + ≤1 小食（真人点餐逻辑）
        if not has_price and len(picks) > 4:
            main = picks[:1]
            drinks_picked = [p for p in picks[1:] if p["category"] == "饮品"][:2]
            sides_picked = [p for p in picks[1:] if p["category"] in ("小食", "甜品")][:1]
            picks = main + drinks_picked + sides_picked
        return picks

    @staticmethod
    def _extract_meals(resp):
        """从 MCP 返回中解析餐品列表（兼容 list-nutrition-foods / query-meals）。"""
        meals = live_data.nutrition_to_meals(resp)
        return meals or None

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
            price = "{}元".format(p["price"]) if p.get("price") else "时价"
            lines.append("  {} {}{} {}千卡 蛋白{}g".format(
                p["name"], "(" + p["category"] + ")", price,
                p["kcal"], p["protein"]))
        subtotal = "{} 元".format(result["subtotal"]) if result["subtotal"] is not None else "以门店实价为准"
        lines.append("  小计: {} | 热量 {} 千卡 | 蛋白 {} g".format(
            subtotal, result["total_kcal"], result["total_protein"]))
        lines.append("  点评: {}".format(result["comment"]))
        return "\n".join(lines)
