---
name: skills-orchestration
description: Skills串联架构和工作流程说明。包含完整执行流程、自动调度逻辑、输入输出传递关系。
---

# Skills串联架构

## 总体架构图

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         Skills自动化流水线                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  用户输入: "测试A数据经B处理后存入C"                                            │
│       │                                                                        │
│       ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                      主控制器 (Orchestrator)                             │  │
│  │                                                                         │  │
│  │  功能:                                                                   │  │
│  │  1. 接收用户输入                                                         │  │
│  │  2. 调度各Skill执行                                                      │  │
│  │  3. 管理中间结果传递                                                      │  │
│  │  4. 处理异常和回退                                                       │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                        │
│       │ 调度执行                                                               │
│       ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         执行流程                                         │  │
│  │                                                                         │  │
│  │  Step 1: input-parser                                                   │  │
│  │  ├─ 输入: 用户自然语言                                                   │  │
│  │  ├─ 输出: parsed_prompt.json                                            │  │
│  │  └─ 作用: 解析组件、识别角色、验证数据流                                  │  │
│  │                                                                         │  │
│  │  Step 2: card-fetcher (内置逻辑，非独立Skill)                            │  │
│  │  ├─ 输入: parsed_prompt.json                                            │  │
│  │  ├─ 输出: component_cards                                               │  │
│  │  └─ 逻辑:                                                                │  │
│  │     ├── 检查卡片是否存在                                                 │  │
│  │     ├── 存在 → 直接获取                                                  │  │
│  │     └─ 不存在 → 调用 component-card-generator                            │  │
│  │                                                                         │  │
│  │  Step 3: scenario-planner                                               │  │
│  │  ├─ 输入: parsed_prompt.json + component_cards                          │  │
│  │  ├─ 输出: test_cases.json                                               │  │
│  │  └─ 作用: 基于角色验证数据流，生成测试用例                                │  │
│  │                                                                         │  │
│  │  Step 4: data-generator                                                 │  │
│  │  ├─ 输入: test_cases.json                                               │  │
│  │  ├─ 输出: data_manifest.json + 数据文件                                  │  │
│  │  └─ 作用: 生成测试数据（公开数据集优先）                                  │  │
│  │                                                                         │  │
│  │  Step 5: test-script-generator                                          │  │
│  │  ├─ 输入: test_cases.json + data_manifest.json + component_cards        │  │
│  │  ├─ 输出: pytest脚本 + conftest.py                                      │  │
│  │  └─ 作用: 生成可执行测试脚本                                              │  │
│  │                                                                         │  │
│  │  Step 6: env-config-generator                                           │  │
│  │  ├─ 输入: test_cases.json + component_cards                             │  │
│  │  ├─ 输出: docker-compose.yaml + 配置文件                                │  │
│  │  └─ 作用: 生成测试环境配置                                                │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│       │                                                                        │
│       ▼                                                                        │
│  输出结果:                                                                     │
│  ├─ 测试用例 (JSON + Excel)                                                   │
│  ├─ 测试数据 (CSV/JSON)                                                        │
│  ├─ 测试脚本 (pytest)                                                          │
│  ├─ 环境配置 (docker-compose)                                                  │
│  └─ 知识卡片 (JSON + MD + Excel)                                              │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细执行流程

### Step 1: input-parser

```
输入: 用户自然语言
    例如: "测试A数据经B处理后存入C"

处理逻辑:
    1. 场景类型识别 (functional/integration/fault_tolerance/performance)
    2. 组件识别 (关键词匹配)
    3. 角色确定 (根据组件类型和位置)
    4. 数据流解析 (组件调用顺序)
    5. 数据流验证 (基于角色序列)

输出: parsed_prompt.json
    {
      "original_input": "测试A数据经B处理后存入C",
      "parsed_elements": {
        "components": [
          {"name": "A", "role": "source"},
          {"name": "B", "role": "processor"},
          {"name": "C", "role": "sink"}
        ],
        "role_sequence": "source -> processor -> sink",
        "scenario_type": "integration"
      },
      "validation": {
        "valid": true,
        "reason": "完整数据流"
      },
      "component_cards_needed": ["A_CARD.json", "B_CARD.json", "C_CARD.json"]
    }
```

### Step 2: card-fetcher（内置逻辑）

```
输入: parsed_prompt.json

处理逻辑:
    1. 获取组件列表: ["A", "B", "C"]
    2. 检查卡片存在性:
        for component in components:
            if card_exists(component):
                fetch_card(component)
            else:
                call_skill("component-card-generator", component)
                wait_for_card_generation()
                fetch_card(component)

输出: component_cards
    {
      "A": {...},  // A_CARD.json内容
      "B": {...},  // B_CARD.json内容
      "C": {...}   // C_CARD.json内容
    }

异常处理:
    - 如果卡片生成失败: 报告错误，停止流程
```

