---
name: input-parser
description: 解析用户自然语言输入，提取关键要素，输出结构化Prompt。支持业务场景识别、组件提取、数据流分析。
license: MIT
metadata:
  author: opencode
  version: "1.0"
---

解析用户自然语言输入，提取关键要素，输出结构化Prompt。

---

## 用户输入规范

### 推荐格式（结构化输入）

```
场景描述: {业务场景描述}
涉及组件: {组件列表，可选}
数据规模: {数据量级，可选}
验证重点: {重点关注点，可选}
```

### 示例输入（以storage-compute-storage场景为例）

**结构化输入（推荐）：**
```
场景描述: 测试从{source}读取数据，经{processor}聚合计算后写入{sink}的完整流程
涉及组件: {source_component}, {processor_component}
数据规模: 中等规模（100万条记录）
验证重点: 数据完整性、计算正确性、写入成功
```

**自然语言输入（支持）：**
```
测试{source}上数据经{processor}计算存{sink}上
```

---

## 输出格式（结构化Prompt，完整输出）

### 输出文件路径
```
./output/parsed_prompt.json
```

### 输出JSON结构

```json
{
  "prompt_id": "P_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "original_input": "{user_input}",
  "status": "success|error",
  "errors": [],
  
  "parsed_elements": {
    "scenario_type": "{functional|integration|fault_tolerance|performance}",
    "scenario_description": "{parsed_scenario_description}",
    
    "components": [
      {
        "name": "{component_name}",
        "role": "{source|processor|sink}",
        "operation": "{read|compute|write}",
        "confidence": 1.0,
        "position": 0
      }
    ],
    
    "data_flow": {
      "flow_type": "{linear|branch|merge}",
      "sequence": ["{component}.read", "{component}.compute", "{component}.write"],
      "description": "{flow_description}",
      "role_sequence": "source -> processor -> sink",
      "valid": true,
      "validation_reason": "完整数据流"
    },
    
    "data_requirements": {
      "input": {
        "source": "{source_component}",
        "type": "text_file",
        "format": "CSV",
        "size": "medium",
        "estimated_rows": 100000
      },
      "processing": {
        "type": "aggregation",
        "operations": ["groupBy", "count"],
        "logic_description": "{具体处理逻辑}"
      },
      "output": {
        "target": "{sink_component}",
        "type": "text_file",
        "format": "CSV",
        "expected_rows": "{估算行数}"
      }
    },
    
    "validation_points": [
      {
        "point_id": "VP_001",
        "point": "data_integrity",
        "description": "输入输出数据完整性",
        "priority": "P1",
        "assertion_type": "row_count_match"
      }
    ],
    
    "test_coverage_requirements": {
      "single_component": true,
      "component_combination": true,
      "fault_tolerance": false,
      "performance": false,
      "estimated_test_count": 10
    }
  },
  
  "component_cards_needed": [
    "{COMPONENT_1}_CARD.json",
    "{COMPONENT_2}_CARD.json"
  ],
  
  "output": {
    "path": "./output/parsed_prompt.json",
    "format": "json",
    "size_estimate": "2KB"
  },
  
"suggested_next_steps": [
    {
      "skill": "component-card-generator",
      "reason": "需要获取HDFS和Spark的知识卡片",
      "optional": true
    },
    {
      "skill": "scenario-planner",
      "reason": "直接生成测试用例（如果组件卡片已存在）",
      "optional": true
    }
  ]
}
}
```

### 输出示例（具体示例）

```json
{
  "prompt_id": "P_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "original_input": "测试HDFS数据经Spark聚合计算后存入HDFS",
  "status": "success",
  "errors": [],
  
  "parsed_elements": {
    "scenario_type": "integration",
    "scenario_description": "从HDFS读取数据，经Spark聚合计算，结果写入HDFS",
    
    "components": [
      {"name": "HDFS", "role": "source", "operation": "read", "confidence": 1.0, "position": 0},
      {"name": "Spark", "role": "processor", "operation": "compute", "confidence": 1.0, "position": 1},
      {"name": "HDFS", "role": "sink", "operation": "write", "confidence": 1.0, "position": 2}
    ],
    
    "data_flow": {
      "flow_type": "linear",
      "sequence": ["HDFS.read", "Spark.compute", "HDFS.write"],
      "description": "HDFS -> Spark -> HDFS",
      "role_sequence": "source -> processor -> sink",
      "valid": true,
      "validation_reason": "完整数据流，包含processor"
    },
    
    "test_coverage_requirements": {
      "single_component": true,
      "component_combination": true,
      "fault_tolerance": true,
      "performance": true,
      "estimated_test_count": 12
    }
  },
  
  "component_cards_needed": ["HDFS_CARD.json", "SPARK_CARD.json"],
  
  "output": {
    "path": "./output/parsed_prompt.json",
    "format": "json"
  },
  
"suggested_next_steps": [
    {
      "skill": "component-card-generator",
      "reason": "需要获取或生成组件知识卡片",
      "optional": true
    },
    {
      "skill": "scenario-planner",
      "reason": "直接生成测试用例（如果组件卡片已存在）",
      "optional": true
    }
  ]
}
}
```

