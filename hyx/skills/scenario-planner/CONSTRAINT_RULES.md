# 测试用例生成约束规则

## 核心原则：严格基于用户输入，不发散

### 问题说明

用户反馈示例：
- 用户输入："HDFS数据经Spark计算存HDFS"
- 实际涉及组件：HDFS, Spark（两个组件）
- 错误做法：添加Kafka/HBase等未提及组件的组合用例
- 正确做法：只生成HDFS和Spark相关的用例

### 为什么不能发散？

1. **环境兼容性**：用户环境可能没有Kafka/HBase等组件，添加这些用例会导致无法执行
2. **测试有效性**：超出用户需求的用例没有实际意义
3. **资源浪费**：为不存在组件准备数据和配置是浪费

---

## 组件分类

| 类型 | 组件列表 | 特点 | 用例生成策略 |
|------|----------|------|--------------|
| **环境依赖组件** | HDFS, Spark, Kafka, Flink, HBase, Hive, MySQL, Redis, Elasticsearch等 | 需要特定环境配置才能运行 | 用户明确提及才生成 |
| **默认可用组件** | Local本地文件系统 | 无需额外环境，任何机器都有 | 可作为合理补充(P2) |

---

## 组合场景决策表

| 场景来源 | 示例 | 决策 | 优先级 |
|----------|------|------|--------|
| **用户明确指定** | "HDFS -> Spark -> HDFS" | ✅ 必须生成 | P1 |
| **Local合理补充** | "Local -> Spark -> HDFS" | ✅ 可生成（Local默认可用） | P2 |
| **未提及环境依赖组件** | "HDFS -> Spark -> Kafka"（用户未提及Kafka） | ❌ 禁止生成 | - |

---

## 典型用户输入与对应用例范围

### 示例1：单组件输入

**用户输入：** "测试Spark功能"

**解析：**
- 涉及组件：Spark
- 环境需求：Spark环境

**生成用例：**
```
✅ Spark单组件功能用例(3-5个)
✅ Spark单组件容错用例(2-3个)
✅ Spark单组件性能用例(1-2个)

❌ 不生成：HDFS/Kafka等其他组件用例
❌ 不生成：多组件组合用例（无组合）
```

---

### 示例2：两组件输入

**用户输入：** "HDFS数据经Spark处理后存储"

**解析：**
- 涉及组件：HDFS, Spark
- 数据流：HDFS -> Spark -> (未指定目标)
- 环境需求：HDFS + Spark

**生成用例：**
```
✅ HDFS单组件功能用例(3-5个)
✅ Spark单组件功能用例(3-5个)

✅ HDFS -> Spark组合用例(P1，用户明确指定)
✅ Local -> Spark组合用例(P2，合理扩展)
✅ HDFS -> Spark -> Local组合用例(P2，合理扩展)

✅ HDFS相关容错用例
✅ Spark相关容错用例
✅ HDFS->Spark组合容错用例

❌ 不生成：Kafka/HBase等其他组件用例
❌ 不生成：HDFS -> Spark -> Kafka（用户未提及Kafka）
```

---

### 示例3：往返流输入

**用户输入：** "HDFS数据经Spark计算存HDFS"

**解析：**
- 涉及组件：HDFS, Spark
- 数据流：HDFS -> Spark -> HDFS
- 环境需求：HDFS + Spark

**生成用例：**
```
✅ HDFS单组件功能用例(3-5个)
✅ Spark单组件功能用例(3-5个)

✅ HDFS -> Spark -> HDFS组合用例(P1，用户明确主场景)
✅ Local -> Spark -> HDFS组合用例(P2，合理扩展）
✅ HDFS -> Spark -> Local组合用例(P2，合理扩展)

✅ HDFS容错用例(读取不存在文件、空文件、权限等)
✅ Spark容错用例(空RDD、内存溢出等)
✅ HDFS->Spark->HDFS组合容错用例(中途失败、写入冲突等)

✅ HDFS读取性能用例
✅ Spark计算性能用例
✅ HDFS->Spark->HDFS端到端性能用例

❌ 不生成：Kafka/HBase/Hive等其他组件用例
❌ 不生成：HDFS -> Spark -> Kafka（用户未提及Kafka）
❌ 不生成：Kafka -> Spark -> HDFS（用户未提及Kafka）
```

---

### 示例4：三组件输入

**用户输入：** "Kafka消息经Spark处理后存入HDFS"

**解析：**
- 涉及组件：Kafka, Spark, HDFS
- 数据流：Kafka -> Spark -> HDFS
- 环境需求：Kafka + Spark + HDFS

**生成用例：**
```
✅ Kafka单组件功能用例(3-5个)
✅ Spark单组件功能用例(3-5个)
✅ HDFS单组件功能用例(3-5个)

✅ Kafka -> Spark -> HDFS组合用例(P1，用户明确指定)
✅ Local -> Spark -> HDFS组合用例(P2，合理扩展)
✅ Kafka -> Spark -> Local组合用例(P2，合理扩展)

✅ Kafka容错用例(连接失败、空消息等)
✅ Spark容错用例
✅ HDFS容错用例
✅ Kafka->Spark->HDFS组合容错用例

❌ 不生成：HBase/MySQL等其他组件用例
❌ 不生成：Kafka -> Spark -> HBase（用户未提及HBase）
```

