---
name: scenario-planner
description: 根据用户自然语言输入和组件知识卡片，生成结构化测试用例（Excel/JSON格式）。识别场景类型、分解测试步骤、定义数据需求和预期结果。
license: MIT
compatibility: 需要组件知识卡片和LLM API调用
metadata:
  author: opencode
  version: "1.0"
---

根据用户输入和组件知识卡片，生成结构化测试用例。

---

## 输入格式

```json
{
  "user_input": "测试HDFS上数据经Spark计算后存储到HDFS的完整流程",
  "component_cards": [
    {
      "component_name": "HDFS",
      "core_concepts": [...],
      "test_scenarios": [...],
      "integration_points": [...]
    },
    {
      "component_name": "Spark",
      "core_concepts": [...],
      "test_scenarios": [...],
      "integration_points": [...]
    }
  ]
}
```

---

## 输出格式

### JSON格式 (测试用例)

```json
{
  "test_suite": {
    "suite_id": "TS_001",
    "suite_name": "HDFS-Spark集成测试",
    "description": "测试HDFS数据经Spark计算后存储的完整流程",
    "scenario_type": "integration",
    "components": ["HDFS", "Spark"],
    "data_flow": "HDFS读取 → Spark计算 → HDFS写入",
    "test_cases": [
      {
        "case_id": "TC_001",
        "case_name": "HDFS数据读取验证",
        "priority": "P1",
        "step": 1,
        "description": "验证从HDFS正确读取输入数据",
        "component": "HDFS",
        "operation": "读取",
        "api": "textFile",
        "input_data": {
          "type": "text_file",
          "path": "/test/input/data.txt",
          "size": "medium",
          "format": "CSV"
        },
        "expected_result": {
          "status": "success",
          "validation": "数据行数匹配预期",
          "metrics": ["读取耗时<5s", "无数据丢失"]
        },
        "preconditions": ["HDFS目录存在", "数据文件已准备"],
        "postconditions": ["数据加载到SparkRDD"]
      },
      {
        "case_id": "TC_002",
        "case_name": "Spark数据处理验证",
        "priority": "P1",
        "step": 2,
        "description": "验证Spark正确处理输入数据",
        "component": "Spark",
        "operation": "计算",
        "api": "map, reduceByKey",
        "input_data": {
          "type": "RDD",
          "source": "TC_001输出"
        },
        "expected_result": {
          "status": "success",
          "validation": "计算结果符合预期",
          "metrics": ["计算正确", "无异常"]
        },
        "preconditions": ["TC_001成功"],
        "postconditions": ["结果RDD可用"]
      },
      {
        "case_id": "TC_003",
        "case_name": "HDFS数据写入验证",
        "priority": "P1",
        "step": 3,
        "description": "验证结果正确写入HDFS",
        "component": "HDFS",
        "operation": "写入",
        "api": "saveAsTextFile",
        "input_data": {
          "type": "RDD",
          "source": "TC_002输出"
        },
        "output_data": {
          "path": "/test/output/result/",
          "format": "文本文件"
        },
        "expected_result": {
          "status": "success",
          "validation": "文件成功写入",
          "metrics": ["写入成功", "文件完整"]
        },
        "preconditions": ["TC_002成功", "输出目录存在"],
        "postconditions": ["结果文件可读"]
      },
      {
        "case_id": "TC_004",
        "case_name": "数据完整性验证",
        "priority": "P1",
        "step": 4,
        "description": "验证输入输出数据一致性",
        "component": "Spark/HDFS",
        "operation": "比对",
        "api": "count, collect",
        "input_data": {
          "input_path": "/test/input/data.txt",
          "output_path": "/test/output/result/"
        },
        "expected_result": {
          "status": "success",
          "validation": "数据完整一致",
          "metrics": ["输入输出行数一致", "计算结果正确"]
        },
        "preconditions": ["TC_003成功"],
        "postconditions": ["测试完成"]
      }
    ],
    "test_data_requirements": {
      "dataset_type": "custom",
      "description": "简单文本数据集，包含数值字段用于计算",
      "suggested_sources": [
        {"type": "public", "name": "Kaggle简单数据集"},
        {"type": "generated", "name": "Skill生成符合特征的测试数据"}
      ]
    },
    "environment_requirements": {
      "hdfs": {
        "nodes": 1,
        "version": "3.x"
      },
      "spark": {
        "mode": "local",
        "version": "4.x"
      }
    }
  }
}
```

