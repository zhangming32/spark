---
name: test-script-generator
description: 根据测试用例和测试数据生成可执行的pytest测试脚本。数据路径由data-generator提供，脚本生成在数据准备之后。
license: MIT
metadata:
  author: opencode
  version: "1.0"
---

根据测试用例和测试数据生成可执行的pytest测试脚本，数据必须在脚本生成前准备好。

---

## 执行顺序（关键）

```
1. scenario-planner    → 输出: test_cases.json
2. data-generator      → 输出: data_manifest.json (数据路径)
3. test-script-generator (本Skill) → 输出: test_*.py
```

**脚本生成时需要数据路径，因此数据必须先准备好。**

---

## 输入

### 1. 测试用例JSON（抽象模板）

```json
{
  "test_suite_id": "TS_001",
  "test_cases": [
    {
      "test_case_id": "TC_001",
      "name": "{source_component}_Read_{processor_component}_Process_{sink_component}_Write",
      "type": "integration",
      "priority": "P1",
      "components": ["{source_component}", "{processor_component}", "{sink_component}"],
      "scenario": {
        "description": "从{source}读取数据，{processor}进行处理，写入{sink}",
        "data_flow": ["{source}.read", "{processor}.compute", "{sink}.write"]
      },
      "steps": [
        {
          "step_id": 1,
          "action": "read_from_{source}",
          "component": "{source_component}",
          "params": {
            "path": "${input_path}",
            "format": "CSV"
          }
        },
        {
          "step_id": 2,
          "action": "process_with_{processor}",
          "component": "{processor_component}",
          "params": {
            "operation": "groupBy_count",
            "group_by": "category",
            "aggregate": "count"
          }
        },
        {
          "step_id": 3,
          "action": "write_to_{sink}",
          "component": "{sink_component}",
          "params": {
            "path": "${output_path}",
            "format": "CSV"
          }
        }
      ],
      "assertions": [
        {
          "type": "row_count_match",
          "expected": "expected_output.csv"
        },
        {
          "type": "data_content_match",
          "tolerance": 0.001
        }
      ]
    }
  ]
}
```

### 2. 数据清单JSON

```json
{
  "data_manifest_id": "DM_001",
  "data_files": [
    {
      "file_id": "DF_001",
      "path": "./test_data/processed/input_data.csv",
      "type": "input"
    },
    {
      "file_id": "DF_002",
      "path": "./test_data/processed/expected_output.csv",
      "type": "expected_output"
    }
  ]
}
```

### 3. 组件知识卡片

```json
{
  "component_name": "{component}",
  "api_reference": {
    "read_csv": "{component}.read.csv(path)",
    "write_csv": "{component}.write.csv(path)",
    "groupBy": "{component}.groupBy(col).agg(...)"
  }
}
```

---

## 输出

### 输出文件路径
```
./tests/
./output/test_scripts_manifest.json
```

### 测试脚本结构（通用模板）

```
tests/
├── conftest.py                   # pytest配置和fixtures
├── test_{components}_integration.py # 集成测试（根据组件动态命名）
├── test_{component_1}_unit.py    # 单组件测试
├── test_{component_2}_unit.py    # 单组件测试
├── test_{components}_fault_tolerance.py # 容错测试
├── test_{components}_performance.py # 性能测试
├── fixtures/                     # 测试fixtures
│   ├── {component_1}_fixtures.py
│   └── {component_2}_fixtures.py
├── utils/                        # 工具函数
│   ├── {component_1}_utils.py
│   ├── {component_2}_utils.py
│   └── data_utils.py
├── config/                       # 测试配置
│   └── test_config.yaml
├── pytest.ini                    # pytest配置
└── requirements.txt              # 依赖包
```

### 输出清单JSON结构

