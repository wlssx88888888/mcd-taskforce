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

| Tool | 使用者 | 用途 | 调用时机 |
|---|---|---|---|
| `list-nutrition-foods` | 🥗 营养师 | 获取餐品营养成分（能量/蛋白/脂肪/碳水/钠/钙） | 每次配餐 |
| `available-coupons` | 💰 省钱特工 | 查询当前可领取的麦麦省优惠券 | 每次凑券 |
| `query-store-coupons` | 💰 省钱特工 | 查询当前门店可用优惠券 | 凑券兜底 |
| `calculate-price` | 💰 省钱特工 | 按选购清单+优惠券计算应付金额 | 交叉验证估算 |
| `campaign-calendar` | 📡 雷达员 | 查询当月营销活动日历 | 每次任务 |
| `now-time-info` | 📡 雷达员 | 获取当前时间，校准活动时效判断 | 每次任务 |
| `query-meals` | 🥗 营养师 | 查询门店在售餐品列表（分类/编码/价格） | 实弹模式配餐 |
| `query-nearby-stores` | 🧾 下单员 | 查询附近门店，确定订单门店 | 下单预览 |
| `create-order` | 🧾 下单员 | 创建订单（**仅显式 confirm=True 时调用**） | 用户确认后 |

未使用但兼容的工具（客户端 `call_tool()` 通用支持）：`auto-bind-coupons`、`query-my-coupons`、`query-my-account`、`mall-points-products`、`draw-lottery`、`query-order`、`order-list`、`cancel-order`、`query-meal-detail` 等。

## 3. 调用流程

一次"加班餐，30 块以内，多来点蛋白"任务的完整 MCP 交互时序：

```
用户
 │ 自然语言需求
 ▼
🎖️ 队长 Captain（纯本地规则引擎，无 MCP 调用）
 │ 任务单 {budget: 30, scene: 加班充饥, goal: [高蛋白]}
 ▼
🥗 营养师 Nutritionist
 │─ MCP: list-nutrition-foods ──────────► 餐品营养全集
 │  本地：按 protein/price 性价比贪心选餐（预算感知）
 ▼  配餐清单（猪柳蛋麦满分 + 中杯拿铁，28 元 / 蛋白 29g）
💰 省钱特工 Saver
 │─ MCP: available-coupons ─────────────► 可领券列表
 │  本地：按门槛与折扣估算最优券（饮品第二杯半价）
 │─ MCP: calculate-price ───────────────► 验证：立省 7 元，实付 21 元
 ▼  省钱结论（与 MCP 账目交叉验证，非估算）
📡 雷达员 Radar
 │─ MCP: now-time-info ─────────────────► 当前时间
 │─ MCP: campaign-calendar ─────────────► 活动日历
 ▼  薅羊毛情报（周三会员日 / 55周年 / 万圣节预告）
🧾 下单员 Orderer
 │─ MCP: query-nearby-stores ───────────► 附近门店
 │  本地：生成订单预览（不调 create-order）
 ▼  预览单（应付 21 元，状态：未下单）
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
| 实弹 | 环境变量 `MCD_MCP_TOKEN` 存在且 initialize 成功 | 麦当劳 MCP Server 实时数据 |
| Mock | 无 Token 或网络不可达 | `mcd_taskforce/mock_data.py` 内置对齐 MCP 返回结构的数据 |

Mock 数据的字段结构与真实 Tool 返回对齐（`foods`/`coupons`/`campaigns` 等键名一致），两种模式间切换无需改业务代码。
