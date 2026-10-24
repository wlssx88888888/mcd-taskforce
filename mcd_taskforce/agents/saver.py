"""省钱特工 Saver —— 凑券算价最优解。

在预算内挑选可用优惠券，用 calculate-price 验证实付金额，
保证"嘴上说省"和"账上真省"对得上。

真实模式下面包屑：available-coupons 返回的是 markdown 券列表，
券上没有结构化折扣字段，且 calculate-price 需要门店编码。
因此真实模式的策略是「券情报优先，实算尽力」：
- 有卡包券 + 有价格 → 尽力 calculate-price 实算
- 无价格（纯营养表）或无门店 → 输出可领券情报，明确标注需门店实算
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
        from .. import live_data

        if use_mock or client is None:
            coupons = mock_data.MOCK_COUPONS
        else:
            resp = client.call_tool("available-coupons", {})
            coupons = live_data.parse_coupon_markdown(
                live_data.extract_text(resp)) or mock_data.MOCK_COUPONS

        priced = [p for p in picks if p.get("price")]
        subtotal = round(sum(p["price"] for p in priced), 1) if priced and len(priced) == len(picks) else None

        best = None
        if subtotal is not None:
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
        verify_note = None
        if best:
            if use_mock or client is None:
                verified = mock_data._mock_calculate_price({
                    "items": [{"code": p["code"], "quantity": 1} for p in picks],
                    "coupon": best["coupon"]["couponId"],
                })
            else:
                try:
                    resp = client.call_tool("calculate-price", {
                        "items": [{"code": p["code"], "quantity": 1} for p in picks],
                        "coupon": best["coupon"]["couponId"],
                    })
                    verified = self._extract_price(resp)
                except Exception as exc:  # 缺门店编码等场景，降级为估算值
                    verify_note = "calculate-price 未返回实价（{}），以下为估算".format(
                        getattr(exc, "args", [exc])[0] if getattr(exc, "args", None) else exc)

        payable = round(verified["payable"], 1) if verified else (
            best["estimated_payable"] if best else subtotal)

        return {
            "agent": self.ROLE,
            "subtotal": subtotal,
            "best_coupon": best["coupon"] if best else None,
            "estimated_saving": best["estimated_saving"] if best else 0.0,
            "saving": round(verified["discount"], 1) if verified else (best["estimated_saving"] if best else 0.0),
            "payable": payable,
            "within_budget": (payable is not None and payable <= plan["budget"]),
            "verify_note": verify_note,
            "available_titles": [c.get("title", "") for c in coupons if c.get("title")],
            "unused_coupons": [c for c in coupons if not best or c.get("couponId") != best["coupon"].get("couponId")],
        }

    @staticmethod
    def _estimate_saving(coupon, subtotal):
        # 真实 markdown 券没有结构化门槛/面额，无法可靠估算
        min_spend = coupon.get("minSpend")
        discount = coupon.get("discount")
        if min_spend is None or discount is None:
            return None
        if subtotal < min_spend:
            return None
        if coupon.get("type") == "折扣":
            # 简化：第二杯半价类按 5 折估一半差价
            return round(subtotal * 0.25, 1)
        return discount

    @staticmethod
    def _extract_coupons(resp):
        from .. import live_data
        return live_data.parse_coupon_markdown(live_data.extract_text(resp)) or None

    @staticmethod
    def _extract_price(resp):
        from .. import live_data
        payload = live_data.extract_original_json(live_data.extract_text(resp))
        if payload and "payable" in payload:
            return payload
        return None

    def brief(self, result):
        lines = ["【省钱特工战报】"]
        if result["subtotal"] is not None:
            lines.append("  配餐原价: {} 元".format(result["subtotal"]))
        else:
            lines.append("  配餐价格以门店实价为准，先看券情报")
        if result["best_coupon"]:
            c = result["best_coupon"]
            lines.append("  选用优惠券: {} ({})".format(c.get("title", ""), c.get("couponId", "")))
            lines.append("  立省: {} 元 → 实付 {} 元".format(result["saving"], result["payable"]))
            if result["verify_note"]:
                lines.append("  备注: {}".format(result["verify_note"]))
        else:
            lines.append("  当前无可用券，原价购买")
        if result["available_titles"]:
            lines.append("  可领券情报: " + ", ".join(result["available_titles"][:6]))
        return "\n".join(lines)
