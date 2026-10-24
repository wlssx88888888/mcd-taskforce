"""Mock 数据层：无 MCD_MCP_TOKEN 时，demo 用内置数据跑通全流程。

数据结构对齐麦当劳 MCP 各 Tool 的真实返回，便于无缝切换真实模式。
"""

# query-meals / list-nutrition-foods 风格
MOCK_MEALS = [
    {"code": "BIG_MAC", "name": "巨无霸", "category": "主食",
     "price": 23.5, "kcal": 520, "protein": 26, "fat": 28, "carb": 42, "sodium": 1050},
    {"code": "MC_CHICKEN", "name": "麦辣鸡腿堡", "category": "主食",
     "price": 21.0, "kcal": 480, "protein": 24, "fat": 25, "carb": 45, "sodium": 980},
    {"code": "FILET_O_FISH", "name": "麦香鱼", "category": "主食",
     "price": 18.5, "kcal": 380, "protein": 17, "fat": 16, "carb": 44, "sodium": 720},
    {"code": "MC_CAFE_LATTE_M", "name": "中杯拿铁", "category": "饮品",
     "price": 15.0, "kcal": 180, "protein": 10, "fat": 9, "carb": 18, "sodium": 120},
    {"code": "COKE_M", "name": "中杯可乐", "category": "饮品",
     "price": 8.0, "kcal": 160, "protein": 0, "fat": 0, "carb": 40, "sodium": 30},
    {"code": "ORANGE_JUICE_M", "name": "中杯橙汁", "category": "饮品",
     "price": 12.0, "kcal": 150, "protein": 2, "fat": 0, "carb": 36, "sodium": 20},
    {"code": "FRIES_M", "name": "中份薯条", "category": "小食",
     "price": 11.5, "kcal": 320, "protein": 4, "fat": 15, "carb": 42, "sodium": 290},
    {"code": "MC_NUGGETS_4", "name": "四块麦乐鸡", "category": "小食",
     "price": 10.5, "kcal": 190, "protein": 11, "fat": 11, "carb": 13, "sodium": 380},
    {"code": "APPLE_PIE", "name": "苹果派", "category": "甜品",
     "price": 7.5, "kcal": 230, "protein": 2, "fat": 10, "carb": 33, "sodium": 160},
    {"code": "SUNDAE_STRAWBERRY", "name": "草莓新地", "category": "甜品",
     "price": 9.0, "kcal": 260, "protein": 6, "fat": 6, "carb": 42, "sodium": 90},
    {"code": "MC_MUFFIN_EGG", "name": "猪柳蛋麦满分", "category": "早餐",
     "price": 13.0, "kcal": 400, "protein": 19, "fat": 20, "carb": 38, "sodium": 850},
    {"code": "CONGEE", "name": "皮蛋瘦肉粥", "category": "早餐",
     "price": 8.5, "kcal": 240, "protein": 8, "fat": 3, "carb": 46, "sodium": 620},
]

# available-coupons / query-store-coupons 风格
MOCK_COUPONS = [
    {"couponId": "CP-1001", "title": "堡卷省20元券", "type": "满减",
     "discount": 20.0, "minSpend": 40.0, "expire": "2026-10-31"},
    {"couponId": "CP-1002", "title": "麦乐鸡5元券", "type": "立减",
     "discount": 5.0, "minSpend": 10.0, "expire": "2026-10-28"},
    {"couponId": "CP-1003", "title": "饮品第二杯半价", "type": "折扣",
     "discount": 0.5, "minSpend": 0.0, "expire": "2026-11-05", "note": "第二杯半价"},
    {"couponId": "CP-1004", "title": "早餐粥品加1元换购", "type": "换购",
     "discount": 3.0, "minSpend": 12.0, "expire": "2026-10-31"},
]

# campaign-calendar 风格
MOCK_CAMPAIGNS = [
    {"name": "麦麦省周三会员日", "status": "进行中", "date": "2026-10-28",
     "desc": "每周三领券满40减20"},
    {"name": "巨无霸55周年纪念", "status": "进行中", "date": "2026-10-24 ~ 2026-11-02",
     "desc": "经典回归，限定周边兑换"},
    {"name": "万圣节幽灵套餐", "status": "未开始", "date": "2026-10-30 ~ 2026-11-01",
     "desc": "限定包装+抽奖活动"},
]

MOCK_STORE = {"storeId": "MOCK-001", "name": "麦当劳(科技园餐厅)",
              "address": "深圳市南山区科技园南路 1 号"}


def mock_call_tool(name, arguments=None):
    """按工具名返回对应 mock 数据，签名与真实 call_tool 对齐。"""
    arguments = arguments or {}
    table = {
        "list-nutrition-foods": {"foods": MOCK_MEALS},
        "query-meals": {"storeId": MOCK_STORE["storeId"], "meals": MOCK_MEALS},
        "query-meal-detail": {"meals": MOCK_MEALS},
        "available-coupons": {"coupons": MOCK_COUPONS},
        "query-store-coupons": {"coupons": MOCK_COUPONS},
        "query-my-coupons": {"coupons": MOCK_COUPONS[:2]},
        "auto-bind-coupons": {"claimed": ["CP-1001", "CP-1002"], "total": 2},
        "calculate-price": _mock_calculate_price(arguments),
        "campaign-calendar": {"campaigns": MOCK_CAMPAIGNS},
        "now-time-info": {"datetime": "2026-10-24T16:40:00+08:00", "weekday": "Saturday"},
        "query-nearby-stores": {"stores": [MOCK_STORE]},
        "query-my-account": {"available": 320, "total": 1580, "frozen": 0},
        "query-order": {"orderId": "MOCK-ORDER-001", "status": "制作中"},
        "order-list": {"orders": []},
    }
    return table.get(name, {"warning": "mock 模式暂不支持该工具: " + name})


def _mock_calculate_price(arguments):
    """按选购清单+优惠券算总价，逻辑与真实工具语义一致。"""
    items = arguments.get("items", [])
    coupon = arguments.get("coupon")
    total = 0.0
    for item in items:
        meal = next((m for m in MOCK_MEALS if m["code"] == item.get("code")), None)
        if meal:
            total += meal["price"] * item.get("quantity", 1)
    discount = 0.0
    if coupon:
        found = next((c for c in MOCK_COUPONS if c["couponId"] == coupon), None)
        if found and total >= found["minSpend"]:
            discount = found["discount"] if found["type"] != "折扣" else round(
                total * 0.5 / 2, 1)
    return {"total": round(total, 1), "discount": round(discount, 1),
            "payable": round(total - discount, 1)}
