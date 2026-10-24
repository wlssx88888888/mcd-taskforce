# MCP_INTEGRATION.md — 麦当劳 MCP 集成说明

> 本文件说明「麦门特工队 McTaskForce」实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值。

## 1. MCP Server

| 项 | 值 |
|---|---|
| Server | 麦当劳中国 MCP Server |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 认证方式 | 请求头 `Authorization: Bearer <MCD_MCP_TOKEN>` |
| Token 申请 | [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 手机号登录 → 控制台 → 激活 |
| 参考文档 | [mcd-mcp-server 使用指南](https://github.com/M-China/mcd-mcp-server) |

客户端配置（环境变量占位，不包含真实凭证）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer <MCD_MCP_TOKEN>"
      }
    }
  }
}
```

## 2. 使用的 Tool 及用途

McTaskForce 客户端通过 `tools/list` 实测发现麦当劳 MCP 当前提供 **35 个 Tool**，本流水线直接调用其中 6 个核心工具，其余工具客户端通用支持（`call_tool()` 任意调用）。

### 流水线直接调用（6 个）

| Tool | 使用者 | 用途 | 调用时机 |
|---|---|---|---|
| `list-nutrition-foods` | 🥗 营养师 | 获取 160 个餐品的营养成分（能量/蛋白/脂肪/碳水/钠/钙） | 每次配餐 |
| `available-coupons` | 💰 省钱特工 | 查询当前可领取的麦麦省优惠券 | 每次凑券 |
| `calculate-price` | 💰 省钱特工 | 按选购清单+优惠券计算应付金额 | 交叉验证估算 |
| `campaign-calendar` | 📡 雷达员 | 查询当月营销活动日历（往期/今日/未来） | 每次任务 |
| `now-time-info` | 📡 雷达员 | 获取当前时间，校准活动时效判断 | 每次任务 |
| `create-order` | 🧾 下单员 | 创建订单（**仅显式 confirm=True 时调用**） | 用户确认后 |

### 规划中的扩展调用（客户端已支持）

| Tool | 计划用途 |
|---|---|
| `query-nearby-stores` | 定位附近门店，把"时价"变成实价 |
| `query-meals` / `query-meal-detail` | 门店在售餐品与实时价格 |
| `query-store-coupons` / `query-my-coupons` / `auto-bind-coupons` | 门店券/我的卡包/一键领券 |
| `query-my-account` | 积分余额，联动积分商城兑换 |
| `mall-points-products` / `mall-create-order` | 积分兑换商品与下单 |
| `order-list` / `query-order` / `cancel-order` | 历史订单查询/详情/取消 |
| `delivery-query-addresses` / `delivery-create-address` / `delivery-query-stores` | 麦乐送外送链路 |
| `query-promotions` / `query-party-*` / `draw-lottery` / `query-lottery-info` | 团餐促销/派对预订/积分抽奖 |

### 真实响应格式适配（`live_data.py` 的职责）

麦当劳 MCP 的返回不是规整 JSON，本项目的解析层处理了三类真实格式：

| 格式 | 样例 | 解析器 |
|---|---|---|
| Markdown 说明书 + `## Original Response` JSON | 大多数工具 | `extract_original_json()` |
| 独有 `[N]{col1,col2}:` 表格 | `list-nutrition-foods` 的 160 餐品营养表 | `parse_mcd_table()` |
| Markdown 列表（券/活动） | `available-coupons`、`campaign-calendar` | `parse_coupon_markdown()` / `parse_campaign_markdown()` |

## 3. 调用流程

一次"加班餐，多来点蛋白"任务的完整 MCP 交互时序（实弹模式实测，2026-10-24）：

```
用户
 │ 自然语言需求
 ▼
🎖️ 队长 Captain（纯本地规则引擎，无 MCP 调用）
 │ 任务单 {budget: 50, scene: 加班充饥, goal: [高蛋白]}
 ▼
🥗 营养师 Nutritionist
 │─ MCP: list-nutrition-foods ──────────► 160 个餐品真实营养表
 │  本地：protein/price 性价比贪心选餐（无价格时退化为纯营养策略+组合规模限制）
 ▼  配餐清单（芝士双层安格斯厚牛堡 58g 蛋白 + 冰牛奶大杯 15g + 抹茶牛奶 14g + 中薯条）
💰 省钱特工 Saver
 │─ MCP: available-coupons ─────────────► 可领券列表（免费脆薯饼/11.9元麦辣鸡腿堡/19.9元王牌炸鸡任选2）
 │  本地：券情报输出；有价格时 estimate + calculate-price 交叉验证
 ▼  省钱结论
📡 雷达员 Radar
 │─ MCP: now-time-info ─────────────────► 服务器当前时间
 │─ MCP: campaign-calendar ─────────────► 28 个真实活动（今日/往期分段）
 ▼  薅羊毛情报（G-DRAGON 联名/麦金学期卡/蓝莓爆爆珠麦旋风……）
🧾 下单员 Orderer
 │  本地：生成订单预览（不调 create-order，confirm=False 默认）
 ▼  预览单（状态：未下单）
📋 输出：终端简报 + HTML 战报
```

限流说明：麦当劳 MCP 每 Token 每分钟上限 600 次请求；本流水线单次任务约 4-6 次调用，远低于限制。

## 4. 业务价值

1. **多目标决策自动化**：营养×预算×优惠×时机四个目标互相牵制，人工凑单要在 4 个 App 间来回切；特工队一次交互全解决。
2. **账目可信**：省钱特工的券后价不是拍脑袋，而是用 `calculate-price` 真实工具验证过的——"两条独立链路算出同一个数"才算数。
3. **可扩展的特工编制**：新增场景（团餐、健身餐、积分兑换）只需注册新特工，不动流水线。
4. **负责任的 AI**：涉及真实资金的下单操作默认只预览，把确认权留给用户。

## 5. Mock 与实弹双模式

| 模式 | 触发条件 | 数据来源 |
|---|---|---|
| 实弹 | 环境变量 `MCD_MCP_TOKEN` 存在且 initialize 成功 | 麦当劳 MCP Server 实时数据（35 个工具） |
| Mock | 无 Token 或网络不可达 | `mcd_taskforce/mock_data.py` 内置对齐 MCP 返回结构的数据 |

Mock 数据的字段结构与真实 Tool 返回对齐（`foods`/`coupons`/`campaigns` 等键名一致），两种模式间切换无需改业务代码。

真实响应的脱敏存档（不含 Token）收录在 `tests/fixtures/`，单测直接拿真实响应验证解析器——**解析器不是对着想象写的，是对着真子弹写的**。

## 6. 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0.0 | 2026-10-24 | 初版：5 特工流水线 + mock/实弹双模式，报名参赛 |
| v1.1.0 | 2026-10-24 | 实弹升级：新增 `live_data.py` 真实响应解析层（营养表 160 餐品/真实券/28 活动），修复 JSON-RPC 通知空响应导致误降级 mock 的协议 bug，单测 7 → 12 |
