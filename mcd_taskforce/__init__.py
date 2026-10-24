"""麦门特工队 McTaskForce - 多智能体协作的麦当劳 Skill。

一支 AI 特工队帮你吃得明白、省得彻底：
- 队长 Captain    : 拆解任务单
- 营养师 Nutritionist: 营养配餐
- 省钱特工 Saver  : 凑券算价最优解
- 雷达员 Radar    : 活动日历监控
- 下单员 Orderer  : 订单预览与执行(需显式确认)
"""

__version__ = "1.0.0"
__all__ = ["MCDMCPClient", "TaskForce"]

from .mcp_client import MCDMCPClient
from .orchestrator import TaskForce
