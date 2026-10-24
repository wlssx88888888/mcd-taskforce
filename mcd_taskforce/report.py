"""报告生成：终端简报 + 自包含 HTML 战报。"""

import html
import json


def render_terminal(report):
    """纯文本战报，demo 直接打印。"""
    lines = [
        "=" * 56,
        "  麦门特工队 McTaskForce 战报  [模式: {}]".format(
            "mock 演示" if report["mode"] == "mock" else "MCP 实弹"),
        "=" * 56,
        "",
        report["brief"],
        "",
        "-" * 56,
        "最终结论: {} 元拿下，预算 {} 元{}".format(
            report["saving"]["payable"], report["plan"]["budget"],
            "，达标" if report["saving"]["within_budget"] else "，超支需调整"),
    ]
    return "\n".join(lines)


def render_html(report, path):
    """生成自包含 HTML 战报（特工档案风），返回文件路径。"""
    mode_badge = ("MCP 实弹模式" if report["mode"] == "live" else "Mock 演示模式")
    rows = []
    for p in report["nutrition"]["picks"]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td class='num'>¥{}</td>"
            "<td class='num'>{}</td><td class='num'>{}g</td></tr>".format(
                html.escape(p["name"]), html.escape(p["category"]),
                p["price"], p["kcal"], p["protein"]))

    campaigns = "".join(
        "<li><b>{}</b> <span class='tag'>{}</span> {}</li>".format(
            html.escape(c["name"]), html.escape(c["status"]),
            html.escape(c.get("desc", "")))
        for c in report["radar"]["active"] + report["radar"]["upcoming"])

    coupon = report["saving"]["best_coupon"]
    coupon_html = ("<b>{}</b>".format(html.escape(coupon["title"]))
                   if coupon else "<i>无可用券</i>")

    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>麦门特工队战报</title>
<style>
body{{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f1e8;
color:#2b2b2b;margin:0;padding:32px}}
.card{{max-width:760px;margin:0 auto;background:#fff;border:3px solid #2b2b2b;
border-radius:16px;overflow:hidden;box-shadow:8px 8px 0 #2b2b2b}}
header{{background:#ffbc0d;padding:24px 32px;border-bottom:3px solid #2b2b2b}}
header h1{{margin:0;font-size:26px}}
header p{{margin:6px 0 0;font-weight:600}}
.badge{{display:inline-block;background:#2b2b2b;color:#ffbc0d;padding:2px 12px;
border-radius:999px;font-size:13px;margin-left:8px}}
section{{padding:20px 32px;border-bottom:2px dashed #d8cfb8}}
section:last-child{{border-bottom:none}}
h2{{font-size:17px;margin:0 0 12px;color:#8a5a00}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{padding:8px 10px;border-bottom:1px solid #eee;text-align:left}}
th{{background:#faf6ea}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.total{{font-size:22px;font-weight:800}}
.save{{color:#c8102e;font-weight:700}}
ul{{margin:0;padding-left:20px;font-size:14px}}
.tag{{background:#e8f5e9;color:#1b5e20;font-size:12px;padding:1px 8px;border-radius:4px}}
footer{{padding:14px 32px;background:#faf6ea;font-size:12px;color:#777}}
</style></head><body>
<div class="card">
<header><h1>麦门特工队 · 作战战报<span class="badge">{mode}</span></h1>
<p>任务：{mission}</p></header>

<section><h2>🥗 营养师配餐</h2>
<table><tr><th>餐品</th><th>类别</th><th>单价</th><th>热量</th><th>蛋白</th></tr>
{rows}</table>
<p>合计热量 <b>{kcal}</b> 千卡 · 蛋白质 <b>{protein}</b> g</p></section>

<section><h2>💰 省钱特工战报</h2>
<p>配餐原价 ¥{subtotal} → 优惠券 {coupon} → <span class="save">立省 ¥{saving}</span></p>
<p class="total">实付：¥{payable} / 预算 ¥{budget}</p></section>

<section><h2>📡 雷达员情报</h2><ul>{campaigns}</ul></section>

<section><h2>🧾 下单员预览</h2>
<p>门店：{store}</p>
<p>状态：{status}</p></section>

<footer>由麦门特工队 McTaskForce 生成 · 1024 麦当劳程序员创意开发大赛参赛作品 ·
本报告仅供参考，餐品信息以麦当劳官方实时结果为准</footer>
</div></body></html>""".format(
        mode=mode_badge,
        mission=html.escape(report["mission"]),
        rows="\n".join(rows),
        kcal=report["nutrition"]["total_kcal"],
        protein=report["nutrition"]["total_protein"],
        subtotal=report["saving"]["subtotal"],
        coupon=coupon_html,
        saving=report["saving"]["saving"],
        payable=report["saving"]["payable"],
        budget=report["plan"]["budget"],
        campaigns=campaigns or "<li>暂无活动情报</li>",
        store=html.escape(report["order"]["store"]["name"]),
        status="已提交真实订单" if report["order"]["status"] == "submitted" else "预览（未下单）",
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def to_json(report):
    """报告 dict 的安全 JSON 序列化（供 API/测试用）。"""
    return json.dumps(report, ensure_ascii=False, indent=2)
