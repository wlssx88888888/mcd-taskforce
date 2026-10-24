"""编排逻辑单元测试（全程 mock 数据，无需 MCP Token）。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcd_taskforce import TaskForce


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