```json
{
  "scripts_manifest_id": "SM_001",
  "generation_timestamp": "2024-01-15T10:30:00Z",
  "status": "success|error",
  "errors": [],
  
  "input_sources": {
    "test_cases": "./output/test_cases.json",
    "data_manifest": "./output/data_manifest.json",
    "component_cards": ["HDFS_CARD.json", "SPARK_CARD.json"]
  },
  
  "generated_files": [
    {
      "file_id": "SF_001",
      "path": "./tests/conftest.py",
      "type": "config",
      "description": "pytest配置和fixtures",
      "size_estimate": "5KB"
    },
    {
      "file_id": "SF_002",
      "path": "./tests/test_integration.py",
      "type": "test",
      "test_count": 4,
      "description": "集成测试主场景",
      "priority": "P1"
    },
    {
      "file_id": "SF_003",
      "path": "./tests/test_unit.py",
      "type": "test",
      "test_count": 6,
      "description": "单组件功能测试",
      "priority": "P1"
    },
    {
      "file_id": "SF_004",
      "path": "./tests/test_fault_tolerance.py",
      "type": "test",
      "test_count": 3,
      "description": "容错测试",
      "priority": "P2"
    },
    {
      "file_id": "SF_005",
      "path": "./tests/test_performance.py",
      "type": "test",
      "test_count": 2,
      "description": "性能测试",
      "priority": "P3"
    },
    {
      "file_id": "SF_006",
      "path": "./tests/config/test_config.yaml",
      "type": "config",
      "description": "测试环境配置"
    },
    {
      "file_id": "SF_007",
      "path": "./tests/pytest.ini",
      "type": "config",
      "description": "pytest运行配置"
    },
    {
      "file_id": "SF_008",
      "path": "./tests/requirements.txt",
      "type": "config",
      "description": "Python依赖包"
    }
  ],
  
  "test_summary": {
    "total_tests": 15,
    "integration_tests": 4,
    "unit_tests": 6,
    "fault_tolerance_tests": 3,
    "performance_tests": 2,
    "p1_tests": 10,
    "p2_tests": 3,
    "p3_tests": 2
  },
  
  "validation": {
    "all_files_created": true,
    "imports_valid": true,
    "syntax_valid": true
  },
  
  "output": {
    "path": "./output/test_scripts_manifest.json",
    "tests_dir": "./tests/"
  },
  
  "next_skill": {
    "name": "env-config-generator",
    "reason": "生成测试环境配置（docker-compose等）",
    "input_from": ["./output/test_cases.json", "./output/test_scripts_manifest.json"]
  },
  
  "run_command": "pytest ./tests/ -v --alluredir=./allure-results"
}
```

---

## 执行状态说明

| 状态 | 说明 | 后续操作 |
|------|------|----------|
| `success` | 测试脚本生成完成 | 调用 env-config-generator |
| `error_syntax` | 生成脚本语法错误 | 修复并重新生成 |
| `error_import` | 依赖导入问题 | 检查 requirements.txt |
| `partial` | 部分脚本生成成功 | 继续生成剩余脚本 |

---

## 生成的测试脚本模板

### 1. conftest.py - Pytest配置（通用模板）

```python
"""
pytest配置文件
提供测试fixtures和配置
"""

import pytest
import os
import yaml
from pyspark.sql import SparkSession
from pathlib import Path


def load_config():
    """加载测试配置"""
    config_path = Path(__file__).parent / "config" / "test_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return load_config()


@pytest.fixture(scope="session")
def spark_session():
    """Spark Session fixture"""
    spark = SparkSession.builder \
        .appName("IntegrationTest") \
        .master("local[*]") \
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.fixture(scope="session")
def hdfs_client(test_config):
    """HDFS Client fixture"""
    from hdfs import InsecureClient
    
    client = InsecureClient(
        test_config['hdfs']['namenode_url'],
        user=test_config['hdfs']['user']
    )
    
    yield client


@pytest.fixture(scope="function")
def test_data_paths(test_config):
    """测试数据路径fixture"""
    return {
        "input_path": test_config['data']['input_path'],
        "output_path": test_config['data']['output_path'],
        "expected_path": test_config['data']['expected_path']
    }


@pytest.fixture(scope="function")
def cleanup_hdfs(hdfs_client, test_data_paths):
    """清理HDFS测试数据"""
    # Setup: 清理旧数据
    output_path = test_data_paths['output_path']
    try:
        hdfs_client.delete(output_path, recursive=True)
    except:
        pass
    
    yield
    
    # Teardown: 清理新数据（可选）
    # try:
    #     hdfs_client.delete(output_path, recursive=True)
    # except:
    #     pass
```

### 2. test_integration.py - 集成测试