---

### 示例5：本地文件输入

**用户输入：** "本地文件经Spark处理后存入HDFS"

**解析：**
- 涉及组件：Local, Spark, HDFS
- 数据流：Local -> Spark -> HDFS
- 环境需求：Spark + HDFS（Local默认可用）

**生成用例：**
```
✅ Spark单组件功能用例(3-5个)
✅ HDFS单组件功能用例(3-5个)
(Local无需单独测试，默认可用)

✅ Local -> Spark -> HDFS组合用例(P1，用户明确指定)
✅ HDFS -> Spark -> Local组合用例(P2，反向场景）

❌ 不生成：Kafka等其他组件用例
```

---

## 用例生成Prompt模板（修正版）

```markdown
你是测试用例设计专家。请根据以下信息生成完整的测试用例：

## 用户需求
{user_input}

## 解析结果
{parsed_prompt}

涉及的组件：{components_list}
数据流：{data_flow}

## 组件知识卡片
{component_cards}

## 用例生成规则（严格遵守）

### 核心约束
1. **严格基于用户输入的组件范围，不发散**
2. **只生成用户明确提及的组件用例**
3. **Local可作为合理补充（P2优先级）**
4. **禁止添加用户未提及的环境依赖组件**

### 1. 单组件功能用例
仅针对用户涉及的组件生成3-5个功能用例：
- 核心API功能验证
- 边界条件测试
- 参数有效性测试

禁止生成用户未提及组件的功能用例。

### 2. 多组件组合用例
严格按照用户输入的数据流生成组合用例：

**必须生成（P1）：**
- 用户明确指定的数据流组合
- 例如：用户说"HDFS -> Spark -> HDFS"，生成此组合用例

**可合理扩展（P2）：**
- Local作为source/sink的组合（Local默认可用）
- 例如：Local -> Spark -> HDFS, HDFS -> Spark -> Local

**禁止生成：**
- 用户未提及的环境依赖组件组合
- 例如：用户未提及Kafka，不生成HDFS -> Spark -> Kafka

### 3. 容错场景用例
仅针对用户涉及的组件生成容错用例：
- 文件不存在、空数据、权限问题等
- 不生成未提及组件的容错用例

### 4. 性能场景用例
仅针对用户涉及的组件生成性能用例：
- 读取性能、计算性能、端到端性能
- 不生成未提及组件的性能用例

## 输出格式

生成完整的JSON格式测试用例，仅包含用户涉及的组件。

{
  "test_suite": {
    "suite_id": "TS_001",
    "suite_name": "...",
    "components": ["仅用户涉及的组件"],
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

## 修正后的JSON示例

用户输入：**"HDFS数据经Spark计算存HDFS"**

```json
{
  "test_suite": {
    "suite_id": "TS_001",
    "suite_name": "HDFS-Spark-HDFS完整测试",
    "components": ["HDFS", "Spark"],
    "test_cases": {
      "functional": [
        {
          "case_id": "TC_FUNC_HDFS_001",
          "component": "HDFS",
          "case_name": "HDFS写入文件"
        },
        {
          "case_id": "TC_FUNC_HDFS_002",
          "component": "HDFS",
          "case_name": "HDFS读取文件"
        },
        {
          "case_id": "TC_FUNC_SPARK_001",
          "component": "Spark",
          "case_name": "Spark聚合计算"
        }
      ],
      "integration": [
        {
          "case_id": "TC_INT_001",
          "data_flow": "HDFS -> Spark -> HDFS",
          "priority": "P1",
          "description": "用户明确指定的主场景"
        },
        {
          "case_id": "TC_INT_002",
          "data_flow": "Local -> Spark -> HDFS",
          "priority": "P2",
          "description": "Local合理扩展，默认可用"
        },
        {
          "case_id": "TC_INT_003",
          "data_flow": "HDFS -> Spark -> Local",
          "priority": "P2",
          "description": "Local合理扩展，默认可用"
        }
      ],
      "fault_tolerance": [
        {
          "case_id": "TC_FT_001",
          "component": "HDFS",
          "case_name": "HDFS读取不存在文件"
        },
        {
          "case_id": "TC_FT_002",
          "component": "Spark",
          "case_name": "Spark处理空RDD"
        },
        {
          "case_id": "TC_FT_003",
          "components": ["HDFS", "Spark"],
          "case_name": "HDFS->Spark->HDFS中途失败"
        }
      ],
      "performance": [
        {
          "case_id": "TC_PERF_001",
          "component": "HDFS",
          "case_name": "HDFS读取性能"
        },
        {
          "case_id": "TC_PERF_002",
          "component": "Spark",
          "case_name": "Spark计算性能"
        }
      ]
    }
  }
}
```

**注意：不包含Kafka/HBase等未提及组件的用例！**

---

## 总结

| 原则 | 说明 |
|------|------|
| **严格基于输入** | 只生成用户明确提及的组件和组合 |
| **Local可补充** | Local默认可用，可作为合理扩展(P2) |
| **不发散** | 禁止添加用户未提及的环境依赖组件 |
| **环境兼容** | 确保所有用例在用户环境中可执行 |