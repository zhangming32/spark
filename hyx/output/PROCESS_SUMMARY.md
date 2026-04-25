# 测试生成流程说明文档

## 任务概述

**用户输入**: "测试HDFS数据经过spark计算后存入HDFS"

**生成时间**: 2026-04-24T19:05:00Z
**最后更新**: 2026-04-25T10:30:00Z (质量改进完成)

---

## 执行流程

### Step 1: input-parser (输入解析)

**输入**: 用户自然语言描述

**输出**: `./output/parsed_prompt.json`

**解析结果**:
- **场景类型**: integration (集成测试)
- **组件**: HDFS(source) -> Spark(processor) -> HDFS(sink)
- **数据流验证**: ✅ 有效 (完整数据流，包含processor)
- **测试覆盖**: 单组件+组合+容错+性能

---

### Step 2: component-card-generator (组件知识卡片生成)

**输入**: parsed_prompt.json中的组件列表

**输出**: 
- `./output/knowledge_cards/json/HDFS_CARD.json`
- `./output/knowledge_cards/json/SPARK_CARD.json`

**卡片内容**:

| 组件 | 类型 | 可扮演角色 | 不能扮演 |
|------|------|-----------|---------|
| HDFS | storage | source, sink | processor |
| Spark | compute | processor | source, sink |

---

### Step 3: scenario-planner (测试用例生成)

**输入**: parsed_prompt.json + 组件卡片

**输出**: `./output/test_cases.json`

**测试用例统计**:

| 类别 | 数量 | 说明 |
|------|------|------|
| functional | 5 | 单组件功能测试 |
| integration | 4 | 多组件组合测试 |
| fault_tolerance | 5 | 容错场景测试 |
| performance | 4 | 性能测试 |
| **总计** | **18** | 全部测试用例 |

---

### Step 4: data-generator (测试数据生成)

**输入**: test_cases.json

**输出**: `./output/data_manifest.json` + 测试数据文件

**生成的测试数据**:

| 文件 | 路径 | 行数 | 用途 |
|------|------|------|------|
| data_small.csv | ./test_data/input/ | 100 | 功能测试、容错测试 |
| data_medium.csv | ./test_data/input/ | 100000 | 集成测试 |
| data_boundary.csv | ./test_data/input/ | 13 | 边界值测试 |
| empty.csv | ./test_data/input/ | 0 | 容错测试 |
| expected_aggregation.csv | ./test_data/expected/ | 10 | 结果验证 |

**数据schema**:
- id: integer
- category: string (A-J共10类) ✅ 已修正
- value: double (0-1000)

**质量改进**:
- ✅ data_small.csv: category已修正为A-J
- ✅ data_medium.csv: category已修正为A-J (原为0-9数字)
- ✅ data_boundary.csv: 新增边界值+null值数据
- ✅ expected_aggregation.csv: 补充精确预期值

---

### Step 5: test-script-generator (测试脚本生成)

**输入**: test_cases.json + data_manifest.json + 组件卡片

**输出**: `./output/test_scripts_manifest.json` + 测试脚本文件

**生成的测试文件**:

| 文件 | 路径 | 说明 |
|------|------|------|
| conftest.py | ./tests/ | pytest配置和fixtures (v2版本) |
| test_integration.py | ./tests/ | 集成测试脚本(18个测试方法) |
| test_config.yaml | ./tests/config/ | 测试环境配置 |
| pytest.ini | ./tests/ | pytest运行配置 |
| requirements.txt | ./tests/ | Python依赖 |

**质量改进**:
- ✅ 测试方法从10个增加到18个
- ✅ 新增边界值测试(boundary marker)
- ✅ 新增数值验证逻辑(assert精确值)
- ✅ 新增benchmark fixture

---

### Step 6: env-config-generator (环境配置生成)

**输入**: test_cases.json

**输出**: `./output/docker-compose.yaml`

**环境组件**:
- Spark Master (端口8080, 7077)
- Spark Worker (端口8081)
- HDFS (需单独部署或使用现有集群)

---

## 文件结构

```
./output/
├── parsed_prompt.json          # Step 1: 解析结果
├── test_cases.json             # Step 3: 测试用例
├── data_manifest.json          # Step 4: 数据清单
├── test_scripts_manifest.json  # Step 5: 脚本清单
├── docker-compose.yaml         # Step 6: 环境配置
├── knowledge_cards/
│   └── json/
│       ├── HDFS_CARD.json      # HDFS知识卡片
│       └── SPARK_CARD.json     # Spark知识卡片
└── PROCESS_SUMMARY.md          # 本说明文档

./test_data/
├── input/
│   ├── data_small.csv          # 小规模测试数据(100行, category A-J)
│   ├── data_medium.csv         # 中规模测试数据(100000行, category A-J)
│   ├── data_boundary.csv       # 边界值测试数据(13行)
│   └── empty.csv               # 空文件
├── expected/
│   └ expected_aggregation.csv  # 预期聚合结果
└── scripts/
    └ generate_test_data.py     # 数据生成脚本

./tests/
├── conftest.py                 # pytest配置
├── test_integration.py         # 集成测试
├── pytest.ini                  # pytest配置
├── requirements.txt            # 依赖包
└── config/
    └ test_config.yaml          # 测试配置
```