---

## 解析Prompt模板

```
你是测试需求解析专家。请分析以下用户输入，提取关键要素：

用户输入: {user_input}

请按以下结构输出JSON：

1. 场景类型识别 (scenario_type)
   - functional: 单组件功能测试
   - integration: 多组件集成测试
   - fault_tolerance: 容错测试
   - performance: 性能测试

2. 组件识别 (components)
   - 识别所有涉及的组件
   - 标注每个组件的角色(source/processor/sink)
   - 标注操作类型(read/write/compute)
   - 给出置信度(0-1)

3. 数据流分析 (data_flow)
   - 数据流向顺序
   - 每个节点的操作

4. 数据需求 (data_requirements)
   - 输入数据类型、格式
   - 处理操作类型
   - 输出数据类型

5. 验证点 (validation_points)
   - 关键验证点
   - 验证优先级

6. 测试覆盖要求 (test_coverage_requirements)
   - 是否需要单组件测试
   - 是否需要组合测试
   - 是否需要容错测试
   - 是否需要性能测试

输出结构化JSON。
```

---

## 组件识别规则

### 组件关键词映射表（示例，可扩展）

以下为常见组件的关键词映射示例，实际识别时可根据用户输入动态匹配：

| 关键词 | 组件名 | 匹配规则 |
|--------|--------|----------|
| {storage_keywords} | {storage_component} | 直接匹配 |
| {compute_keywords} | {compute_component} | 直接匹配 |
| {streaming_keywords} | {streaming_component} | 直接匹配 |
| {database_keywords} | {database_component} | 直接匹配 |

**常见组件关键词示例：**

| 关键词 | 组件名 | 说明 |
|--------|--------|------|
| 分布式文件系统、HDFS、hdfs | Apache HDFS | 存储组件 |
| Spark、spark | Apache Spark | 计算组件 |
| Kafka、kafka、消息队列 | Apache Kafka | 消息组件 |
| Flink、flink、流处理 | Apache Flink | 流处理组件 |
| HBase、hbase | Apache HBase | 数据库组件 |
| Hive、hive | Apache Hive | 数据仓库 |
| MySQL、mysql、数据库 | MySQL | 关系数据库 |
| Redis、redis | Redis | 缓存数据库 |
| Elasticsearch、es | Elasticsearch | 搜索引擎 |

### 角色识别规则

| 语境关键词 | 角色 | 操作 |
|------------|------|------|
| 读取、加载、输入、从... | source | read |
| 计算、处理、分析、聚合 | processor | compute |
| 写入、存储、输出、到... | sink | write |
| 验证、检查、确认 | validator | validate |

---

## 处理流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  Step 1: 输入规范化                  │
│  - 判断输入格式                      │
│  - 结构化输入→直接解析               │
│  - 自然语言→LLM解析                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Step 2: 组件识别                    │
│  - 关键词匹配                        │
│  - 角色判断                          │
│  - 检查卡片是否存在                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Step 3: 数据流分析                  │
│  - 组件顺序                          │
│  - 操作类型                          │
│  - 依赖关系                          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Step 4: 输出Prompt                  │
│  - 结构化JSON                        │
│  - 标记下一步action                  │
└─────────────────────────────────────┘
```

---

## 下一步Action标记

| action | 条件 | 后续调用 |
|--------|------|----------|
| fetch_component_cards | 卡片全部存在 | 直接获取 |
| generate_component_card | 卡片不存在 | component-card-generator |
| call_scenario_planner | 卡片已准备好 | scenario-planner |