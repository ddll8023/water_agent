# Agent 架构设计文档（多 Agent 重构版）

> 本文档描述系统多 Agent 智能分析引擎的架构设计与重构方案。
> 对应需求文档中的 M6 模块。
> 两 Agent + 工具函数架构：Collector + Analyst + `llm_suggestion`，通过共享数据库状态隐式协作。

---

## 1. 总体架构

系统拆分为两个 Agent 和一个工具函数，各自独立运行，通过数据库表状态协作：

| 组件 | 触发 | 是否调 LLM | 职责 |
|---|---|---|---|
| Collector Agent | 每 10 分钟（APScheduler） | 否 | 采集、入库、规则判定、创建规则预警 |
| Analyst Agent | 每 6 小时（APScheduler） | **是** | 趋势特征计算、LLM 分析、创建 AI 预警 |
| `llm_suggestion()` | 预警创建后 `asyncio.create_task` | **是** | Neo4j 溯源、RAG 检索、生成处置建议 |

**交互方式（数据驱动）：**

- Collector 和 Analyst 之间**不直接调用**——Analyst 每 6h 自己读数据库，不需要 Collector 通知
- 处置建议的触发：Collector/Analyst 创建预警后，直接 `asyncio.create_task(llm_suggestion(alert_id))` 异步执行
- 所有组件共享 `monitoring_record`、`alert_event`、`patrol_analysis` 等数据库表

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌───────────────────┐       ┌───────────────────┐             │
│  │  Collector Agent  │ 写    │  monitoring_record │←──┐        │
│  │  (10min 周期)     │──────→│  alert_event(s=0)  │   │        │
│  │  4 节点 LangGraph │──┐    │  patrol_log        │   │        │
│  │  不调 LLM         │  │    └───────────────────┘   │        │
│  └───────┬───────────┘  │                          │        │
│          │               │  写  ┌─────────────────┐  │  读    │
│          │               └────→│ alert_event(s=1) │←─┘        │
│          │                      │ patrol_analysis  │           │
│          │                      └────────┬────────┘           │
│          │                               │                     │
│          │           ┌───────────────────┐│                    │
│          │           │  llm_suggestion() ││                    │
│          └──────────→│  (工具函数)       ││                    │
│                      │  Neo4j+RAG+LLM   ││                    │
│                      │  写 suggestion    ││                    │
│                      └───────────────────┘│                    │
│                                            │                    │
│  两条链路 + 一个工具函数，共享数据库不共享进程内状态           │
│  触发方式：APScheduler（Collector/Analyst）+ create_task      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1.1 设计原则

| 原则 | 说明 |
|---|---|
| Agent 自治 | 每个 Agent 独立运行，无主从关系，不互相阻塞 |
| 数据驱动 | Agent 之间不直接调用，通过数据库表状态隐式协作 |
| 事务优先 | 数据库事务提交成功后，才能执行 Redis 缓存、WebSocket 广播、建议任务投递 |
| 失败隔离 | LLM、Neo4j、RAG 失败不影响 Collector 的 10 分钟采集任务 |
| source 隔离 | 规则预警 `source=0`，AI 趋势预警 `source=1`，默认不合并 |
| 先算后问 | 趋势特征由代码确定性计算，LLM 负责解释和生成结构化结论 |
| 可重试 | AI 建议生成应具备幂等与重试能力 |
| 可观测 | 每个 Agent 都记录日志、状态、耗时和失败原因 |

---

## 2. Agent 1：Collector Agent（采集与规则链路）

### 2.1 职责

Collector Agent 是纯实时数据管道，使用 LangGraph 构建 4 节点工作流，不调用 LLM。

负责：
- 从真实 API 或模拟数据源获取监测数据
- 按 `station_code` 匹配站点
- 写入 `monitoring_record`
- 按规则表执行阈值判断
- 创建或合并规则预警（`source=0`）
- 写 Redis 监测缓存
- 写巡检日志
- 在事务提交成功后，异步触发 `llm_suggestion(alert_id)` 生成处置建议