---

## 测试用例生成规则（重要）

### 核心约束原则

**规则1：基于组件角色判断，不发散**
- 从组件卡片获取每个组件的角色能力（source/processor/sink）
- 基于角色序列验证数据流有效性
- 不添加用户未提及的组件

**规则2：组件角色分类**

| 角色 | 功能 | 操作类型 | 典型组件类型 |
|------|------|----------|--------------|
| **source** | 数据源 | read, consume, query | storage, streaming, database |
| **processor** | 数据处理 | compute, transform | compute, streaming |
| **sink** | 数据目标 | write, produce, insert | storage, streaming, database |
| **Local** | 特殊组件 | read, write | 默认可用，可替代source/sink |

**规则3：数据流有效性验证**

在生成组合用例前，必须先验证数据流有效性：

```
数据流模式          角色序列              有效性
---------------------------------------------------------
source -> processor -> sink    ✅ 有效（完整数据流）
source -> processor            ✅ 有效（读取处理）
processor -> sink              ✅ 有效（处理存储）
source -> sink                 ❌ 无效（缺少processor）
source -> source               ❌ 无效（同类型不能直接交互）
sink -> sink                   ❌ 无效（同类型不能直接交互）
processor -> processor         ✅ 有效（可链式处理）
```

---

### 用例分类体系

#### 1. 单组件功能用例

仅针对用户输入中涉及的组件，每个组件3-5个功能用例。

**生成规则：**
```
输入：用户涉及的组件列表
从组件卡片获取：supported_roles, key_operations

生成：每个组件的功能用例（基于其角色）
- source角色组件：read, list, query等操作测试
- processor角色组件：compute, transform等操作测试
- sink角色组件：write, create等操作测试

不生成：用户未提及组件的用例
```

#### 2. 多组件组合用例

**数据流验证流程：**

```
Step 1: 加载组件卡片，获取角色能力
  从每个组件卡片获取：
  - supported_roles: 该组件可扮演的角色
  - cannot_act_as: 该组件不能扮演的角色

Step 2: 将数据流转换为角色序列
  根据组件在数据流中的位置，确定其扮演的角色
  例如：A -> B -> A
  - 第一个A：source角色（提供数据）
  - B：processor角色（处理数据）
  - 第二个A：sink角色（接收数据）
  
  角色序列：source -> processor -> sink

Step 3: 验证角色序列有效性
  - 是否包含processor？
  - source和sink是否通过processor连接？
  - 是否存在同类型组件直接交互？
  
  如果无效，提示用户修正输入，不生成用例

Step 4: 生成组合用例
  - P1: 用户指定且角色序列有效的主场景
  - P2: Local替代source/sink的合理扩展
```

**有效数据流生成示例：**

```
用户输入："A数据经B处理后存入A"
（假设A是storage组件，B是compute组件）

Step 1: 获取角色能力
  A: supported_roles=["source", "sink"]
  B: supported_roles=["processor"]

Step 2: 角色序列
  A(source) -> B(processor) -> A(sink)
  序列：source -> processor -> sink

Step 3: 验证 ✅ 有效

Step 4: 生成用例
  P1: A -> B -> A（用户主场景）
  P2: Local -> B -> A（Local替代source）
  P2: A -> B -> Local（Local替代sink）
```

**无效数据流处理示例：**

```
用户输入："A数据直接写入B"
（假设A和B都是storage组件）

Step 1: 获取角色能力
  A: supported_roles=["source"]
  B: supported_roles=["sink"]

Step 2: 角色序列
  A(source) -> B(sink)
  序列：source -> sink

Step 3: 验证 ❌ 无效（缺少processor）

处理：
  - 提示用户：数据流无效，缺少processor组件
  - 建议修正：A -> processor -> B（需要添加compute组件）
  - 不生成用例
```