### Step 3: scenario-planner

```
输入: parsed_prompt.json + component_cards

处理逻辑:
    1. 加载组件角色能力 (从component_cards获取)
    2. 再次验证数据流有效性 (基于component_roles)
    3. 如果无效: 返回错误提示，停止流程
    4. 如果有效:
        - 生成单组件功能用例 (每个组件3-5个)
        - 生成组合用例 (基于角色序列)
        - 生成容错用例 (基于组件角色)
        - 生成性能用例 (基于组件角色)

输出: test_cases.json
    {
      "test_suite": {
        "components": ["A", "B", "C"],
        "role_sequence_validation": {
          "sequence": "source -> processor -> sink",
          "valid": true
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

### Step 4: data-generator

```
输入: test_cases.json

处理逻辑:
    1. 分析数据需求 (从test_cases.data_requirements获取)
    2. 选择数据策略:
        - 匹配公开数据集 → 下载脚本
        - 不匹配 → Skill生成脚本
    3. 生成数据文件
    4. 生成预期输出 (可选)

输出: data_manifest.json
    {
      "data_files": [
        {
          "path": "./test_data/input_data.csv",
          "type": "input",
          "rows": 100000
        },
        {
          "path": "./test_data/expected_output.csv",
          "type": "expected_output",
          "rows": 50
        }
      ],
      "download_scripts": [...],
      "generation_scripts": [...]
    }

关键: 数据必须在脚本生成前准备好！
```

### Step 5: test-script-generator

```
输入: test_cases.json + data_manifest.json + component_cards

处理逻辑:
    1. 读取测试用例
    2. 读取数据路径
    3. 读取组件API
    4. 生成pytest脚本:
        - conftest.py (fixtures)
        - test_integration.py (组合用例)
        - test_unit.py (单组件用例)
        - test_fault_tolerance.py (容错用例)
        - test_performance.py (性能用例)

输出: 测试脚本文件
    tests/
    ├── conftest.py
    ├── test_integration.py
    ├── test_unit.py
    └── ...
```

### Step 6: env-config-generator

```
输入: test_cases.json + component_cards

处理逻辑:
    1. 读取组件列表
    2. 读取组件环境需求
    3. 生成docker-compose (仅包含用户涉及的组件)
    4. 生成组件配置文件
    5. 生成部署脚本

输出: 环境配置文件
    environment/
    ├── docker-compose.yaml
    ├── config/
    │   ├── {component_1}/
    │   └── {component_2}/
    ├── scripts/
    └── test_config.yaml
```

---

## 输入输出传递关系

```
┌─────────────────────────────────────────────────────────────────┐
│                     Skills输入输出传递                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入                                                        │
│      │                                                          │
│      ▼                                                          │
│  input-parser                                                   │
│      │                                                          │
│      ├─→ parsed_prompt.json ──────────────────────────────────┐│
│      │                                                        ││
│      ▼                                                        ││
│  card-fetcher                                                  ││
│      │                                                        ││
│      ├─→ component_cards ─────────────────────────────────────┤│
│      │                                                        ││
│      ▼                                                        ││
│  scenario-planner                                              ││
│      │                                                        ││
│      ├─→ test_cases.json ─────────────────────────────────────┤│
│      │                                                        ││
│      ▼                                                        ││
│  data-generator                                                ││
│      │                                                        ││
│      ├─→ data_manifest.json ──────────────────────────────────┤│
│      │                                                        ││
│      ▼                                                        ││
│  test-script-generator                                         ││
│      │                                                        ││
│      ├─→ pytest scripts                                        ││
│      │                                                        ││
│      ▼                                                        ││
│  env-config-generator                                          ││
│      │                                                        ││
│      ├─→ docker-compose.yaml                                   ││
│      │                                                        ││
│      ▼                                                        ││
│  测试环境就绪                                                   ││
│                                                                 │
│  输入传递总结:                                                  │
│  - parsed_prompt.json → scenario-planner                       │
│  - component_cards → scenario-planner                          │
│  - test_cases.json → data-generator                            │
│  - test_cases.json → test-script-generator                     │
│  - data_manifest.json → test-script-generator                  │
│  - component_cards → test-script-generator                     │
│  - test_cases.json → env-config-generator                      │
│  - component_cards → env-config-generator                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 自动调度逻辑

### 主控制器 (Orchestrator)