不负责：
- LLM 趋势分析
- Neo4j 溯源
- RAG 检索
- AI 处警建议的生成过程（只负责触发）

### 2.2 工作流（LangGraph）

```
         ┌─────────────────┐
         │ fetch_data       │  获取监测数据（API / mock）
         └────────┬────────┘
                  │
              条件路由（失败/无数据 → 跳过）
                  │
                  ▼
         ┌─────────────────┐
         │ process_save     │  入库监测记录，输出 pending_alerts
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ rule_alert       │  规则阈值判断，创建/合并 source=0 预警
         │                  │  → commit
         │                  │  → 广播 WebSocket / 写 Redis
         │                  │  → asyncio.create_task(llm_suggestion(alert_id))
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ cache_log        │  写 Redis 监测缓存 + 巡检日志
         └─────────────────┘
```

### 2.3 规则预警判断

规则判断必须严格按 `compare_direction` 执行。

推荐逻辑：

```python
if rule.compare_direction == "gt":
    limit = indicator.standard_limit_xxx_upper
    triggered = current_value > limit
elif rule.compare_direction == "lt":
    limit = indicator.standard_limit_xxx_lower
    triggered = current_value < limit
elif rule.compare_direction == "gte":
    limit = indicator.standard_limit_xxx_upper
    triggered = current_value >= limit
elif rule.compare_direction == "lte":
    limit = indicator.standard_limit_xxx_lower
    triggered = current_value <= limit
else:
    triggered = False
```

禁止写成：

```python
if current_value > limit:
    trigger
elif current_value < limit:
    trigger
```

否则只要当前值不等于限值，几乎都会误触发。

### 2.4 规则预警合并策略

默认策略：规则预警和 AI 趋势预警隔离。

规则预警只查询并合并：

```text
reservoir_id = 当前水库
source = 0
status < 3
```

AI 趋势预警只查询并去重：

```text
reservoir_id = 当前水库
source = 1
status < 3
同指标或同异常模式
```

如果后续产品要求规则预警和 AI 预警合并，需要额外设计：

- `source_list`
- `triggered_by`
- `indicator.trigger_source`
- `alert_reason`
- 前端展示规则

在当前重构阶段，不建议混合合并。

---

## 3. Agent 2：Analyst Agent（趋势分析链路）

### 3.1 职责

Analyst Agent 是系统的 AI 分析引擎，使用 LangGraph 构建 5 节点工作流。

独立运行，每 6 小时触发一次，对**全部水库**进行趋势分析和 AI 预警生成。

负责：
- 查询所有水库最近 6 小时监测数据和预警事件
- 查询上一次分析摘要
- 计算确定性趋势特征（delta、slope、连续升降等）
- 结合 RAG 构造 Prompt
- 调用 LLM 生成趋势分析（结构化 JSON 输出）
- 创建 AI 趋势预警（`source=1`）
- 写入 `patrol_analysis`
- 创建预警后异步触发 `llm_suggestion(alert_id)` 生成处置建议

### 3.2 工作流（LangGraph）

```
         ┌────────────────────────┐
         │ fetch_recent_data      │  查询所有水库 6h 数据 + 预警
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │ compute_features       │  计算确定性趋势特征（代码）
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │ ai_trend_analysis      │  LLM 趋势分析 ← 核心 Agent 节点
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │ process_alerts         │  创建 source=1 预警
         │                        │  → commit
         │                        │  → 广播 WebSocket / 写 Redis
         │                        │  → asyncio.create_task(llm_suggestion(alert_id))
         └───────────┬────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │ write_summary          │  写入 patrol_analysis
         └────────────────────────┘
```

### 3.3 fetch_recent_data

查询范围：

```text
alert_event:
  detected_at >= now - 6h

monitoring_record:
  record_time >= now - 6h

patrol_analysis:
  最近一次分析记录
```

输出：

```python
{
    "period_start": now - 6h,
    "period_end": now,
    "recent_alerts": list[AlertEvent],
    "monitoring_records": list[MonitoringRecord],
    "last_analysis": PatrolAnalysis | None,
}
```

