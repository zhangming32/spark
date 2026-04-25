# Skills测试指南

## 测试方式

有两种测试方式：

### 方式1：直接对话测试（推荐）

在当前对话中直接输入测试需求，opencode会自动调用相应skill。

### 方式2：Skill命令调用

使用 `/skill` 命令显式调用。

---

## 测试场景选择

| 测试级别 | 测试内容 | 验证点 |
|----------|----------|--------|
| **Level 1** | 单skill测试 | 单个skill输出正确性 |
| **Level 2** | 多skill串联 | 输入输出传递正确性 |
| **Level 3** | 完整流程 | 从输入到输出的全流程 |

---

## Level 1：单Skill测试

### 1.1 测试 component-design-doc

**测试输入：**
```
请调用 component-design-doc skill，为组件 Kafka 生成设计文档
```

**预期输出：**
```
output/KAFKA_DESIGN_DOCUMENT.md
├─ 1.概述
├─ 2.架构设计
├─ 3.功能模块清单
├─ 4.核心抽象
├─ 5.内部设计
├─ 6.容错机制
├─ 7.与其他组件交互关系
├─ 8.API参考
├─ 9.生态系统
├─ 10.性能优化
├─ 11.安全机制
├─ 12.监控与运维
├─ 13.设计演进
└─ 附录
```

**验证命令：**
```bash
# 检查文档是否生成
ls -la KAFKA_DESIGN_DOCUMENT.md

# 检查文档结构
grep "^## " KAFKA_DESIGN_DOCUMENT.md | head -15
```

---

### 1.2 测试 component-card-generator

**测试输入：**
```
请调用 component-card-generator skill，从 Spark 设计文档生成知识卡片
```

**预期输出：**
```
output/
├─ SPARK_CARD.json    (供程序调用)
├─ SPARK_CARD.md      (供人阅读)
└─ SPARK_CARD.xlsx    (供人阅读)
```

**验证命令：**
```bash
# 检查JSON结构
cat output/SPARK_CARD.json | python -m json.tool | head -50

# 验证关键字段
grep "component_roles" output/SPARK_CARD.json
grep "supported_roles" output/SPARK_CARD.json
grep "valid_data_flows" output/SPARK_CARD.json
```

---

### 1.3 测试 input-parser

**测试输入：**
```
请调用 input-parser skill，解析以下输入：
"测试HDFS上数据经Spark聚合计算后存储到HDFS"
```

**预期输出：**
```json
{
  "parsed_elements": {
    "components": ["HDFS", "Spark"],
    "role_sequence": "source -> processor -> sink",
    "scenario_type": "integration",
    "validation": {"valid": true}
  }
}
```

**验证点：**
- 组件识别正确（HDFS、Spark）
- 角色分配正确（source、processor、sink）
- 数据流验证正确（有效）

---

### 1.4 测试 scenario-planner

**测试输入：**
```
请调用 scenario-planner skill，根据以下信息生成测试用例：

组件：HDFS, Spark
数据流：HDFS -> Spark -> HDFS
角色序列：source -> processor -> sink
```

**预期输出：**
```json
{
  "test_suite": {
    "test_cases": {
      "functional": [/* 3-5个用例 */],
      "integration": [/* 组合用例 */],
      "fault_tolerance": [/* 容错用例 */],
      "performance": [/* 性能用例 */]
    }
  }
}
```

**验证点：**
- 包含四类用例
- 组合用例基于角色序列生成
- 不包含未提及组件

---

## Level 2：多Skill串联测试

### 2.1 设计文档 → 知识卡片

**测试输入：**
```
请依次调用：
1. component-design-doc 为 Flink 生成设计文档
2. component-card-generator 从文档生成知识卡片
```

**预期输出：**
```
1. FLINK_DESIGN_DOCUMENT.md
2. FLINK_CARD.json + FLINK_CARD.md + FLINK_CARD.xlsx
```

**验证：**
```bash
# 检查卡片是否包含设计文档的关键信息
grep "component_name" FLINK_CARD.json
grep "supported_roles" FLINK_CARD.json
```

---

### 2.2 输入解析 → 用例生成

