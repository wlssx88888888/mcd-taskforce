#!/usr/bin/env python3
"""麦门特工队 demo 入口。

用法:
    python demo.py "加班餐，30块以内，多来点蛋白"   # mock 模式（无需 Token）
    MCD_MCP_TOKEN=<token> python demo.py "..."      # 实弹模式
    python demo.py --html                           # 同时生成 HTML 战报
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcd_taskforce import TaskForce
from mcd_taskforce.report import render_terminal, render_html


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_html = "--html" in sys.argv
    mission = " ".join(args) if args else "一人食，40块以内，营养均衡"

    tf = TaskForce()
    report = tf.run(mission)
    print()
    print(render_terminal(report))

    if want_html:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "report.html")
        render_html(report, out)
        print("\nHTML 战报已生成: {}".format(out))


if __name__ == "__main__":
    main()
