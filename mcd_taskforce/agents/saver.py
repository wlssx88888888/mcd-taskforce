"""省钱特工 Saver —— 凑券算价最优解。

在预算内挑选可用优惠券，用 calculate-price 验证实付金额，
保证"嘴上说省"和"账上真省"对得上。
"""


class Saver:
    ROLE = "省钱特工"
    MOTTO = "每一分钱都要花出回响。"

    def __init__(self):
        pass

    def run(self, plan, picks, client=None, use_mock=False):
        """为营养师的配餐挑选最优券。

        :param picks: 营养师选出的餐品列表
        """
        from .. import mock_data

        if use_mock or client is None:
            coupons = mock_data.MOCK_COUPONS
        else:
            resp = client.call_tool("available-coupons", {})
            coupons = self._extract_coupons(resp) or mock_data.MOCK_COUPONS

        subtotal = round(sum(p["price"] for p in picks), 1)
        best = None
        for c in coupons:
            saving = self._estimate_saving(c, subtotal)
            if saving is None or saving <= 0:
                continue
            candidate = {
                "coupon": c, "estimated_saving": saving,
                "estimated_payable": round(subtotal - saving, 1),
            }
            if best is None or candidate["estimated_payable"] < best["estimated_payable"]:
                best = candidate

        # 用 calculate-price 交叉验证（真实模式才调；mock 模式本地验证）
        verified = None
        if best:
            if use_mock or client is None:
                verified = mock_data._mock_calculate_price({
                    "items": [{"code": p["code"], "quantity": 1} for p in picks],
                    "coupon": best["coupon"]["couponId"],
                })
            else:
                resp = client.call_tool("calculate-price", {
                    "items": [{"code": p["code"], "quantity": 1} for p in picks],
                    "coupon": best["coupon"]["couponId"],
                })
                verified = self._extract_price(resp)

        return {
            "agent": self.ROLE,
            "subtotal": subtotal,
            "best_coupon": best["coupon"] if best else None,
            "saving": round(verified["discount"], 1) if verified else 0.0,
            "payable": round(verified["payable"], 1) if verified else subtotal,
            "within_budget": (verified["payable"] if verified else subtotal) <= plan["budget"],
            "unused_coupons": [c for c in coupons if not best or c["couponId"] != best["coupon"]["couponId"]],
        }

    @staticmethod
    def _estimate_saving(coupon, subtotal):
        if subtotal < coupon.get("minSpend", 0):
            return None
        if coupon["type"] == "折扣":
            # 简化：第二杯半价类按 5 折估一半差价
            return round(subtotal * 0.25, 1)
        return coupon.get("discount", 0)

    @staticmethod
    def _extract_coupons(resp):
        content = resp.get("content", []) if isinstance(resp, dict) else []
        import json
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    data = json.loads(block.get("text", "{}"))
                except ValueError:
                    continue
                if "coupons" in data:
                    return data["coupons"]
        return None

    @staticmethod
    def _extract_price(resp):
        content = resp.get("content", []) if isinstance(resp, dict) else []
        import json
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    data = json.loads(block.get("text", "{}"))
                except ValueError:
                    continue
                if "payable" in data:
                    return data
        return None

    def brief(self, result):
        lines = ["【省钱特工战报】"]
        lines.append("  配餐原价: {} 元".format(result["subtotal"]))
        if result["best_coupon"]:
            c = result["best_coupon"]
            lines.append("  选用优惠券: {} ({})".format(c["title"], c["couponId"]))
            lines.append("  立省: {} 元 → 实付 {} 元".format(result["saving"], result["payable"]))
            lines.append("  预算达标: {}".format("是" if result["within_budget"] else "否"))
        else:
            lines.append("  当前无可用券，原价购买")
        if result["unused_coupons"]:
            lines.append("  备选未用券: " + ", ".join(
                c["title"] for c in result["unused_coupons"]))
        return "\n".join(lines)