```python
class SkillOrchestrator:
    """Skills调度控制器"""
    
    def __init__(self):
        self.skills = {
            "input-parser": InputParserSkill(),
            "component-card-generator": ComponentCardGeneratorSkill(),
            "scenario-planner": ScenarioPlannerSkill(),
            "data-generator": DataGeneratorSkill(),
            "test-script-generator": TestScriptGeneratorSkill(),
            "env-config-generator": EnvConfigGeneratorSkill()
        }
        self.card_index = CardIndex()
    
    def run(self, user_input: str) -> dict:
        """
        执行完整流程
        
        Args:
            user_input: 用户自然语言输入
        
        Returns:
            {
                "status": "success|error",
                "results": {
                    "parsed_prompt": {...},
                    "component_cards": {...},
                    "test_cases": {...},
                    "data_manifest": {...},
                    "scripts": [...],
                    "env_config": {...}
                },
                "output_files": {
                    "test_cases_excel": "...",
                    "pytest_scripts": "...",
                    "docker_compose": "..."
                }
            }
        """
        results = {}
        
        # Step 1: input-parser
        parsed_prompt = self.skills["input-parser"].execute(user_input)
        results["parsed_prompt"] = parsed_prompt
        
        # 验证数据流有效性
        if not parsed_prompt["validation"]["valid"]:
            return {
                "status": "error",
                "error": parsed_prompt["validation"]["reason"],
                "suggestion": "请添加processor组件"
            }
        
        # Step 2: card-fetcher
        component_cards = self.fetch_cards(parsed_prompt["component_cards_needed"])
        results["component_cards"] = component_cards
        
        # Step 3: scenario-planner
        test_cases = self.skills["scenario-planner"].execute(
            parsed_prompt=parsed_prompt,
            component_cards=component_cards
        )
        results["test_cases"] = test_cases
        
        # Step 4: data-generator
        data_manifest = self.skills["data-generator"].execute(
            test_cases=test_cases
        )
        results["data_manifest"] = data_manifest
        
        # Step 5: test-script-generator
        scripts = self.skills["test-script-generator"].execute(
            test_cases=test_cases,
            data_manifest=data_manifest,
            component_cards=component_cards
        )
        results["scripts"] = scripts
        
        # Step 6: env-config-generator
        env_config = self.skills["env-config-generator"].execute(
            test_cases=test_cases,
            component_cards=component_cards
        )
        results["env_config"] = env_config
        
        # 生成输出文件
        output_files = self.generate_output_files(results)
        
        return {
            "status": "success",
            "results": results,
            "output_files": output_files
        }
    
    def fetch_cards(self, card_names: list) -> dict:
        """获取或生成组件卡片"""
        cards = {}
        
        for card_name in card_names:
            component = card_name.replace("_CARD.json", "")
            
            # 检查卡片是否存在
            if self.card_index.exists(component):
                # 直接获取
                cards[component] = self.card_index.fetch(component)
            else:
                # 调用component-card-generator生成
                card = self.skills["component-card-generator"].execute(component)
                cards[component] = card
                
                # 更新索引
                self.card_index.register(component, card)
        
        return cards
    
    def generate_output_files(self, results: dict) -> dict:
        """生成最终输出文件"""
        output_files = {}
        
        # 生成Excel测试用例
        output_files["test_cases_excel"] = self.to_excel(
            results["test_cases"]
        )
        
        # 生成pytest脚本
        output_files["pytest_scripts"] = results["scripts"]
        
        # 生成docker-compose
        output_files["docker_compose"] = results["env_config"]["docker_compose"]
        
        return output_files
```

---

## 调用入口

### 方式1: 命令行

```bash
# 执行完整流程
python orchestrator.py "测试A数据经B处理后存入C"

# 输出
测试用例已生成: ./output/test_cases.xlsx
测试脚本已生成: ./tests/test_integration.py
环境配置已生成: ./environment/docker-compose.yaml
```

### 方式2: Python API

```python
from orchestrator import SkillOrchestrator

orchestrator = SkillOrchestrator()

# 执行流程
result = orchestrator.run("测试A数据经B处理后存入C")

# 检查结果
if result["status"] == "success":
    print("测试用例:", result["output_files"]["test_cases_excel"])
    print("测试脚本:", result["output_files"]["pytest_scripts"])
    print("环境配置:", result["output_files"]["docker_compose"])
else:
    print("错误:", result["error"])
    print("建议:", result["suggestion"])
```

### 方式3: Web界面

