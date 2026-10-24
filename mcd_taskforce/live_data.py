"""真实 MCP 数据解析层。

麦当劳 MCP 的工具返回不是规整的 JSON，而是「Markdown 说明书 + Original Response」
的混合体，营养表更是独有的 ``[N]{col1,col2}:`` 表格格式。
本模块负责把这些真实响应解析成结构化数据，让特工们吃到真子弹。

所有解析函数都是纯函数，方便单测；不依赖第三方库。
"""

import json
import re

_MARKER = "## Original Response"


# ---------- 通用：从 MCP 响应提取 JSON ----------

def extract_text(resp):
    """从 MCP tools/call 响应中取出第一段文本内容。

    兼容两种形态::

        {"result": {"content": [{"type": "text", "text": "..."}]}}  # 标准 RPC
        {"content": [{"type": "text", "text": "..."}]}              # 已拆封
    """
    if not isinstance(resp, dict):
        return ""
    blocks = resp.get("content")
    if blocks is None and isinstance(resp.get("result"), dict):
        blocks = resp["result"].get("content")
    for block in blocks or []:
        if isinstance(block, dict) and block.get("type") == "text":
            return block.get("text", "")
    return ""


def extract_original_json(text):
    """提取 ``## Original Response`` 之后的 JSON 对象。

    返回 dict；找不到或解析失败返回 None（有些工具直接返回 markdown 文本，
    如 available-coupons，需要专用解析器）。
    """
    if not text:
        return None
    idx = text.find(_MARKER)
    payload = text[idx + len(_MARKER):].strip() if idx >= 0 else text.strip()
    # JSON 后面可能跟着中文说明文字，用 raw_decode 只吃第一个完整对象
    try:
        obj, _ = json.JSONDecoder().raw_decode(payload)
        return obj if isinstance(obj, dict) else None
    except ValueError:
        return None


# ---------- 麦当劳独有表格格式 ----------

_TABLE_HEADER = re.compile(r"^\[(\d+)\]\{([^}]*)\}:\s*$")


def parse_mcd_table(data_str):
    """解析麦当劳 ``[N]{col1,col2,...}:`` 表格格式。

    示例输入::

        [160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:
          猪柳蛋麦满分,null,1618,387,23,21,25,846,243

    返回 list[dict]，列名作 key。解析失败返回 []。
    """
    if not isinstance(data_str, str):
        return []
    lines = [ln.strip() for ln in data_str.strip().splitlines()]
    if not lines:
        return []
    m = _TABLE_HEADER.match(lines[0])
    if not m:
        return []
    cols = [c.strip() for c in m.group(2).split(",")]
    rows = []
    for ln in lines[1:]:
        if not ln:
            continue
        # 值里可能含逗号（如"能量约清水1杯"），按列数切：前 N-1 个逗号切开，
        # 最后一段允许自带逗号
        parts = ln.split(",")
        if len(parts) > len(cols):
            head = parts[:len(cols) - 1]
            tail = ",".join(parts[len(cols) - 1:])
            parts = head + [tail]
        if len(parts) < len(cols):
            parts += [""] * (len(cols) - len(parts))
        rows.append({col: parts[i].strip() for i, col in enumerate(cols)})
    return rows


# ---------- 营养数据 ----------

def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def nutrition_to_meals(resp):
    """把 list-nutrition-foods 的真实响应转成统一餐品结构。

    返回的每个餐品含: name / kcal / protein / fat / carb / sodium / category。
    price 为 None——营养接口不带价格，价格走 query-meals（需门店编码）。
    """
    text = extract_text(resp)
    payload = extract_original_json(text)
    if not payload:
        return []
    rows = parse_mcd_table(payload.get("data", ""))
    meals = []
    for row in rows:
        name = (row.get("productName") or "").strip()
        if not name:
            continue
        meals.append({
            "code": name,  # 营养表无独立编码，用名称作 key
            "name": name,
            "price": None,
            "kcal": _to_float(row.get("energyKcal")),
            "protein": _to_float(row.get("protein")),
            "fat": _to_float(row.get("fat")),
            "carb": _to_float(row.get("carbohydrate")),
            "sodium": _to_float(row.get("sodium")),
            "calcium": _to_float(row.get("calcium")),
            "category": guess_category(name),
        })
    return meals


