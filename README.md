# 🍔 麦门特工队 McTaskForce

> 一支 AI 特工队，帮你吃得明白、省得彻底。

**1024 程序员节 · 麦当劳程序员创意开发大赛**参赛作品 · 基于 [麦当劳中国 MCP](https://github.com/M-China/mcd-mcp-server) 开发 · 使用 [WorkBuddy](https://www.workbuddy.cn) 完成开发

[![License: MIT](https://img.shields.io/badge/License-MIT-ffbc0d.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![麦当劳 MCP](https://img.shields.io/badge/MCP-McDonald's%20China-c8102e.svg)](https://open.mcd.cn/mcp)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)](#-开发与测试)

---

## 这是什么？

市面上的麦当劳 Skill 都是"一个助手答你所有问题"。**麦门特工队换了个打法：把点餐拆成一条特工流水线，五个 AI 各司其职。**

你只说一句话——"加班餐，30 块以内，多来点蛋白"——特工队内部就是这么跑的：

```
你的需求
   │
   ▼
┌─────────────┐
│  🎖️ 队长     │  拆解任务单：预算 30 元 / 场景 加班充饥 / 目标 高蛋白
│  Captain    │
└──────┬──────┘
       ▼
┌─────────────┐
│  🥗 营养师   │  拉取餐品营养数据，按"蛋白/元"性价比在预算内选餐
│ Nutritionist│  → 猪柳蛋麦满分 13元(19g蛋白) + 中杯拿铁 15元(10g蛋白)
└──────┬──────┘
       ▼
┌─────────────┐
│  💰 省钱特工 │  查询可用优惠券，估算最优券
│  Saver      │  → "饮品第二杯半价" 立省 7 元，实付 21 元
└──────┬──────┘
       ▼
┌─────────────┐
│  📡 雷达员   │  盯活动日历：周三会员日、55周年、万圣节预告
│  Radar      │
└──────┬──────┘
       ▼
┌─────────────┐
│  🧾 下单员   │  生成订单预览 —— 默认绝不下单，等你点头
│  Orderer    │
└──────┬──────┘
       ▼
   📋 作战战报（终端 + HTML）
```

**为什么是特工队而不是一个助手？** 因为真实世界的一顿饭本来就是多目标决策：营养、预算、优惠、时机互相牵制。拆成角色后，每个 agent 的策略可以独立优化、独立测试，也天然可扩展——想加"团餐策划"特工？继承基类写个 `run()` 就行。

## ✨ 特性

- **🧠 任务拆解**：自然语言 → 结构化任务单（预算/场景/营养目标），正则规则引擎，零 LLM 依赖也能跑
- **🥗 营养配餐**：直吃麦当劳 MCP `list-nutrition-foods` 真实营养表（160 个餐品的热量/蛋白/脂肪/钠/钙），预算感知的性价比贪心选餐，不超支、不糊弄
- **💰 凑券最优**：`available-coupons` 真实可领券情报 + `calculate-price` 实算交叉验证——嘴上说省，账上真省
- **📡 活动雷达**：`campaign-calendar` + `now-time-info`，28 个真实活动实时薅羊毛情报
- **🛡️ 安全下单**：下单员默认只出预览，真实 `create-order` 必须显式 `confirm=True`，决定权永远在人
- **🔌 双模式**：有 `MCD_MCP_TOKEN` 走实弹（35 个工具全量可用）；没有也能一键 mock demo，clone 下来 30 秒看到效果
- **🧪 可测**：12 个单元测试覆盖预算解析、场景识别、流水线、报告生成，以及 5 个基于真实响应存档的解析器测试

## 🚀 快速开始

### 前置条件

- Python 3.8+（零第三方依赖，纯标准库实现 MCP 客户端）
- （可选，实弹模式）麦当劳 MCP Token：到 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 用手机号登录，控制台点「激活」领取

### Mock 模式（无需 Token）

```bash
git clone https://github.com/wlssx88888888/mcd-taskforce.git
cd mcd-taskforce
python demo.py "加班餐，30块以内，多来点蛋白"
```

### 实弹模式（真实麦当劳 MCP）

```bash
export MCD_MCP_TOKEN=<你的MCP Token>    # Windows PowerShell: $env:MCD_MCP_TOKEN="..."
python demo.py "一人食，40块以内，营养均衡"
```

### 生成 HTML 战报

```bash
python demo.py --html "周末聚餐，100块，多来点蛋白"
# 生成 report.html，浏览器打开即看
```

### 作为库调用

```python
from mcd_taskforce import TaskForce

tf = TaskForce()                      # 自动检测 MCD_MCP_TOKEN，无则 mock
report = tf.run("加班餐，30块以内，多来点蛋白")

print(report["saving"]["payable"])    # 实付金额
print(report["nutrition"]["picks"])   # 配餐清单
print(report["radar"]["active"])      # 进行中活动
print(report["brief"])                # 完整文字战报
```

## 🎬 Demo 实拍

### 实弹模式（真实麦当劳 MCP，2026-10-24 实测）

```
$ export MCD_MCP_TOKEN=<你的MCP Token>
$ python demo.py "加班餐，多来点蛋白"

【队长简报】
  原始需求: 加班餐，多来点蛋白
  预算上限: 50.0 元
  场景判断: 加班充饥
  营养目标: 高蛋白

【营养师配餐】（数据来自 MCP list-nutrition-foods 真实营养表，160 个餐品）
  芝士双层安格斯厚牛堡 (主食) 时价 1003.0千卡 蛋白58.0g
  冰牛奶大杯 (饮品) 时价 269.0千卡 蛋白15.0g
  热浓浓抹茶牛奶大杯 (饮品) 时价 333.0千卡 蛋白14.0g
  中薯条 (小食) 时价 289.0千卡 蛋白4.0g
  小计: 以门店实价为准 | 热量 1894.0 千卡 | 蛋白 91.0 g
  点评: 蛋白质合计 91.0 g，训练后补给充足。

【省钱特工战报】（数据来自 MCP available-coupons 真实可领券）
  配餐价格以门店实价为准，先看券情报
  可领券情报: 免费脆薯饼, 11.9元麦辣鸡腿堡, 19.9元王牌炸鸡任选2

【雷达员情报】（数据来自 MCP campaign-calendar 真实活动日历）
  当前时间: 2026-10-24T18:12:18.411
  [进行中] 麦当劳「我就喜欢」限定丝巾正式开售🔥 (2026年10月24日)
  [进行中] 韩式风味蘸酱上新❤️就「酱」心有所「薯」 (2026年10月24日)
  [进行中] 参与麦金喜抽奖，🉐[积分霸王餐] (2026年10月24日)
  ……等 24 个进行中活动

【下单员预览】
  门店: 麦当劳(科技园餐厅)（默认门店，真实门店需 query-nearby-stores 定位）
  应付: 以门店实价为准
  状态: 预览（未下单）
```

### Mock 模式（无需 Token，clone 即跑）

```
$ python demo.py "加班餐，30块以内，多来点蛋白"

【营养师配餐】
  猪柳蛋麦满分 (早餐) 13.0元 400千卡 蛋白19g
  中杯拿铁 (饮品) 15.0元 180千卡 蛋白10g
  小计: 28.0 元 | 热量 580 千卡 | 蛋白 29 g

【省钱特工战报】
  选用优惠券: 饮品第二杯半价 (CP-1003)
  立省: 7.0 元 → 实付 21.0 元
--------------------------------------------------------
最终结论: 21.0 元拿下，预算 30.0 元，达标
```

> 📋 [查看 HTML 战报示例（真实模式生成，浏览器直接打开）](docs/report-sample.html)

## 🔧 架构

```
mcd-taskforce/
├── demo.py                      # 一键演示入口
├── mcd_taskforce/
│   ├── mcp_client.py            # 麦当劳 MCP Streamable HTTP 客户端（纯标准库）
│   ├── live_data.py             # 真实 MCP 响应解析层（markdown/表格格式 → 结构化数据）
│   ├── mock_data.py             # mock 数据层，无 Token 也能跑全流程
│   ├── orchestrator.py          # TaskForce 编排器：特工流水线
│   ├── report.py                # 终端简报 + 自包含 HTML 战报
│   └── agents/
│       ├── captain.py           # 队长：需求拆解
│       ├── nutritionist.py      # 营养师：配餐
│       ├── saver.py             # 省钱特工：凑券算价
│       ├── radar.py             # 雷达员：活动监控
│       └── orderer.py           # 下单员：订单预览（默认不执行）
└── tests/
    ├── test_orchestrator.py     # 12 个单元测试
    └── fixtures/                # 真实 MCP 响应存档（脱敏，不含 Token）
        ├── nutrition.json       #   list-nutrition-foods 真实响应
        ├── coupons.json         #   available-coupons 真实响应
        └── calendar.json        #   campaign-calendar 真实响应
```

麦当劳 MCP 的工具返回不是规整 JSON，而是「Markdown 说明书 + Original Response」的混合体，营养表更是独有的 `[N]{col1,col2}:` 表格格式。`live_data.py` 就是为消化这些真实格式而生——这也是本项目区别于"玩具 demo"的工程细节。

每个 agent 都是无状态、可独立测试的单元：

```python
class Agent:
    def run(self, plan, client=None, use_mock=False, **kwargs):
        """输入任务单 + MCP 客户端，输出结构化结果。"""
```

MCP 客户端实现了完整的 Streamable HTTP 协议（initialize → tools/list → tools/call），兼容纯 JSON 和 SSE 两种响应格式，正确区分 JSON-RPC 通知（无 id，空响应体合法），见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md)。

## 🧪 开发与测试

```bash
python -m unittest discover -s tests -v
# test_budget_extract ... ok
# test_scene_and_goal ... ok
# test_nutrition_parser_on_real_response ... ok
# test_coupon_parser_on_real_response ... ok
# test_campaign_parser_on_real_response ... ok
# test_full_run_within_budget ... ok
# test_html_report ... ok
# ...
# Ran 12 tests — OK
```

## 🔐 安全设计

1. **Token 只走环境变量**：代码与仓库中不含任何真实 Token/密钥（详见 [CONTEST_DECLARATION.md](CONTEST_DECLARATION.md) 信息安全声明）
2. **下单双确认**：`create-order` 是副作用操作，必须显式传 `confirm=True`，默认只生成预览
3. **输出仅供参考**：项目不构成营养/医疗建议，餐品信息以麦当劳官方实时结果为准

## 🏆 参赛信息

- **赛事**：1024 程序员节 · 麦当劳程序员创意开发大赛
- **作品类型**：基于麦当劳 MCP 的创意 Skill
- **开发工具**：WorkBuddy（官方合作伙伴，完整开发对话见 [workbuddy.md](workbuddy.md)）
- **排名依据**：GitHub 公开 Star 数（活动前已获得的 Star 亦计入）

> 本项目为参赛者独立开发，非麦当劳官方产品。

## 📄 License

[MIT](LICENSE) © 2026 McTaskForce contributors