### 3.4 compute_features

不要只给 LLM `avg/max/min`。

每个 `reservoir_id + indicator_id` 至少计算：

```python
{
    "count": 记录数,
    "first_value": 期初值,
    "last_value": 期末值,
    "min": 最小值,
    "max": 最大值,
    "avg": 平均值,
    "stddev": 标准差,
    "delta": 期末值 - 期初值,
    "delta_percent": 变化百分比,
    "slope": 趋势斜率,
    "missing_rate": 缺失率,
    "exceed_count": 超标次数,
    "consecutive_rise_count": 连续上升次数,
    "consecutive_fall_count": 连续下降次数,
    "station_coverage": 站点覆盖情况,
}
```

原则：

```text
代码负责计算事实。
LLM 负责解释事实。
```

### 3.5 ai_trend_analysis

输入：

- 最近 6 小时趋势特征
- 最近 6 小时已有预警
- 上一次分析摘要
- RAG 检索结果
- 水库基础信息
- 指标阈值与单位

输出必须是结构化 JSON（按水库组织）：

```json
{
  "reservoir_analyses": [
    {
      "reservoir_id": 1,
      "reservoir_name": "碧源水库",
      "summary": "碧源水库近期水质整体呈轻度恶化趋势...",
      "supplementary_alerts": [
        {
          "title": "碧源水库溶解氧持续下降趋势预警",
          "alert_level": 2,
          "indicators": [
            {
              "indicator_id": 1,
              "name": "溶解氧",
              "value": 4.2,
              "limit": 5.0,
              "unit": "mg/L",
              "feature_reason": "连续下降，6小时跌幅28%"
            }
          ],
          "reason": "溶解氧从6.5mg/L持续降至4.2mg/L...",
          "evidence_features": ["delta_percent=-28%", "consecutive_fall_count=5"]
        }
      ]
    }
  ],
  "concerns": ["需要关注的事项"],
  "trend_changed": true
}
```

### 3.6 process_alerts

对 LLM 输出的 `supplementary_alerts` 逐条处理。

跳过条件：

```text
已存在同水库、同指标、source=1、status<3 的 AI 趋势预警
```

创建流程：

```text
1. 创建 alert_event，source=1
2. commit
3. commit 成功后写 Redis 最近预警缓存
4. commit 成功后 WebSocket 广播
5. commit 成功后 asyncio.create_task(llm_suggestion(alert_id))
```

### 3.7 write_summary

为每个水库写入 1 条 `patrol_analysis` 记录，字段范围：

```
id
reservoir_id
period_start
period_end
summary
supplementary_alert_ids
analyzed_at
created_at
```

---

## 4. `llm_suggestion` 工具函数

### 4.1 定位

`services.alerts.llm_suggestion()` 是核心工具函数，不自成 Agent，不自成工作流。

职责：
1. 读取 AlertEvent
2. 读取 Reservoir
3. Neo4j 污染溯源
4. RAG 检索
5. 构造 Prompt
6. 调用 LLM
7. 写入 alert_event.suggestion
8. 更新 suggestion_status

### 4.2 签名

```python
# 自建 DB/Neo4j session，无需外部传入
async def llm_suggestion(alert_id: int):
    async with get_background_db_session() as db:
        async with neo4j_driver.session() as session:
            # 核心逻辑
```

### 4.3 调用方式

Collector 和 Analyst 在创建预警并提交事务后，直接：

```python
asyncio.create_task(llm_suggestion(alert_id))
```

幂等保护：`llm_suggestion` 内部检查 `suggestion_status == 1` 时直接跳过，避免重复执行。

### 4.4 失败处理

- 异常时记录日志，将 `suggestion_status` 恢复为 0
- 不影响调用方（Collector/Analyst）

---

## 5. 两条链路对比