```python
"""
集成测试: HDFS -> Spark -> HDFS
测试从HDFS读取数据，经Spark处理后写回HDFS的完整流程
"""

import pytest
import pandas as pd
from pyspark.sql import functions as F


class TestHDFSSparkIntegration:
    """HDFS-Spark集成测试类"""
    
    @pytest.mark.integration
    @pytest.mark.P1
    def test_hdfs_read_spark_process_hdfs_write(
        self, 
        spark_session, 
        hdfs_client, 
        test_data_paths
    ):
        """
        测试用例: TC_001
        场景: HDFS -> Spark -> HDFS
        优先级: P1
        """
        input_path = test_data_paths['input_path']
        output_path = test_data_paths['output_path']
        expected_path = test_data_paths['expected_path']
        
        # Step 1: 从HDFS读取数据
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        # 验证: 数据读取成功
        assert df.count() > 0, "从HDFS读取数据失败"
        
        # Step 2: Spark处理
        result_df = df.groupBy("category") \
            .agg(
                F.count("*").alias("count"),
                F.sum("value").alias("sum")
            ) \
            .orderBy("category")
        
        # Step 3: 写入HDFS
        result_df.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        # 验证: 数据写入成功
        assert hdfs_client.status(output_path, strict=False) is not None
        
        # Step 4: 结果验证
        # 读取实际结果
        actual_df = spark_session.read \
            .option("header", "true") \
            .csv(output_path)
        
        # 读取预期结果
        expected_df = spark_session.read \
            .option("header", "true") \
            .csv(expected_path)
        
        # 验证行数
        assert actual_df.count() == expected_df.count(), \
            f"行数不匹配: 实际={actual_df.count()}, 预期={expected_df.count()}"
        
        # 验证列数
        assert len(actual_df.columns) == len(expected_df.columns), \
            f"列数不匹配: 实际={len(actual_df.columns)}, 预期={len(expected_df.columns)}"
        
        # 验证数据内容
        actual_pd = actual_df.toPandas()
        expected_pd = expected_df.toPandas()
        
        pd.testing.assert_frame_equal(
            actual_pd.sort_values('category').reset_index(drop=True),
            expected_pd.sort_values('category').reset_index(drop=True),
            check_dtype=False
        )
    
    @pytest.mark.integration
    @pytest.mark.P2
    def test_hdfs_to_spark_local_file_to_hdfs(
        self,
        spark_session,
        hdfs_client,
        test_data_paths,
        tmp_path
    ):
        """
        测试用例: TC_002
        场景: Local File -> Spark -> HDFS
        优先级: P2
        """
        input_path = test_data_paths['input_path']
        output_path = test_data_paths['output_path']
        
        # Step 1: 从本地读取数据
        # 先从HDFS下载到本地
        local_input = str(tmp_path / "input.csv")
        hdfs_client.download(input_path, local_input)
        
        # Step 2: Spark处理本地文件
        df = spark_session.read \
            .option("header", "true") \
            .csv(local_input)
        
        result_df = df.groupBy("category").count()
        
        # Step 3: 写入HDFS
        result_df.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        # 验证
        assert hdfs_client.status(output_path, strict=False) is not None
    
    @pytest.mark.integration
    @pytest.mark.P2
    def test_hdfs_spark_hdfs_with_null_handling(
        self,
        spark_session,
        hdfs_client,
        test_data_paths
    ):
        """
        测试用例: TC_003
        场景: HDFS -> Spark (含空值处理) -> HDFS
        优先级: P2
        """
        input_path = test_data_paths['input_path']
        output_path = test_data_paths['output_path']
        
        # 读取数据
        df = spark_session.read \
            .option("header", "true") \
            .option("nullValue", "") \
            .csv(input_path)
        
        # 空值处理: 过滤掉category为空的行
        df_clean = df.filter(F.col("category").isNotNull())
        
        # 聚合计算
        result_df = df_clean.groupBy("category") \
            .agg(F.count("*").alias("count"))
        
        # 写入
        result_df.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        # 验证结果不含空值
        assert result_df.filter(F.col("category").isNull()).count() == 0


class TestHDFSSparkFaultTolerance:
    """HDFS-Spark容错测试类"""
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P3
    def test_hdfs_read_retry_on_failure(
        self,
        spark_session,
        hdfs_client,
        test_data_paths
    ):
        """
        测试用例: TC_FT_001
        场景: HDFS读取失败重试
        优先级: P3
        """
        input_path = test_data_paths['input_path']
        non_existent_path = "/non/existent/path.csv"
        
        # 测试读取不存在的文件
        with pytest.raises(Exception):
            df = spark_session.read.csv(non_existent_path)
        
        # 测试读取存在的文件（重试后成功）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = spark_session.read.option("header", "true").csv(input_path)
                assert df.count() > 0
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P3
    def test_spark_write_with_directory_conflict(
        self,
        spark_session,
        hdfs_client,
        test_data_paths
    ):
        """
        测试用例: TC_FT_002
        场景: Spark写入已存在的目录（覆盖）
        优先级: P3
        """
        input_path = test_data_paths['input_path']
        output_path = test_data_paths['output_path']
        
        # 第一次写入
        df = spark_session.read.option("header", "true").csv(input_path)
        result_df = df.groupBy("category").count()
        result_df.write.mode("overwrite").csv(output_path)
        
        # 第二次写入（覆盖）
        result_df.write.mode("overwrite").csv(output_path)
        
        # 验证
        assert hdfs_client.status(output_path, strict=False) is not None


class TestHDFSSparkPerformance:
    """HDFS-Spark性能测试类"""
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_hdfs_read_performance(
        self,
        spark_session,
        hdfs_client,
        test_data_paths,
        benchmark
    ):
        """
        测试用例: TC_PERF_001
        场景: HDFS读取性能测试
        优先级: P3
        """
        input_path = test_data_paths['input_path']
        
        def read_data():
            df = spark_session.read \
                .option("header", "true") \
                .csv(input_path)
            return df.count()
        
        result = benchmark(read_data)
        assert result > 0
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_spark_aggregation_performance(
        self,
        spark_session,
        test_data_paths,
        benchmark
    ):
        """
        测试用例: TC_PERF_002
        场景: Spark聚合性能测试
        优先级: P3
        """
        input_path = test_data_paths['input_path']
        
        df = spark_session.read \
            .option("header", "true") \
            .csv(input_path)
        
        def aggregate_data():
            return df.groupBy("category") \
                .agg(F.count("*").alias("count")) \
                .collect()
        
        result = benchmark(aggregate_data)
        assert len(result) > 0
```