_CATEGORY_RULES = [
    ("早餐", ("麦满分", "粥", "早餐")),
    ("甜品", ("新地", "冰淇淋", "麦旋风", "派", "奶冻", "蛋挞", "拉明顿")),
    ("饮品", ("可乐", "雪碧", "咖啡", "红茶", "牛奶", "果汁", "热朱古力", "纯悦", "柠檬", "苹果汁", "椰奶")),
    ("小食", ("薯条", "鸡翅", "鸡排", "玉米", "脆薯饼", "油条", "苹果片", "麦乐鸡")),
    ("主食", ("堡", "卷", "霸", "麦香", "猪柳", "鸡腿", "安格斯", "板烧", "吉士",
              "汉堡", "双层", "不素之霸", "鱼肉堡")),
]


def guess_category(name):
    """按餐品名推断分类（营养接口不带分类字段）。"""
    for category, keywords in _CATEGORY_RULES:
        if any(k in name for k in keywords):
            return category
    return "小食"


# ---------- 优惠券 ----------

_COUPON_ITEM = re.compile(
    r"-\s*优惠券标题[:：]\s*(?P<title>[^\n\\]+?)\s*\\?\s*\n"
    r"\s*状态[:：]\s*(?P<status>[^\n\\]+?)\s*\\?\s*\n"
)


def parse_coupon_markdown(text):
    """解析 available-coupons / query-my-coupons 的 markdown 券列表。

    真实响应形如::

        ### 麦麦省优惠券列表：
        - 优惠券标题：免费脆薯饼 \\
          状态：可领取 \\
          优惠券图片：\\
            <img src="..." alt="免费脆薯饼" ...>

    返回 list[dict]: title / status / couponId（真实接口不返回 ID，用标题占位）。
    """
    if not text:
        return []
    coupons = []
    for m in _COUPON_ITEM.finditer(text):
        title = m.group("title").strip().strip("*").strip()
        status = m.group("status").strip()
        if title:
            coupons.append({"title": title, "status": status,
                            "couponId": title, "discount": None})
    return coupons


# ---------- 营销活动日历 ----------

_SECTION = re.compile(r"^####\s*(?P<date>[^#\n]+?)\s*$", re.MULTILINE)
_ITEM_TITLE = re.compile(r"\*\*活动标题\*\*[:：]\s*(?P<title>[^\n]+)")
_ITEM_DESC = re.compile(r"\*\*活动内容介绍\*\*[:：]\s*(?P<desc>[^\n]+)")

_STATUS_MAP = {"今日": "进行中", "进行中": "进行中", "未来": "未开始",
               "即将开始": "未开始", "往期回顾": "已结束", "往期": "已结束"}


def parse_campaign_markdown(text):
    """解析 campaign-calendar 的 markdown 活动列表。

    真实响应结构::

        ### 当前时间：2026-10-24 18:08:51
        ### 活动列表：
        #### 2026年10月20日 往期回顾
        -   **活动标题**：麦当劳 X PEACEMINUSONE
            **活动内容介绍**：GD同款联名复古棒球帽...

    按日期段（#### 标题）切分，段内提取活动标题与内容介绍，
    段标题里的「今日/未来/往期回顾」映射为活动状态。
    """
    if not text:
        return []
    sections = list(_SECTION.finditer(text))
    campaigns = []
    for i, sec in enumerate(sections):
        seg = text[sec.end(): sections[i + 1].start() if i + 1 < len(sections) else len(text)]
        header = sec.group("date")
        status = "进行中"
        for key, mapped in _STATUS_MAP.items():
            if key in header:
                status = mapped
                break
        date = header.split()[0] if header.split() else header
        titles = _ITEM_TITLE.findall(seg)
        descs = _ITEM_DESC.findall(seg)
        for j, title in enumerate(titles):
            title = title.strip()
            if not title:
                continue
            campaigns.append({
                "name": title,
                "date": date,
                "status": status,
                "desc": (descs[j].strip() if j < len(descs) else "").split("\n")[0][:60],
            })
    return campaigns[:30]