| 项目 | Collector Agent | Analyst Agent | `llm_suggestion()` |
|---|---|---|---|
| 触发 | 10 分钟周期 | 6 小时周期 | 预警创建后异步 |
| 是否调 LLM | 否 | **是**（趋势解释） | **是**（溯源+建议） |
| 检测方式 | 代码规则判断 | 特征 + LLM 分析 | Neo4j + RAG + LLM |
| 响应速度 | 近实时 | 最长 6 小时 | 异步秒级 |
| 产出 | `source=0` 预警 | `source=1` 预警 + 摘要 | suggestion 字段 |
| 是否互相合并 | 默认不合并 | 默认不合并 | — |

---

## 6. 调度配置

### 6.1 main.py

```python
scheduler.add_job(
    run_collector_agent,
    "interval",
    minutes=10,
    id="collector_agent",
    replace_existing=True,
    max_instances=1,
    coalesce=True,
    misfire_grace_time=120,
)

scheduler.add_job(
    run_analyst_agent,
    "interval",
    hours=6,
    id="analyst_agent",
    replace_existing=True,
    max_instances=1,
    coalesce=True,
    misfire_grace_time=600,
)
```

### 6.2 并发保护

- Collector Agent 不重叠运行（`max_instances=1`）
- Analyst Agent 不重叠运行（`max_instances=1`）
- 同一 `alert_id` 不重复生成建议（`suggestion_status=1` 检查已有）
- Analyst 创建 AI 预警前执行幂等去重

---

## 7. 改造涉及文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `agent/collector.py` | **修改（原 patrol.py）** | 去掉 `llm_analyze` 节点，4 节点图 |
| `agent/analyst.py` | **新增** | 5 节点 LangGraph，分析 Agent |
| `agent/state.py` | **修改** | 保留 `PatrolState`，新增 `AnalystState`；去掉 `EmergencyState` |
| `agent/suggestion_worker.py` | **删除** | 不再需要 |
| `services/alerts.py` | **修改** | `llm_suggestion` 改为自建 session |
| `models/patrol_analysis.py` | **小改** | 新增 `supplementary_alert_ids` 字段 |
| `main.py` | **修改** | 导入新入口，新增 Analyst 调度 |
| `prompt/alert.yaml` | **修改** | ANALYSIS 模板适配完整特征输入 |

---

## 8. 原则上不变的部分

| 模块 | 说明 |
|---|---|
| `routers/` | API 路径保持不变 |
| `frontend/` | 前端适配（如有需要） |
| `services/alert_rules.py` | 规则引擎不动 |
| `services/monitoring.py` | 采集逻辑不动 |
| `models/alert.py` | 已有 `source`、`suggestion_status`、`indicators` 字段 |
| `models/monitoring.py` | 监测记录模型不变 |

---

## 9. 验收标准

### 9.1 Collector Agent

- `agent/collector.py` 不导入 LangChain、Prompt、RAG、Neo4j 或 LLM
- 不直接持有 `db` 或 `neo4j_driver` 参数
- 规则预警创建成功后，先 commit，再执行副作用
- 10 分钟任务 `max_instances=1`

### 9.2 规则判断

必须覆盖测试：

```text
compare_direction=gt，current_value > upper_limit，触发
compare_direction=gt，current_value <= upper_limit，不触发
compare_direction=lt，current_value < lower_limit，触发
compare_direction=lt，current_value >= lower_limit，不触发
```

### 9.3 source 策略

- 规则预警创建 `source=0`
- AI 趋势预警创建 `source=1`
- 默认规则预警只合并 `source=0` 的未关闭预警
- 默认 AI 趋势预警只去重 `source=1` 的未关闭预警

### 9.4 Analyst Agent

- 6 小时任务 `max_instances=1`
- LLM 输入包含完整确定性趋势特征
- LLM 输出经过 JSON 校验
- 创建 AI 预警前执行幂等去重

### 9.5 `llm_suggestion` 工具函数

- 独立创建自己的 DB/Neo4j session
- 失败时记录日志，恢复 `suggestion_status=0`
- 同一 `alert_id` 不重复并发生成建议
