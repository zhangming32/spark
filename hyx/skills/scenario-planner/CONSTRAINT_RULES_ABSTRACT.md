# 测试用例生成约束规则（抽象规则版）

## 核心原则：基于组件角色，而非具体组件名

### 为什么需要抽象规则？

- 用户可能输入任意组件组合
- 规则不应写"HDFS/Spark"，否则无法识别"Kafka/Flink"
- 应基于组件角色（source/processor/sink）来判断数据流有效性

---

## 组件角色体系

### 角色定义

| 角色 | 功能 | 操作 | 典型组件类型 |
|------|------|------|--------------|
| **source** | 数据源，向下游提供数据 | read, consume, query | storage, streaming, database |
| **processor** | 数据处理器，转换/计算数据 | compute, transform, aggregate | compute, streaming |
| **sink** | 数据目标，接收上游数据输出 | write, produce, insert | storage, streaming, database |

### 角色识别规则

从组件知识卡片中获取：

```json
{
  "component_roles": {
    "supported_roles": ["source", "sink"],  // 组件可扮演的角色
    "cannot_act_as": ["processor"],          // 组件不能扮演的角色
    "reason": "存储组件无数据处理能力"        // 原因
  }
}
```

---

## 数据流有效性规则（抽象）

### 规则：基于角色判断数据流

| 数据流模式 | 角色序列 | 有效判断 | 说明 |
|------------|----------|----------|------|
| `A -> B -> A` | source -> processor -> sink | ✅ 有效 | source和sink可以是同一组件 |
| `A -> B -> C` | source -> processor -> sink | ✅ 有效 | 完整数据流 |
| `A -> B` | source -> processor | ✅ 有效 | 读取处理场景 |
| `B -> C` | processor -> sink | ✅ 有效 | 处理存储场景 |
| `A -> C` | source -> sink | ❌ **无效** | 缺少processor，无法直接交互 |
| `A -> A` | source -> source | ❌ **无效** | 同类型组件不能直接交互 |

### 具体判断规则

```
规则1：数据流必须包含processor角色（除非是Local）

规则2：source和sink之间必须有processor中转
  - source -> processor -> sink ✅ 有效
  - source -> sink ❌ 无效（缺少processor）

规则3：同角色类型组件不能直接交互
  - source -> source ❌ 无效（存储组件不能直接交互）
  - sink -> sink ❌ 无效（存储组件不能直接交互）
  - processor -> processor ✅ 有效（可以链式处理）

规则4：Local是特殊组件，默认可用，可替代source/sink
  - Local -> processor -> sink ✅ 有效
  - source -> processor -> Local ✅ 有效
```

---

## 用例生成决策算法

### 输入

```json
{
  "user_input": "HDFS数据经Spark计算存HDFS",
  "parsed_components": [
    {"name": "HDFS", "roles": ["source", "sink"]},
    {"name": "Spark", "roles": ["processor"]}
  ],
  "parsed_data_flow": ["HDFS", "Spark", "HDFS"],
  "component_cards": [
    "HDFS_CARD.json",
    "SPARK_CARD.json"
  ]
}
```

### 决策流程

```
Step 1: 加载组件卡片，获取每个组件的角色能力
  HDFS: supported_roles=["source", "sink"], cannot_act_as=["processor"]
  Spark: supported_roles=["processor"], cannot_act_as=["source", "sink"]

Step 2: 将组件转换为角色序列
  HDFS(as source) -> Spark(as processor) -> HDFS(as sink)
  角色序列: source -> processor -> sink

Step 3: 验证数据流有效性
  - 是否包含processor? ✅ 是（Spark）
  - source和sink是否通过processor连接? ✅ 是
  - 同角色类型是否直接交互? ❌ 否（HDFS在不同位置扮演不同角色）
  
  结论：✅ 有效数据流

Step 4: 生成组合用例
  必须生成(P1)：HDFS -> Spark -> HDFS（用户指定，角色序列有效）
  可合理扩展(P2)：Local -> Spark -> HDFS（Local替代source）
  可合理扩展(P2)：HDFS -> Spark -> Local（Local替代sink）
```

### 无效数据流示例

```
用户输入："HDFS数据直接写入HBase"

Step 1: 获取组件角色
  HDFS: supported_roles=["source", "sink"]
  HBase: supported_roles=["source", "sink"]

Step 2: 转换角色序列
  HDFS(as source) -> HBase(as sink)
  角色序列: source -> sink

Step 3: 验证数据流有效性
  - 是否包含processor? ❌ 否
  - source和sink是否直接交互? ❌ 是（无效）
  
  结论：❌ 无效数据流
  
  提示用户：需要添加processor组件（如Spark/Flink）作为中转
  建议修正：HDFS -> Spark -> HBase
```

---

## 用例生成抽象规则

### 规则模板（不带具体组件名）

