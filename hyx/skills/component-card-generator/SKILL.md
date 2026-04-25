---
name: component-card-generator
description: 从组件设计文档中提取关键信息，生成标准化的组件知识卡片JSON文件。用于测试场景规划和知识库管理。
license: MIT
metadata:
  author: opencode
  version: "1.0"
---

从组件设计文档提取知识卡片。

---

## 输入

- 组件设计文档路径（如 `{COMPONENT}_DESIGN_DOCUMENT.md`）

---

## 输出：知识卡片JSON结构（抽象模板）

以下为通用模板，实际输出根据具体组件填充：

```json
{
  "component_name": "{COMPONENT_NAME}",
  "component_type": "{storage|compute|streaming|database}",
  "version": "{version}",
  
  "component_roles": {
    "supported_roles": ["{source|processor|sink}"],
    "role_details": {
      "{role}": {
        "operations": ["{operation_list}"],
        "api": ["{api_list}"],
        "data_format": ["{format_list}"],
        "description": "{role_description}"
      }
    },
    "cannot_act_as": ["{cannot_act_roles}"],
    "reason": "{reason_based_on_component_type}"
  },
  
  "component_interaction_rules": {
    "as_source": {
      "compatible_downstream": [
        {
          "component_type": "compute",
          "data_flow": "source -> processor",
          "interaction_type": "read_data",
          "api_mapping": "{api_mapping_between_components}"
        }
      ],
      "incompatible_downstream": [
        {
          "component_type": "storage",
          "reason": "存储组件之间不能直接交互，需要processor组件中转"
        }
      ]
    },
    "as_sink": {
      "compatible_upstream": [
        {
          "component_type": "compute",
          "data_flow": "processor -> sink",
          "interaction_type": "write_data",
          "api_mapping": "{api_mapping_between_components}"
        }
      ],
      "incompatible_upstream": [
        {
          "component_type": "storage",
          "reason": "存储组件之间不能直接交互，需要processor组件中转"
        }
      ]
    }
  },
"valid_data_flows": [
    "source -> processor -> sink",
    "source -> processor",
    "processor -> sink",
    "local -> processor -> sink",
    "source -> processor -> local"
  ],
  
  "invalid_data_flows": [
    "source -> sink（缺少processor）",
    "source -> source（同类型组件不能直接交互）",
    "sink -> sink（同类型组件不能直接交互）"
  ],
  
  "core_concepts": {
    "key_abstractions": [
      {
        "name": "{abstraction_name}",
        "type": "{API|DataUnit|Config}",
        "description": "{description}"
      }
    ],
    "key_operations": ["{operations}"]
  },
  
  "test_scenarios": {
    "functional": ["{功能场景}"],
    "integration": ["{集成场景}"],
    "fault_tolerance": ["{容错场景}"],
    "performance": ["{性能场景}"]
  },
  
  "integration_points": [
    {
      "target_component_type": "compute",
      "interaction_type": "data_source",
      "api": "{api}"
    }
  ],
  
  "data_requirements": {
    "small": {"rows": 100, "size": "10KB"},
    "medium": {"rows": 100000, "size": "10MB"},
    "large": {"rows": 1000000, "size": "100MB"}
  }
}
```

---

## 组件角色定义（通用规则）

### 角色类型

| 角色 | 作用 | 操作类型 | 描述 |
|------|------|----------|------|
| **source** | 数据源 | read, consume, query | 向下游组件提供数据 |
| **processor** | 数据处理器 | compute, transform, aggregate | 转换/计算数据 |
| **sink** | 数据目标 | write, produce, insert | 接收上游数据输出 |

### 组件类型与角色映射（通用规则）

| 组件类型 | 可扮演角色 | 不能扮演角色 | 原因 |
|----------|------------|--------------|------|
| **storage** | source, sink | processor | 存储组件无数据处理能力 |
| **compute** | processor | source, sink | 计算组件需外部数据源/目标 |
| **streaming** | source, sink | processor | 消息传递组件，不处理数据 |
| **database** | source, sink | processor | 数据库组件，不处理数据 |

---

## 组件交互规则（通用规则）

### 有效数据流模式

| 模式 | 角色序列 | 说明 |
|------|----------|------|
| `source -> processor -> sink` | 完整数据流 | ✅ 有效 |
| `source -> processor` | 读取处理 | ✅ 有效 |
| `processor -> sink` | 处理存储 | ✅ 有效 |
| `local -> processor -> sink` | 本地到集群 | ✅ 有效（Local默认可用） |
| `source -> processor -> local` | 集群到本地 | ✅ 有效（Local默认可用） |

### 无效数据流模式

| 模式 | 说明 |
|------|------|
| `source -> sink` | ❌ 无效，缺少processor |
| `source -> source` | ❌ 无效，同类型组件不能直接交互 |
| `sink -> sink` | ❌ 无效，同类型组件不能直接交互 |

---

## 提取规则

从设计文档中提取以下关键信息：

| 文档章节 | 提取内容 | 卡片字段 |
|----------|----------|----------|
| 1.概述 | 组件名、类型、版本 | component_name, component_type, version |
| 3.功能模块清单 | API列表、操作类型 | core_concepts.key_operations, component_roles |
| 4.核心抽象 | 数据模型、关键概念 | core_concepts |
| 7.与其他组件交互关系 | 集成点、上下游组件 | integration_points, component_interaction_rules |
| 10.性能优化 | 常见问题 | common_issues |

---

## Prompt模板

```markdown
请从以下组件设计文档中提取知识卡片信息：

文档内容: {design_document_content}

提取要求：

## 1. 组件角色定义（component_roles）【关键】

分析该组件可以扮演的角色：
- **source**: 是否可以作为数据源提供数据？
- **processor**: 是否可以处理/计算数据？
- **sink**: 是否可以作为数据目标接收数据？

对于每个可扮演的角色，提取：
- supported_roles: ["source", "sink", ...]
- role_details: 每个角色的operations、api、data_format
- cannot_act_as: 不能扮演的角色
- reason: 不能扮演的原因

## 2. 组件交互规则（component_interaction_rules）【关键】

定义组件的上下游兼容关系：

**as_source（作为数据源时）**：
- compatible_downstream: 兼容的下游组件类型
- incompatible_downstream: 不兼容的下游组件类型及原因
- api_mapping: 与下游组件的API对应关系

**as_sink（作为数据目标时）**：
- compatible_upstream: 兼容的上游组件类型
- incompatible_upstream: 不兼容的上游组件类型及原因
- api_mapping: 与上游组件的API对应关系

## 3. 有效/无效数据流（valid_data_flows / invalid_data_flows）

列出该组件参与的典型数据流：
- valid_data_flows: 有效数据流模式
- invalid_data_flows: 无效数据流模式及原因

## 4. 核心概念（core_concepts）
- key_abstractions: 主要数据模型/API
- key_operations: 关键操作类型

## 5. 测试场景（test_scenarios）
- functional/integration/fault_tolerance/performance场景关键词

## 6. 集成点（integration_points）
- 与其他组件类型的交互点

## 7. 数据需求（data_requirements）
- 不同规模的数据建议

输出完整JSON格式的知识卡片。
```