【禁止生成】规则：

❌ 用户未提及的组件：不生成涉及用户未提及组件的用例
❌ 角色序列无效：不生成数据流无效的用例
❌ 同类型直接交互：不生成source->source或sink->sink的用例

原因：确保用例可执行，避免环境兼容性问题
```

**组合场景决策表（抽象规则）：**

| 场景类型 | 决策依据 | 角色序列要求 | 是否生成 |
|----------|----------|--------------|----------|
| 用户明确指定 | 解析用户输入的数据流 | 必须符合有效角色序列 | ✅ P1 |
| Local合理补充 | Local替代source/sink | 替换后角色序列仍有效 | ✅ P2 |
| 未提及组件 | 用户未提及的组件 | - | ❌ 禁止 |
| 无效角色序列 | source->sink等 | - | ❌ 禁止 |

**典型用户输入与处理流程（抽象）：**

| 用户输入示例 | 解析组件 | 角色验证 | 生成用例 |
|--------------|----------|----------|----------|
| "测试A功能" | A | 获取A的角色能力 | A单组件用例 |
| "A数据经B处理" | A, B | A(source)->B(processor) ✅ | A+B单组件 + A->B组合 |
| "A数据经B处理后存入A" | A, B | A(source)->B(processor)->A(sink) ✅ | A+B单组件 + A->B->A组合 + Local扩展 |
| "A数据直接写入B" | A, B | A(source)->B(sink) ❌ | 提示用户修正 |
| "A数据经B处理后经C再处理存入D" | A,B,C,D | source->processor->processor->sink ✅ | 链式处理用例 |

#### 3. 容错场景用例

**基于组件角色生成容错用例（抽象规则）：**

| 组件角色 | 容错场景 | 用例模板 |
|----------|----------|----------|
| **source** | 数据源容错 | 读取不存在、空数据、权限错误、连接失败 |
| **processor** | 处理器容错 | 空数据处理、计算失败、内存溢出 |
| **sink** | 数据目标容错 | 写入失败、目录已存在、权限错误、空间不足 |

**生成规则：**
```
仅针对用户涉及的组件，基于其角色生成容错用例：

for component in user_components:
    roles = get_roles_from_card(component)
    
    if "source" in roles:
        generate: 读取不存在文件、空数据读取、权限错误
    
    if "processor" in roles:
        generate: 空数据处理、计算异常
    
    if "sink" in roles:
        generate: 写入失败、目录冲突、权限错误

不生成：用户未提及组件的容错用例
```

#### 4. 性能场景用例

**基于组件角色生成性能用例（抽象规则）：**

| 组件角色 | 性能场景 | 用例模板 |
|----------|----------|----------|
| **source** | 数据源性能 | 不同规模读取性能 |
| **processor** | 处理器性能 | 不同规模计算性能 |
| **sink** | 数据目标性能 | 不同规模写入性能 |

**生成规则：**
```
仅针对用户涉及的组件，基于其角色生成性能用例：

for component in user_components:
    roles = get_roles_from_card(component)
    
    if "source" in roles:
        generate: 小/中/大数据量读取性能
    
    if "processor" in roles:
        generate: 小/中/大数据量计算性能
    
    if "sink" in roles:
        generate: 小/中/大数据量写入性能

不生成：用户未提及组件的性能用例
```

---

## 完整用例生成Prompt模板（抽象规则版）

```markdown
你是测试用例设计专家。请根据以下信息生成测试用例：

## 用户需求
{user_input}

## 解析结果
{parsed_prompt}

## 组件知识卡片
{component_cards}

## 用例生成规则（抽象规则，基于角色判断）

### Step 1: 获取组件角色能力

从组件卡片获取每个组件的角色能力：
- supported_roles: 该组件可扮演的角色列表
- cannot_act_as: 该组件不能扮演的角色
- role_details: 每个角色的操作类型和API