### 3. test_unit.py - 单组件测试

```python
"""
单组件测试: HDFS / Spark
测试单个组件的功能点
"""

import pytest
from pyspark.sql import functions as F


class TestHDFSUnit:
    """HDFS单组件测试"""
    
    @pytest.mark.unit
    @pytest.mark.P1
    def test_hdfs_write_csv(self, hdfs_client, test_data_paths, tmp_path):
        """
        测试用例: TC_HDFS_001
        场景: HDFS写入CSV文件
        """
        local_file = tmp_path / "test.csv"
        local_file.write_text("id,name\n1,test\n")
        
        hdfs_path = "/tmp/test_output/test.csv"
        
        # 上传文件
        hdfs_client.upload(hdfs_path, str(local_file))
        
        # 验证
        assert hdfs_client.status(hdfs_path, strict=False) is not None
    
    @pytest.mark.unit
    @pytest.mark.P1
    def test_hdfs_read_csv(self, hdfs_client, test_data_paths):
        """
        测试用例: TC_HDFS_002
        场景: HDFS读取CSV文件
        """
        input_path = test_data_paths['input_path']
        
        # 读取文件
        with hdfs_client.read(input_path) as reader:
            content = reader.read()
        
        assert len(content) > 0
    
    @pytest.mark.unit
    @pytest.mark.P2
    def test_hdfs_list_directory(self, hdfs_client):
        """
        测试用例: TC_HDFS_003
        场景: HDFS列出目录
        """
        path = "/"
        
        # 列出目录
        files = hdfs_client.list(path)
        
        assert isinstance(files, list)


class TestSparkUnit:
    """Spark单组件测试"""
    
    @pytest.mark.unit
    @pytest.mark.P1
    def test_spark_create_dataframe(self, spark_session):
        """
        测试用例: TC_SPARK_001
        场景: Spark创建DataFrame
        """
        data = [("A", 1), ("B", 2), ("C", 3)]
        df = spark_session.createDataFrame(data, ["category", "value"])
        
        assert df.count() == 3
        assert len(df.columns) == 2
    
    @pytest.mark.unit
    @pytest.mark.P1
    def test_spark_groupby_aggregation(self, spark_session):
        """
        测试用例: TC_SPARK_002
        场景: Spark聚合计算
        """
        data = [("A", 10), ("A", 20), ("B", 30), ("B", 40)]
        df = spark_session.createDataFrame(data, ["category", "value"])
        
        result = df.groupBy("category") \
            .agg(F.sum("value").alias("total")) \
            .collect()
        
        result_dict = {row['category']: row['total'] for row in result}
        
        assert result_dict['A'] == 30
        assert result_dict['B'] == 70
    
    @pytest.mark.unit
    @pytest.mark.P2
    def test_spark_filter_operation(self, spark_session):
        """
        测试用例: TC_SPARK_003
        场景: Spark过滤操作
        """
        data = [("A", 10), ("B", 20), ("C", 30)]
        df = spark_session.createDataFrame(data, ["category", "value"])
        
        filtered = df.filter(F.col("value") > 15)
        
        assert filtered.count() == 2
    
    @pytest.mark.unit
    @pytest.mark.P2
    def test_spark_join_operation(self, spark_session):
        """
        测试用例: TC_SPARK_004
        场景: Spark连接操作
        """
        data1 = [("A", 1), ("B", 2)]
        data2 = [("A", "X"), ("B", "Y")]
        
        df1 = spark_session.createDataFrame(data1, ["key", "value1"])
        df2 = spark_session.createDataFrame(data2, ["key", "value2"])
        
        joined = df1.join(df2, on="key")
        
        assert joined.count() == 2
        assert len(joined.columns) == 3
```

