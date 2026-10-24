"""编排逻辑单元测试（全程 mock 数据，无需 MCP Token）。"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcd_taskforce import TaskForce
from mcd_taskforce import live_data

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


class TestCaptain(unittest.TestCase):
    def setUp(self):
        self.tf = TaskForce(use_mock=True, verbose=False)

    def test_budget_extract(self):
        for text, expected in [
            ("加班餐，30块以内", 30.0),
            ("预算不超过50元", 50.0),
            ("想吃点好的，40 块钱", 40.0),
            ("随便吃点", None),
        ]:
            self.assertEqual(self.tf.captain._extract_budget(text), expected, text)

    def test_budget_default(self):
        plan = self.tf.captain.run("随便吃点")
        self.assertEqual(plan["budget"], 50.0)
        self.assertTrue(plan["notes"])

    def test_scene_and_goal(self):
        plan = self.tf.captain.run("加班夜宵，减脂，多蛋白")
        self.assertEqual(plan["scene"], "加班充饥")
        self.assertIn("低卡", plan["goal"])
        self.assertIn("高蛋白", plan["goal"])


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tf = TaskForce(use_mock=True, verbose=False)

    def test_full_run_within_budget(self):
        report = self.tf.run("加班餐，30块以内，多来点蛋白")
        self.assertEqual(report["mode"], "mock")
        self.assertGreater(len(report["nutrition"]["picks"]), 0)
        self.assertLessEqual(report["saving"]["payable"], report["plan"]["budget"])
        self.assertEqual(report["order"]["status"], "preview")

    def test_order_needs_confirm(self):
        report = self.tf.run("一人食 40 元")
        self.assertEqual(report["order"]["status"], "preview")

    def test_html_report(self):
        from mcd_taskforce.report import render_html
        report = self.tf.run("一人食 40 元")
        out = os.path.join(os.path.dirname(__file__), "_tmp_report.html")
        render_html(report, out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("麦门特工队", content)
        os.remove(out)

    def test_tools_mock(self):
        tools = self.tf.tools()
        self.assertIn("calculate-price", tools)
        self.assertIn("campaign-calendar", tools)


class TestLiveDataParsers(unittest.TestCase):
    """真实 MCP 响应解析测试（fixtures 为真实响应的脱敏存档，不含 Token）。"""

    def test_extract_text_handles_rpc_envelope(self):
        resp = {"result": {"content": [{"type": "text", "text": "hello"}]}}
        self.assertEqual(live_data.extract_text(resp), "hello")

    def test_nutrition_parser_on_real_response(self):
        meals = live_data.nutrition_to_meals(_load_fixture("nutrition.json"))
        self.assertGreater(len(meals), 100)
        big_mac = next(m for m in meals if m["name"] == "巨无霸")
        self.assertEqual(big_mac["kcal"], 513.0)
        self.assertEqual(big_mac["protein"], 27.0)
        self.assertEqual(big_mac["category"], "主食")

    def test_mcd_table_parser(self):
        rows = live_data.parse_mcd_table(
            "[2]{a,b,c}:\n  x,1,2\n  y,3,4")
        self.assertEqual(rows, [{"a": "x", "b": "1", "c": "2"},
                                {"a": "y", "b": "3", "c": "4"}])

    def test_coupon_parser_on_real_response(self):
        coupons = live_data.parse_coupon_markdown(
            live_data.extract_text(_load_fixture("coupons.json")))
        self.assertGreaterEqual(len(coupons), 3)
        self.assertEqual(coupons[0]["title"], "免费脆薯饼")
        self.assertEqual(coupons[0]["status"], "可领取")

    def test_campaign_parser_on_real_response(self):
        campaigns = live_data.parse_campaign_markdown(
            live_data.extract_text(_load_fixture("calendar.json")))
        self.assertGreater(len(campaigns), 10)
        statuses = {c["status"] for c in campaigns}
        self.assertIn("进行中", statuses)
        self.assertIn("已结束", statuses)
        today = [c for c in campaigns if "10月24日" in c["date"]]
        self.assertTrue(today)


if __name__ == "__main__":
    unittest.main(verbosity=2)