### Step 2: 验证数据流有效性

根据用户输入的数据流，转换为角色序列：
- 确定每个组件在数据流中扮演的角色
- 验证角色序列是否符合有效模式

有效角色序列：
- source -> processor -> sink ✅
- source -> processor ✅
- processor -> sink ✅
- processor -> processor ✅（链式）

无效角色序列：
- source -> sink ❌（缺少processor）
- source -> source ❌（同类型不能直接交互）
- sink -> sink ❌（同类型不能直接交互）

如果数据流无效，提示用户修正，不生成用例。

### Step 3: 生成单组件功能用例

仅针对用户涉及的组件：
- 根据组件角色生成对应操作的功能用例
- source角色：读取、查询、连接等操作
- processor角色：计算、转换、聚合等操作
- sink角色：写入、创建、插入等操作

不生成用户未提及组件的用例。

### Step 4: 生成组合用例

根据有效角色序列生成组合用例：
- P1: 用户明确指定且角色序列有效的主场景
- P2: Local替代source/sink的合理扩展

不生成无效角色序列的用例。

### Step 5: 生成容错用例

仅针对用户涉及的组件，基于组件角色：
- source角色容错：读取不存在、空数据、权限错误
- processor角色容错：空数据处理、计算异常
- sink角色容错：写入失败、目录冲突、权限错误

### Step 6: 生成性能用例

仅针对用户涉及的组件，基于组件角色：
- source角色性能：不同规模读取性能
- processor角色性能：不同规模计算性能
- sink角色性能：不同规模写入性能

## 输出格式