---

## 测试配置文件

### test_config.yaml

```yaml
# 测试环境配置
environment: test

# HDFS配置
hdfs:
  namenode_url: "http://localhost:9870"
  user: "test_user"
  base_path: "/tmp/test_data"

# Spark配置
spark:
  app_name: "IntegrationTest"
  master: "local[*]"
  config:
    spark.sql.warehouse.dir: "/tmp/spark-warehouse"
    spark.driver.memory: "2g"
    spark.executor.memory: "2g"

# 数据配置
data:
  input_path: "/tmp/test_data/input/input_data.csv"
  output_path: "/tmp/test_data/output/result"
  expected_path: "/tmp/test_data/expected/expected_output.csv"

# 测试配置
test:
  timeout: 300  # 秒
  retry: 3
  parallel: true
```

---

## pytest.ini

```ini
[pytest]
# 测试发现
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 标记
markers =
    unit: 单组件测试
    integration: 集成测试
    fault_tolerance: 容错测试
    performance: 性能测试
    P1: 优先级P1
    P2: 优先级P2
    P3: 优先级P3

# 配置
addopts = 
    -v
    --strict-markers
    --tb=short
    --alluredir=./allure-results

# 日志
log_cli = true
log_cli_level = INFO

# 警告过滤
filterwarnings =
    ignore::DeprecationWarning
```

---

## requirements.txt

```
pytest>=7.0.0
pytest-benchmark>=4.0.0
pytest-allure>=2.0.0
pytest-xdist>=3.0.0
pyspark>=3.0.0
hdfs>=2.0.0
pandas>=1.0.0
pyyaml>=6.0
```

---

## 脚本生成Prompt

```markdown
你是测试脚本生成专家。请根据以下信息生成pytest测试脚本：

## 测试用例
{test_cases_json}

## 数据路径
{data_manifest_json}

## 组件API参考
{component_cards_json}

## 生成要求

1. **测试文件命名**
   - 集成测试: `test_{components}_integration.py`
   - 单组件测试: `test_{component}_unit.py`
   - 容错测试: `test_{components}_fault_tolerance.py`
   - 性能测试: `test_{components}_performance.py`

2. **测试类组织**
   - 按测试类型分类: `TestIntegration`, `TestUnit`, `TestFaultTolerance`, `TestPerformance`
   - 每个类对应一组相关测试

3. **测试方法命名**
   - 格式: `test_{scenario_name}`
   - 使用下划线分隔
   - 名称清晰描述测试场景

4. **Fixture使用**
   - 使用conftest.py中的fixtures
   - 避免重复初始化
   - 使用合适的scope

5. **断言设计**
   - 明确的断言条件
   - 清晰的错误消息
   - 验证关键点

6. **标记使用**
   - 类型标记: @pytest.mark.unit/integration/fault_tolerance/performance
   - 优先级标记: @pytest.mark.P1/P2/P3

请生成完整的pytest测试脚本。
```

---

## 执行命令

```bash
# 运行所有测试
pytest tests/

# 运行特定类型测试
pytest -m integration tests/
pytest -m unit tests/
pytest -m fault_tolerance tests/
pytest -m performance tests/

# 运行特定优先级测试
pytest -m P1 tests/

# 并行执行
pytest -n auto tests/

# 生成测试报告
pytest --alluredir=./allure-results tests/
allure serve ./allure-results
```