```
用户在Web界面输入:
┌─────────────────────────────────────────────────────────────┐
│  请输入测试需求:                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 测试A数据经B处理后存入C                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  [生成测试用例]                                              │
└─────────────────────────────────────────────────────────────┘

点击后自动调用orchestrator，显示进度:
┌─────────────────────────────────────────────────────────────┐
│  执行进度:                                                   │
│  ✅ Step 1: input-parser 完成                               │
│  ✅ Step 2: 获取组件卡片 完成                                │
│  ✅ Step 3: scenario-planner 完成                           │
│  ✅ Step 4: data-generator 完成                             │
│  ✅ Step 5: test-script-generator 完成                      │
│  ✅ Step 6: env-config-generator 完成                       │
│                                                              │
│  [下载测试用例Excel] [下载测试脚本] [下载环境配置]           │
└─────────────────────────────────────────────────────────────┘
```

---

## 异常处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                     异常处理策略                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  异常类型 1: 数据流无效                                      │
│  ├─ 检测点: input-parser 或 scenario-planner                │
│  ├─ 处理: 返回错误提示                                       │
│  ├─ 建议: "请添加processor组件"                             │
│  └─ 动作: 停止流程，等待用户修正输入                         │
│                                                             │
│  异常类型 2: 组件卡片不存在                                  │
│  ├─ 检测点: card-fetcher                                    │
│  ├─ 处理: 调用 component-card-generator                     │
│  ├─ 失败: 报告生成失败                                       │
│  └─ 动作: 停止流程，等待手动处理                             │
│                                                             │
│  异常类型 3: 组件角色不匹配                                  │
│  ├─ 检测点: scenario-planner                                │
│  ├─ 检测: 组件不能扮演指定角色                               │
│  ├─ 处理: 返回错误提示                                       │
│  └─ 建议: "A不能作为processor，请使用compute组件"           │
│                                                             │
│  异常类型 4: 数据生成失败                                    │
│  ├─ 检测点: data-generator                                  │
│  ├─ 处理: 尝试备用数据集                                     │
│  ├─ 失败: 使用Skill生成                                     │
│  └─ 最终失败: 报告错误                                       │
│                                                             │
│  异常类型 5: LLM API调用失败                                 │
│  ├─ 检测点: 所有依赖LLM的Skills                             │
│  ├─ 处理: 重试机制 (3次)                                    │
│  ├─ 失败: 使用备用API                                       │
│  └─ 最终失败: 报告错误                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 流程优化

### 并行执行

```
可并行执行的步骤:

Step 1完成后，以下可并行:
├─ Step 2: card-fetcher (多个组件卡片可并行获取/生成)
├─ Step 3: scenario-planner (依赖Step 2完成)
└─ Step 2和Step 3顺序执行

Step 3完成后，以下可并行:
├─ Step 4: data-generator
├─ Step 5: test-script-generator (需要等待Step 4完成)
└─ Step 6: env-config-generator (可与Step 4、5并行)

优化流程:
┌────────────────────────────────────────┐
│ Step 1: input-parser                   │
└────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ Step 2: card-fetcher                   │
└────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ Step 3: scenario-planner               │
└────────────────────────────────────────┘
              │
              ├──────────────┬─────────────
              ▼              ▼             ▼
┌───────────────┐ ┌─────────────────┐ ┌───────────────┐
│ Step 4        │ │ Step 5          │ │ Step 6        │
│ data-generator│ │ (等待Step 4)    │ │ env-config    │
└───────────────┘ └─────────────────┘ └───────────────┘
              │              │             │
              └──────────────┴─────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │ 输出完成    │
                      └─────────────┘
```

---

## 执行日志

每次执行生成日志记录:

```json
{
  "execution_id": "exec_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_input": "测试A数据经B处理后存入C",
  "steps": [
    {
      "step": 1,
      "skill": "input-parser",
      "duration_ms": 500,
      "status": "success",
      "output": "parsed_prompt.json"
    },
    {
      "step": 2,
      "skill": "card-fetcher",
      "duration_ms": 2000,
      "status": "success",
      "output": "component_cards",
      "details": {
        "cards_found": ["A_CARD.json"],
        "cards_generated": ["B_CARD.json", "C_CARD.json"]
      }
    },
    {
      "step": 3,
      "skill": "scenario-planner",
      "duration_ms": 3000,
      "status": "success",
      "output": "test_cases.json"
    },
    {
      "step": 4,
      "skill": "data-generator",
      "duration_ms": 5000,
      "status": "success",
      "output": "data_manifest.json"
    },
    {
      "step": 5,
      "skill": "test-script-generator",
      "duration_ms": 4000,
      "status": "success",
      "output": "pytest scripts"
    },
    {
      "step": 6,
      "skill": "env-config-generator",
      "duration_ms": 2000,
      "status": "success",
      "output": "docker-compose.yaml"
    }
  ],
  "total_duration_ms": 14500,
  "final_status": "success",
  "output_files": [
    "./output/test_cases.xlsx",
    "./tests/test_integration.py",
    "./environment/docker-compose.yaml"
  ]
}