{
  "test_suite": {
    "suite_id": "...",
    "components": ["仅用户涉及的组件"],
    "role_sequence_validation": {
      "sequence": "source -> processor -> sink",
      "valid": true/false,
      "reason": "..."
    },
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

## 组件角色查询示例

### 如何从组件卡片获取角色信息

```python
def get_component_roles(component_card: dict) -> dict:
    """
    从组件卡片获取角色能力
    
    Args:
        component_card: 组件知识卡片JSON
    
    Returns:
        {
            "component_name": "HDFS",
            "supported_roles": ["source", "sink"],
            "cannot_act_as": ["processor"],
            "role_details": {...}
        }
    """
    return {
        "component_name": component_card["component_name"],
        "supported_roles": component_card["component_roles"]["supported_roles"],
        "cannot_act_as": component_card["component_roles"]["cannot_act_as"],
        "role_details": component_card["component_roles"]["role_details"]
    }


def validate_data_flow(data_flow: list, component_cards: dict) -> dict:
    """
    验证数据流有效性
    
    Args:
        data_flow: ["HDFS", "Spark", "HDFS"]
        component_cards: {"HDFS": {...}, "Spark": {...}}
    
    Returns:
        {
            "role_sequence": "source -> processor -> sink",
            "valid": true,
            "reason": "完整数据流"
        }
        或
        {
            "role_sequence": "source -> sink",
            "valid": false,
            "reason": "缺少processor组件"
        }
    """
    role_sequence = []
    
    for i, component in enumerate(data_flow):
        card = component_cards[component]
        roles = card["component_roles"]["supported_roles"]
        
        # 根据位置确定角色
        if i == 0:  # 第一个组件：source
            if "source" in roles:
                role_sequence.append("source")
            else:
                return {"valid": False, "reason": f"{component}不能作为source"}
        
        elif i == len(data_flow) - 1:  # 最后一个组件：sink
            if "sink" in roles:
                role_sequence.append("sink")
            else:
                return {"valid": False, "reason": f"{component}不能作为sink"}
        
        else:  # 中间组件：processor
            if "processor" in roles:
                role_sequence.append("processor")
            else:
                return {"valid": False, "reason": f"{component}不能作为processor"}
    
    # 验证角色序列
    role_str = " -> ".join(role_sequence)
    
    if role_str == "source -> sink":
        return {"role_sequence": role_str, "valid": False, "reason": "缺少processor"}
    
    if "processor" not in role_sequence:
        return {"role_sequence": role_str, "valid": False, "reason": "必须包含processor"}
    
    return {"role_sequence": role_str, "valid": True, "reason": "有效数据流"}
```

---

## 典型场景处理示例

### 场景1：有效数据流

```
用户输入："A数据经B处理后存入A"

假设组件卡片：
- A: supported_roles=["source", "sink"], cannot_act_as=["processor"]
- B: supported_roles=["processor"], cannot_act_as=["source", "sink"]

处理流程：
1. 解析数据流：[A, B, A]
2. 确定角色：
   - 第一个A: source（提供数据）
   - B: processor（处理数据）
   - 第二个A: sink（接收数据）
3. 角色序列：source -> processor -> sink
4. 验证：✅ 有效
5. 生成用例：
   - P1: A -> B -> A
   - P2: Local -> B -> A
   - P2: A -> B -> Local
```

### 场景2：无效数据流

```
用户输入："A数据直接写入B"

假设组件卡片：
- A: supported_roles=["source", "sink"]
- B: supported_roles=["source", "sink"]

处理流程：
1. 解析数据流：[A, B]
2. 确定角色：
   - A: source（提供数据）
   - B: sink（接收数据）
3. 角色序列：source -> sink
4. 验证：❌ 无效（缺少processor）
5. 处理：
   - 提示用户：数据流无效，缺少processor组件
   - 建议修正：A -> processor组件 -> B
   - 不生成用例
```

### 场景3：组件角色不匹配

```
用户输入："A数据经B处理后存入C"

假设组件卡片：
- A: supported_roles=["source"]
- B: supported_roles=["source", "sink"], cannot_act_as=["processor"]（B是storage组件）
- C: supported_roles=["sink"]

处理流程：
1. 解析数据流：[A, B, C]
2. 确定角色：
   - A: source ✅
   - B: processor ❌（B不能作为processor）
3. 验证：❌ 无效（B不能作为processor）
4. 处理：
   - 提示用户：B是storage组件，不能作为processor
   - 建议修正：A -> compute组件 -> C
   - 不生成用例
```

---

## 完整测试用例JSON示例（抽象模板）

```json
{
  "test_suite": {
    "suite_id": "TS_001",
    "suite_name": "用户组件完整测试",
    "components": ["A", "B"],
    "role_sequence_validation": {
      "sequence": "source -> processor -> sink",
      "valid": true,
      "reason": "完整数据流"
    },
    "component_roles": {
      "A": {"roles": ["source", "sink"]},
      "B": {"roles": ["processor"]}
    },
    "test_cases": {
      "functional": [
        {
          "case_id": "TC_FUNC_001",
          "component": "A",
          "role": "source",
          "case_name": "A读取数据"
        },
        {
          "case_id": "TC_FUNC_002",
          "component": "A",
          "role": "sink",
          "case_name": "A写入数据"
        },
        {
          "case_id": "TC_FUNC_003",
          "component": "B",
          "role": "processor",
          "case_name": "B计算处理"
        }
      ],
      "integration": [
        {
          "case_id": "TC_INT_001",
          "data_flow": "A -> B -> A",
          "role_sequence": "source -> processor -> sink",
          "priority": "P1",
          "valid": true
        },
        {
          "case_id": "TC_INT_002",
          "data_flow": "Local -> B -> A",
          "role_sequence": "source -> processor -> sink",
          "priority": "P2",
          "valid": true
        }
      ],
      "fault_tolerance": [
        {
          "case_id": "TC_FT_001",
          "component": "A",
          "role": "source",
          "case_name": "A读取不存在数据"
        },
        {
          "case_id": "TC_FT_002",
          "component": "B",
          "role": "processor",
          "case_name": "B处理空数据"
        },
        {
          "case_id": "TC_FT_003",
          "component": "A",
          "role": "sink",
          "case_name": "A写入失败"
        }
      ],
      "performance": [
        {
          "case_id": "TC_PERF_001",
          "component": "A",
          "role": "source",
          "data_size": "small",
          "case_name": "A读取性能"
        },
        {
          "case_id": "TC_PERF_002",
          "component": "B",
          "role": "processor",
          "data_size": "medium",
          "case_name": "B计算性能"
        }
      ]
    }
  }
}
```

---

## Excel格式映射

JSON输出可转换为Excel表格：

| 用例ID | 类别 | 组件 | 角色 | 数据流 | 角色序列 | 优先级 |
|--------|------|------|------|--------|----------|--------|
| TC_FUNC_001 | functional | A | source | - | - | P1 |
| TC_FUNC_002 | functional | A | sink | - | - | P1 |
| TC_FUNC_003 | functional | B | processor | - | - | P1 |
| TC_INT_001 | integration | A,B | source,processor,sink | A->B->A | source->processor->sink | P1 |
| TC_INT_002 | integration | Local,B,A | source,processor,sink | Local->B->A | source->processor->sink | P2 |
| TC_FT_001 | fault_tolerance | A | source | - | - | P2 |
| TC_FT_002 | fault_tolerance | B | processor | - | - | P2 |
| TC_PERF_001 | performance | A | source | - | - | P3 |

## 完整用例生成Prompt模板（已在前文说明，此处简化）

参见前文"完整用例生成Prompt模板（抽象规则版）"部分。

---

## 完整测试用例JSON示例（抽象模板）

参见前文"完整测试用例JSON示例（抽象模板）"部分。

---

## 数据需求配置

```json
{
  "data_requirements": {
    "small": {"rows": 100, "size": "10KB", "purpose": "功能测试"},
    "medium": {"rows": 100000, "size": "10MB", "purpose": "集成测试"},
    "large": {"rows": 1000000, "size": "100MB", "purpose": "性能测试"}
  }
}
```

---

## 环境需求配置

```json
{
  "environment_requirements": {
    "components": ["用户涉及的组件"],
    "config": "根据组件卡片的环境需求配置"
  }
}
```

---

## 输出文件路径

```
./output/test_cases.json
```

---

## 完整输出结构

```json
{
  "test_suite": {
    "suite_id": "TS_001",
    "suite_name": "用户组件完整测试",
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success|error",
    "errors": [],
    
    "input_source": "./output/parsed_prompt.json",
    "component_cards_used": ["HDFS_CARD.json", "SPARK_CARD.json"],
    
    "components": ["A", "B"],
    "role_sequence_validation": {
      "sequence": "source -> processor -> sink",
      "valid": true,
      "reason": "完整数据流"
    },
    "component_roles": {
      "A": {"roles": ["source", "sink"]},
      "B": {"roles": ["processor"]}
    },
    
    "test_case_summary": {
      "functional_count": 3,
      "integration_count": 2,
      "fault_tolerance_count": 3,
      "performance_count": 2,
      "total_count": 10
    },
    
    "test_cases": {
      "functional": [...],
      "integration": [...],
      "fault_tolerance": [...],
      "performance": [...]
    },
    
    "data_requirements": {
      "input_data": {"type": "CSV", "rows": 100000},
      "expected_output": {"type": "CSV", "rows": 50}
    },
    
    "environment_requirements": {
      "components": ["A", "B"],
      "config": {...}
    }
  },
  
  "output": {
    "path": "./output/test_cases.json",
    "format": "json",
    "excel_path": "./output/test_cases.xlsx"
  },
  
  "next_skill": {
    "name": "data-generator",
    "reason": "根据测试用例生成测试数据",
    "input_from": "./output/test_cases.json"
  }
}
```

---

## 执行状态说明

| 状态 | 说明 | 后续操作 |
|------|------|----------|
| `success` | 数据流验证通过，测试用例生成完成 | 调用 data-generator |
| `error_invalid_flow` | 数据流无效（缺少processor） | 提示用户修正输入 |
| `error_role_mismatch` | 组件角色不匹配 | 提示用户更换组件 |
| `error_missing_cards` | 组件卡片缺失 | 先调用 component-card-generator |