```markdown
你是测试用例设计专家。请根据以下信息生成测试用例：

## 用户需求
{user_input}

## 解析结果
{parsed_prompt}

组件列表: {components_with_roles}
角色序列: {role_sequence}

## 组件知识卡片
{component_cards}

## 用例生成规则（抽象规则，基于角色判断）

### 规则1：验证数据流有效性

从组件卡片获取每个组件的角色能力：
- supported_roles: 该组件可扮演的角色
- cannot_act_as: 该组件不能扮演的角色

验证规则：
```
if 角色序列 == "source -> sink":
    return "无效，缺少processor"
    
if 角色序列 == "source -> source":
    return "无效，同类型组件不能直接交互"
    
if 角色序列 == "sink -> sink":
    return "无效，同类型组件不能直接交互"
    
if "processor" not in 角色序列:
    return "无效，必须包含processor"
    
if 角色序列 == "source -> processor -> sink":
    return "有效，完整数据流"
    
if 角色序列 == "source -> processor":
    return "有效，读取处理场景"
    
if 角色序列 == "processor -> sink":
    return "有效，处理存储场景"
```

### 规则2：生成组合用例

**必须生成（P1）：**
- 用户明确指定且角色序列有效的数据流

**可合理扩展（P2）：**
- 使用Local替代source/sink的数据流（Local默认可用）

**禁止生成：**
- 角色序列无效的数据流
- 添加用户未提及的组件

### 规则3：生成单组件用例

仅针对用户涉及的组件，每个组件生成3-5个功能用例。
不生成用户未提及组件的用例。

### 规则4：生成容错用例

仅针对用户涉及的组件，基于组件角色生成对应容错用例：
- source角色：读取不存在、空数据、权限错误
- processor角色：空数据处理、计算失败
- sink角色：写入失败、目录已存在

### 规则5：生成性能用例

仅针对用户涉及的组件：
- source角色：读取性能
- processor角色：计算性能
- sink角色：写入性能

## 输出格式

{
  "test_suite": {
    "components": ["仅用户涉及的组件"],
    "role_sequence_validation": "有效/无效及原因",
    "test_cases": {
      "functional": [...],
      "integration": [...],
      "fault_tolerance": [...],
      "performance": [...]
    }
  }
}
```

---

## 典型场景示例

### 示例1：有效数据流

**用户输入：** "A数据经B处理后存入A"（A是storage，B是compute）

**解析：**
```
组件A: supported_roles=["source", "sink"]
组件B: supported_roles=["processor"]

角色序列: source -> processor -> sink
```

**验证：** ✅ 有效

**生成用例：**
```
P1: A -> B -> A（用户指定，角色序列有效）
P2: Local -> B -> A（Local替代source）
P2: A -> B -> Local（Local替代sink）
```

---

### 示例2：无效数据流

**用户输入：** "A数据直接写入B"（A和B都是storage）

**解析：**
```
组件A: supported_roles=["source", "sink"]
组件B: supported_roles=["source", "sink"]

角色序列: source -> sink
```

**验证：** ❌ 无效，缺少processor

**处理：**
```
提示用户：数据流无效，缺少processor组件

建议修正：
- A -> C -> B（C是compute组件）
- 需要添加processor如Spark/Flink作为中转

不生成用例，等待用户修正输入
```

---

### 示例3：链式处理

**用户输入：** "A数据经B处理后经C再处理存入D"

**解析：**
```
组件A: supported_roles=["source"]
组件B: supported_roles=["processor"]
组件C: supported_roles=["processor"]
组件D: supported_roles=["sink"]

角色序列: source -> processor -> processor -> sink
```

**验证：** ✅ 有效，processor可以链式

**生成用例：**
```
P1: A -> B -> C -> D（用户指定）
P2: A -> B -> C -> Local（Local替代sink）
```

---

## 组件卡片交互规则字段

每个组件卡片必须包含以下字段，用于判断数据流有效性：

```json
{
  "component_roles": {
    "supported_roles": ["source", "sink", "processor"],
    "role_details": {
      "source": {"operations": ["read"], "api": ["..."]},
      "processor": {"operations": ["compute"], "api": ["..."]},
      "sink": {"operations": ["write"], "api": ["..."]}
    },
    "cannot_act_as": ["..."],
    "reason": "..."
  },
  
  "component_interaction_rules": {
    "as_source": {
      "compatible_downstream": [
        {"component_type": "compute", "examples": ["Spark", "Flink"]}
      ],
      "incompatible_downstream": [
        {"component_type": "storage", "reason": "需要processor中转"}
      ]
    },
    "as_sink": {
      "compatible_upstream": [
        {"component_type": "compute", "examples": ["Spark", "Flink"]}
      ],
      "incompatible_upstream": [
        {"component_type": "storage", "reason": "需要processor中转"}
      ]
    }
  },
  
  "valid_data_flows": ["source -> processor -> sink"],
  "invalid_data_flows": ["source -> sink（缺少processor）"]
}
```

---

## 总结

| 要点 | 说明 |
|------|------|
| **抽象规则** | 基于组件角色（source/processor/sink），而非具体组件名 |
| **角色判断** | 从组件卡片获取supported_roles |
| **数据流验证** | 角色序列必须符合有效模式 |
| **无效处理** | 提示用户修正，不生成用例 |
| **Local特殊** | 默认可用，可替代source/sink |
| **不发散** | 不添加用户未提及的组件 |