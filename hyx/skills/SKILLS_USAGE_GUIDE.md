# Skills使用指南

## Skill体系概览

本项目包含7个通用Skills，支持任意组件组合的自动化测试生成。

---

## Skill调用顺序

```
用户输入自然语言
       │
       ▼
┌─────────────────┐
│ 1. input-parser │ 解析输入，识别组件角色
└─────────────────┘
       │
       ▼
┌─────────────────────┐
│ 2. 组件卡片获取      │
│  - 存在：直接获取    │
│  - 不存在：调用      │
│    component-card-  │
│    generator        │
└─────────────────────┘
       │
       ▼
┌─────────────────┐
│ 3. scenario-    │ 基于角色验证数据流
│    planner      │ 生成测试用例
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ 4. data-        │ 生成测试数据
│    generator    │（公开数据集优先）
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ 5. test-script- │ 生成pytest脚本
│    generator    │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ 6. env-config-  │ 生成环境配置
│    generator    │（docker-compose等）
└─────────────────┘
       │
       ▼
   测试环境就绪
```

---

## 使用示例

### 示例1：单组件测试

**用户输入：**
```
测试Spark聚合功能
```

**Skill处理流程：**

1. **input-parser** 解析：
   ```json
   {
     "components": [{"name": "Spark", "role": "processor"}],
     "scenario_type": "functional"
   }
   ```

2. **获取组件卡片**：检查SPARK_CARD.json是否存在

3. **scenario-planner** 生成用例：
   - Spark单组件功能用例(3-5个)
   - Spark容错用例(2-3个)
   - Spark性能用例(1-2个)

4. **data-generator** 生成数据

5. **test-script-generator** 生成脚本

6. **env-config-generator** 生成Spark环境配置

---

### 示例2：多组件组合测试

**用户输入：**
```
测试A数据经B处理后存入A
```

**Skill处理流程：**

1. **input-parser** 解析：
   ```json
   {
     "components": [
       {"name": "A", "role": "source"},
       {"name": "B", "role": "processor"},
       {"name": "A", "role": "sink"}
     ],
     "role_sequence": "source -> processor -> sink"
   }
   ```

2. **验证数据流**：
   - 角色序列：source -> processor -> sink ✅ 有效

3. **获取组件卡片**：A_CARD.json, B_CARD.json

4. **scenario-planner** 生成用例：
   - A单组件功能用例
   - B单组件功能用例
   - A -> B -> A组合用例(P1)
   - Local -> B -> A组合用例(P2)
   - A -> B -> Local组合用例(P2)
   - 容错用例
   - 性能用例

5. **data-generator** 生成数据

6. **test-script-generator** 生成脚本

7. **env-config-generator** 生成A+B环境配置

---

### 示例3：无效数据流处理

**用户输入：**
```
测试A数据直接写入B
```

**Skill处理流程：**

1. **input-parser** 解析：
   ```json
   {
     "components": [
       {"name": "A", "role": "source"},
       {"name": "B", "role": "sink"}
     ],
     "role_sequence": "source -> sink"
   }
   ```

2. **验证数据流**：
   - 角色序列：source -> sink ❌ 无效（缺少processor）

3. **处理结果**：
   ```
   提示用户：数据流无效，缺少processor组件
   
   建议修正：
   - A -> processor组件 -> B
   - 需要添加compute组件作为中转
   
   不生成测试用例，等待用户修正输入
   ```

---

## 核心抽象规则

### 组件角色判断（通用）

| 组件类型 | 角色 | 判断依据 |
|----------|------|----------|
| storage类 | source, sink | 从组件卡片获取supported_roles |
| compute类 | processor | 从组件卡片获取supported_roles |
| streaming类 | source, sink | 从组件卡片获取supported_roles |
| database类 | source, sink | 从组件卡片获取supported_roles |

### 数据流验证（通用）