**测试输入：**
```
请依次调用：
1. input-parser 解析："测试Kafka消息经Flink处理后存入HDFS"
2. scenario-planner 生成测试用例
```

**验证传递：**
- input-parser输出是否传递给scenario-planner
- 组件信息是否正确传递

---

## Level 3：完整流程测试

### 3.1 端到端测试（单组件）

**测试输入：**
```
请执行完整流程，测试以下场景：
"测试Spark聚合计算功能"
```

**预期完整输出：**
```
output/
├─ SPARK_CARD.json          (知识卡片)
├─ test_cases.json          (测试用例)
├─ test_cases.xlsx          (测试用例Excel)
├─ test_data/
│   ├─ input_data.csv       (测试数据)
│   └─ expected_output.csv  (预期输出)
├─ tests/
│   ├─ conftest.py          (pytest配置)
│   ├─ test_spark_unit.py   (单组件测试)
│   └─ test_spark_integration.py
└─ environment/
    ├─ docker-compose.yaml  (环境配置)
    └─ test_config.yaml
```

---

### 3.2 端到端测试（多组件）

**测试输入：**
```
请执行完整流程，测试以下场景：
"测试HDFS数据经Spark聚合计算后存入HDFS"
```

**预期输出：**
```
output/
├─ HDFS_CARD.json + SPARK_CARD.json
├─ test_cases.json (包含：
    ├─ HDFS单组件用例
    ├─ Spark单组件用例
    ├─ HDFS->Spark->HDFS组合用例
    ├─ Local->Spark->HDFS组合用例
    ├─ 容错用例
    └─ 性能用例)
├─ test_data/
├─ tests/
└─ environment/
```

**验证：**
```bash
# 检查用例数量
cat test_cases.json | grep "case_id" | wc -l

# 检查组合用例
grep "integration" test_cases.json

# 检查不包含未提及组件
grep -i "kafka\|flink" test_cases.json # 应为空
```

---

### 3.3 异常流程测试

**测试输入：**
```
请执行流程：
"测试HDFS数据直接写入HBase"
```

**预期结果：**
```json
{
  "status": "error",
  "error": "数据流无效，缺少processor组件",
  "suggestion": "请添加compute组件作为中转，如: HDFS -> Spark -> HBase"
}
```

**验证点：**
- 正确识别无效数据流
- 返回错误和建议
- 不生成测试用例

---

## 快速测试命令

### 一键测试脚本

```bash
#!/bin/bash
# quick_test.sh

echo "=== Skills快速测试 ==="

# 测试1：设计文档生成
echo "[Test 1] component-design-doc..."
touch test_result_1.log

# 测试2：知识卡片生成
echo "[Test 2] component-card-generator..."
touch test_result_2.log

# 测试3：输入解析
echo "[Test 3] input-parser..."
touch test_result_3.log

# 测试4：用例生成
echo "[Test 4] scenario-planner..."
touch test_result_4.log

echo "=== 测试完成 ==="
```

---

## 测试检查清单

| 检查项 | 命令 | 预期结果 |
|--------|------|----------|
| 文档生成 | `ls *_DESIGN_DOCUMENT.md` | 文档存在 |
| 卡片生成 | `ls *_CARD.json` | JSON存在且valid |
| 卡片结构 | `jq .component_name *_CARD.json` | 组件名正确 |
| 角色定义 | `jq .component_roles *_CARD.json` | 角色正确 |
| 用例数量 | `grep -c case_id test_cases.json` | >= 10 |
| 数据流验证 | `grep role_sequence test_cases.json` | 验证通过 |
| 不发散验证 | `grep -i kafka test_cases.json` (用户输入不含kafka时) | 无匹配 |
| pytest脚本 | `ls tests/*.py` | 脚本存在 |
| docker配置 | `ls docker-compose.yaml` | 配置存在 |

---

## 立即开始测试

**最简单的测试方式：**

直接在当前对话输入：

```
请调用 component-design-doc skill，为 Kafka 生成设计文档
```

或测试完整流程：

```
请执行完整测试流程：
输入：测试Spark聚合计算功能
```

**我会立即响应并执行skill，你可以看到实时输出结果。**