---

## 运行测试

### 1. 安装依赖

```bash
pip install -r tests/requirements.txt
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行P1优先级测试
pytest tests/ -v -m P1

# 运行集成测试
pytest tests/ -v -m integration

# 运行容错测试
pytest tests/ -v -m fault_tolerance
```

### 3. 运行性能测试

```bash
pytest tests/ -v -m performance
```

---

## Skills调用记录

| Step | Skill | 状态 | 输出文件 |
|------|-------|------|----------|
| 1 | input-parser | ✅ 成功 | parsed_prompt.json |
| 2 | component-card-generator | ✅ 成功 | HDFS_CARD.json, SPARK_CARD.json |
| 3 | scenario-planner | ✅ 成功 | test_cases.json |
| 4 | data-generator | ✅ 成功 | data_manifest.json + 数据文件 |
| 5 | test-script-generator | ✅ 成功 | test_integration.py 等 |
| 6 | env-config-generator | ✅ 成功 | docker-compose.yaml |
| 7 | 质量改进 | ✅ 完成 | 修正category、完善测试、增强卡片 |

---

## 组件角色验证

**数据流**: HDFS -> Spark -> HDFS

**角色序列**: source -> processor -> sink

**验证结果**: ✅ 有效

**验证规则**:
- source和sink之间必须有processor连接
- 同类型组件不能直接交互
- HDFS(storage)可扮演source和sink
- Spark(compute)可扮演processor

---

## 测试用例示例

### TC_INT_001: HDFS->Spark->HDFS完整流程

```python
def test_full_pipeline(self, spark_session, test_data_paths):
    # Step 1: 读取数据
    df = spark_session.read.csv(input_path)
    
    # Step 2: 聚合计算
    result = df.groupBy("category").agg(count("*"), sum("value"))
    
    # Step 3: 写入结果
    result.write.csv(output_path)
    
    # Step 4: 验证结果
    assert os.path.exists(output_path)
```

---

## 后续操作

1. **运行测试**: `pytest tests/ -v`
2. **检查覆盖率**: 添加更多测试场景
3. **扩展用例**: 根据实际需求调整test_cases.json
4. **部署环境**: 使用docker-compose.yaml启动Spark集群

---

## 关键文件说明

### parsed_prompt.json
- 包含用户输入的解析结果
- 定义组件、角色、数据流

### test_cases.json
- 包含所有测试用例定义
- 分为functional/integration/fault_tolerance/performance四类

### HDFS_CARD.json / SPARK_CARD.json
- 组件知识卡片
- 定义组件角色、API、交互规则

### data_manifest.json
- 测试数据清单
- 定义数据文件路径、schema、用途

---

## 恢复记忆

如果窗口断开，可按以下步骤恢复：

1. **读取本文档**: `./output/PROCESS_SUMMARY.md`
2. **查看文件结构**: 检查./output/目录下所有JSON文件
3. **继续执行**: 从断开点继续调用相应skill

**关键文件优先级**:
- P0: parsed_prompt.json (输入解析结果)
- P0: test_cases.json (测试用例定义)
- P1: 组件卡片 (HDFS_CARD.json, SPARK_CARD.json)
- P1: data_manifest.json (数据清单)
- P2: 测试脚本 (tests/*.py)

---

---

## 质量改进记录 (2026-04-25)

### 问题发现
1. ❌ data_medium.csv的category字段为数字(0-9)而非字母(A-J)
2. ❌ 测试用例缺少具体的expected_values
3. ❌ 测试脚本覆盖率不足(18用例只实现10个)
4. ❌ 验证逻辑不完整(只验证行数，不验证数值)
5. ❌ 知识卡片缺少common_issues、error_codes字段

### 改进措施
1. ✅ 修正data_medium.csv，category改为A-J字母
2. ✅ 新增data_boundary.csv，包含边界值和null值
3. ✅ 补充expected_aggregation.csv精确数据
4. ✅ 完善测试用例定义，新增boundary类别
5. ✅ 完善测试脚本，从10个增加到18个测试方法
6. ✅ 增加数值验证逻辑，断言精确值
7. ✅ 知识卡片新增common_issues、error_codes字段

### 验证状态
- ⏳ 测试执行验证: 待运行
- ✅ 数据格式验证: 已通过
- ✅ 脚本语法验证: 已通过
- ✅ 知识卡片结构验证: 已通过

---

**文档生成**: 2026-04-24T19:05:00Z
**最后更新**: 2026-04-25T10:30:00Z
**流程状态**: ✅ 全部完成 + 质量改进完成