```
规则：source和sink之间必须有processor中转

有效数据流：
- source -> processor -> sink ✅
- source -> processor ✅
- processor -> sink ✅

无效数据流：
- source -> sink ❌
- source -> source ❌
- sink -> sink ❌
```

### 用例生成范围（通用）

```
规则：只生成用户明确提及的组件用例

必须生成(P1)：用户明确指定且角色序列有效
可合理扩展(P2)：Local替代source/sink
禁止生成：用户未提及组件、无效角色序列
```

---

## 支持的组件

Skills支持任意组件，只要该组件有知识卡片。

### 已有知识卡片的组件

- Spark（已创建）
- HDFS（需创建）
- Kafka（需创建）
- Flink（需创建）
- HBase（需创建）
- MySQL（需创建）
- Redis（需创建）
- 其他...（调用component-card-generator生成）

### 生成新组件知识卡片

```
调用component-card-generator：
输入：组件名称（如"Kafka"）

输出：
- KAFKA_CARD.json
- KAFKA_CARD.md
- KAFKA_CARD.xlsx
```

---

## 组件知识卡片结构

```json
{
  "component_name": "{COMPONENT}",
  "component_roles": {
    "supported_roles": ["source|processor|sink"],
    "cannot_act_as": ["{role}"],
    "reason": "{reason}"
  },
  "component_interaction_rules": {
    "as_source": {
      "compatible_downstream": [{"component_type": "compute"}],
      "incompatible_downstream": [{"component_type": "storage"}]
    },
    "as_sink": {
      "compatible_upstream": [{"component_type": "compute"}],
      "incompatible_upstream": [{"component_type": "storage"}]
    }
  },
  "valid_data_flows": ["source -> processor -> sink"],
  "invalid_data_flows": ["source -> sink"]
}
```

---

## 测试用例输出格式

```json
{
  "test_suite": {
    "components": ["用户涉及的组件"],
    "role_sequence_validation": {
      "sequence": "source -> processor -> sink",
      "valid": true
    },
    "test_cases": {
      "functional": ["基于组件角色的功能用例"],
      "integration": ["基于角色序列的组合用例"],
      "fault_tolerance": ["基于组件角色的容错用例"],
      "performance": ["基于组件角色的性能用例"]
    }
  }
}
```

---

## Skills通用性保证

所有Skills遵循以下通用原则：

1. **规则抽象**：基于角色而非具体组件名
2. **模板抽象**：使用 `{component}` 占位符
3. **动态识别**：从组件卡片获取角色能力
4. **不发散**：只生成用户明确提及的组件用例
5. **示例标注**：具体组件名仅用于示例并标注

---

## 文件结构

```
.opencode/skills/
├── input-parser/
│   └── SKILL.md                    # 输入解析Skill
├── component-design-doc/
│   └── SKILL.md                    # 设计文档生成Skill
├── component-card-generator/
│   └── SKILL.md                    # 知识卡片生成Skill
├── scenario-planner/
│   ├── SKILL.md                    # 测试用例生成Skill
│   ├── CONSTRAINT_RULES_ABSTRACT.md # 抽象约束规则
│   └── CONSTRAINT_RULES.md         # 具体示例（参考）
├── data-generator/
│   └── SKILL.md                    # 数据生成Skill
├── test-script-generator/
│   └── SKILL.md                    # 脚本生成Skill
├── env-config-generator/
│   └── SKILL.md                    # 环境配置Skill
├── SKILLS_GENERALIZATION_REPORT.md # 通用性检查报告
└── SKILLS_USAGE_GUIDE.md           # 使用指南
```

---

## 总结

Skills体系完全通用化，支持任意组件组合的自动化测试生成。核心特性：

- ✅ 规则基于角色，而非具体组件名
- ✅ 数据流自动验证有效性
- ✅ 无效数据流提示修正
- ✅ 只生成用户涉及的组件用例
- ✅ Local默认可用，合理扩展
- ✅ 支持任意新组件（动态生成卡片）