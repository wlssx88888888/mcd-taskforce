"""队长 Captain —— 任务拆解专家。

把用户的一句话需求拆成结构化任务单：预算、场景、目标、约束。
规则引擎实现，零依赖；预留 LLM 增强接口。
"""

import re


class Captain:
    ROLE = "队长"
    MOTTO = "没有拆解不了的任务，只有看不透的需求。"

    def __init__(self):
        pass

    def run(self, mission, client=None, use_mock=False):
        """解析任务单。

        :param mission: 用户自然语言需求，如"加班餐，30块以内，多来点蛋白"
        :return: 结构化任务单 dict
        """
        plan = {
            "mission": mission,
            "budget": self._extract_budget(mission),
            "scene": self._extract_scene(mission),
            "goal": self._extract_goal(mission),
            "headcount": self._extract_headcount(mission),
            "notes": [],
        }
        if plan["budget"] is None:
            plan["budget"] = 50.0
            plan["notes"].append("未指定预算，默认按 50 元规划")
        if plan["scene"] == "unknown":
            plan["scene"] = "一人食"
            plan["notes"].append("未识别场景，按一人食处理")
        return plan

    @staticmethod
    def _extract_budget(text):
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:元|块|rmb|块钱)",
            r"预算\s*(\d+(?:\.\d+)?)",
            r"不超过\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*以内",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return float(m.group(1))
        return None

    @staticmethod
    def _extract_scene(text):
        scene_map = {
            "加班": "加班充饥", "熬夜": "加班充饥", "夜宵": "加班充饥",
            "早餐": "早餐", "早上": "早餐", "午饭": "正餐", "午餐": "正餐",
            "晚饭": "正餐", "晚餐": "正餐", "聚餐": "聚餐", "团建": "聚餐",
            "一人": "一人食", "独自": "一人食", "聚会": "聚餐",
        }
        for key, val in scene_map.items():
            if key in text:
                return val
        return "unknown"

    @staticmethod
    def _extract_goal(text):
        goals = []
        if any(k in text for k in ["减脂", "减肥", "低卡", "瘦"]):
            goals.append("低卡")
        if any(k in text for k in ["增肌", "蛋白", "健身", "肌肉"]):
            goals.append("高蛋白")
        if any(k in text for k in ["吃饱", "管饱", "顶饿", "抗饿"]):
            goals.append("高饱腹")
        if not goals:
            goals.append("均衡")
        return goals

    @staticmethod
    def _extract_headcount(text):
        m = re.search(r"(\d+)\s*(?:人|份|位)", text)
        if m:
            return int(m.group(1))
        return 1

    def brief(self, plan):
        """任务单简报，用于 demo 展示。"""
        lines = [
            "【队长简报】",
            "  原始需求: {}".format(plan["mission"]),
            "  预算上限: {} 元".format(plan["budget"]),
            "  场景判断: {}".format(plan["scene"]),
            "  营养目标: {}".format(" / ".join(plan["goal"])),
        ]
        if plan["notes"]:
            for n in plan["notes"]:
                lines.append("  备注: {}".format(n))
        return "\n".join(lines)
