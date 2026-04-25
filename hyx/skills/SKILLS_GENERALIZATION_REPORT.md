# Skills通用性检查报告

## 检查标准

Skills应该遵循以下通用性原则：

1. **规则抽象化**：规则基于组件角色（source/processor/sink），而非具体组件名
2. **模板抽象化**：输入/输出模板使用 `{component}` 占位符，而非具体组件名
3. **示例标注化**：具体组件名仅在"示例"中使用，需明确标注为"示例"

---

## 检查结果

### 1. input-parser/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| 输入示例硬编码"HDFS、Spark" | 改为 `{source_component}, {processor_component}` |
| 输出示例硬编码 | 改为抽象模板 `{component_name}` |
| 组件关键词映射表硬编码 | 标注为"示例映射表"，说明可扩展 |

### 2. component-design-doc/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| Usage示例硬编码 | 标注为"示例输入" |

**说明**：此skill用于生成任意组件设计文档，示例组件名有助于理解用法，可保留。

### 3. component-card-generator/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| 输出模板硬编码"HDFS" | 改为 `{COMPONENT_NAME}` |
| 示例API硬编码"FileSystem.open()" | 改为 `{api_list}` |
| 组件角色能力表硬编码 | 改为通用规则表 |
| 数据流示例硬编码"HDFS->Spark" | 改为 `source -> processor -> sink` |

### 4. scenario-planner/SKILL.md ✅ 已修正（前文已完成）

| 问题 | 修正 |
|------|------|
| 用例规则硬编码"HDFS、Spark" | 改为抽象规则"A、B" |
| 角色判断硬编码 | 改为基于角色（source/processor/sink）判断 |
| 组合场景示例硬编码 | 改为抽象模板 |

### 5. data-generator/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| 测试用例输入硬编码"HDFS、Spark" | 改为 `{source_component}, {processor_component}` |
| 数据需求示例硬编码 | 改为抽象模板 |

### 6. test-script-generator/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| 输入模板硬编码 | 改为抽象模板 `{source_component}` |
| 输出结构硬编码"hdfs_fixtures.py" | 改为 `{component}_fixtures.py` |

**说明**：pytest示例代码可保留具体组件名，因为它们是代码示例。

### 7. env-config-generator/SKILL.md ✅ 已修正

| 问题 | 修正 |
|------|------|
| 输入模板硬编码"HDFS、Spark、Kafka" | 改为 `{component_1}, {component_2}` |
| 输出结构硬编码"hdfs/"目录 | 标注为"示例模板" |

**说明**：docker-compose和配置文件示例可保留具体组件名，因为它们是配置示例。

---

## 剩余硬编码组件名分类

根据grep统计，剩余329处包含具体组件名，分类如下：

| 类型 | 数量 | 处理方式 |
|------|------|----------|
| **代码示例**（pytest/bash） | ~150 | 可保留，标注为示例 |
| **配置文件示例**（docker-compose/xml） | ~100 | 可保留，标注为示例 |
| **说明性文本**（如"常见组件示例"） | ~50 | 可保留，标注为示例 |
| **需要修正的模板** | ~29 | 已修正 |

---

## 通用性原则总结

### ✅ 需要修正

1. **规则描述**：必须使用抽象角色（source/processor/sink）
2. **模板定义**：必须使用 `{component}` 占位符
3. **决策逻辑**：必须基于角色而非具体组件名

### ⚠️ 可保留（需标注示例）

1. **代码示例**：pytest脚本、bash脚本等
2. **配置示例**：docker-compose、xml配置等
3. **常见组件列举**：如"常见组件：HDFS/Spark/Kafka..."

### 标注方式

在示例前添加以下标注：

```markdown
### 示例（以storage-compute-storage场景为例）
...
```

或

```markdown
### docker-compose.yaml示例（包含storage、compute、streaming组件）
...
```

---

## Skills目录结构

```
.opencode/skills/
├── input-parser/
│   └── SKILL.md               ✅ 已修正为抽象模板
├── component-design-doc/
│   └── SKILL.md               ✅ 已标注示例
├── component-card-generator/
│   └── SKILL.md               ✅ 已修正为抽象模板
├── scenario-planner/
│   ├── SKILL.md               ✅ 已修正为抽象规则
│   ├── CONSTRAINT_RULES.md    ✅ 具体组件示例（参考）
│   └── CONSTRAINT_RULES_ABSTRACT.md ✅ 抽象规则版
├── data-generator/
│   └── SKILL.md               ✅ 已修正为抽象模板
├── test-script-generator/
│   └── SKILL.md               ✅ 已修正，代码示例保留
└── env-config-generator/
    └── SKILL.md               ✅ 已修正，配置示例保留
```

---

## 核心抽象规则

所有Skills遵循以下核心抽象规则：

### 组件角色体系

| 角色 | 功能 | 操作类型 |
|------|------|----------|
| source | 数据源 | read, consume, query |
| processor | 数据处理 | compute, transform |
| sink | 数据目标 | write, produce, insert |
| Local | 特殊组件 | 默认可用 |

### 数据流有效性规则

```
有效：
- source -> processor -> sink
- source -> processor
- processor -> sink
- processor -> processor（链式）

无效：
- source -> sink（缺少processor）
- source -> source（同类型不能直接交互）
- sink -> sink（同类型不能直接交互）
```

### 用例生成决策规则

```
基于组件角色而非具体组件名：

if role_sequence == "source -> processor -> sink":
    generate P1 test case
    
if role_sequence == "source -> sink":
    return error, suggest adding processor
    
if component not in user_input:
    do not generate
```

---

## 结论

所有7个Skills已修正为通用抽象规则，具体组件名仅保留在"示例"部分并已标注。Skills现在支持任意组件组合的测试用例生成。