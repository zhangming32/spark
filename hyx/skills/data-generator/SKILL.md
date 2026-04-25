---
name: data-generator
description: 根据测试用例需求生成测试数据。支持公开数据集推荐和按需Skill生成两种策略，数据生成在脚本生成之前完成。
license: MIT
metadata:
  author: opencode
  version: "1.0"
---

根据测试用例需求生成测试数据，支持公开数据集推荐和Skill按需生成。

---

## 设计原则

**数据生成顺序（重要）：**
```
测试用例生成 → 数据生成 → 测试脚本生成
     ↑              ↑           ↑
scenario-    data-generator  test-script-
planner                    generator
```

**数据必须在脚本生成前准备好，因为脚本需要引用数据路径。**

---

## 数据生成策略

### 策略一：公开数据集推荐（优先）

#### 1.1 公开数据集库

| 数据集名称 | 规模 | 格式 | 适用场景 | 来源 |
|-----------|------|------|----------|------|
| Page Views | 800万条 | CSV | Web日志分析、聚合计算 | Kaggle |
| Online Retail | 54万条 | CSV | 电商交易、统计分析 | UCI |
| NYC Taxi | 10亿+ | CSV | 大规模数据处理、地理计算 | NYC TLC |
| Wikipedia Clickstream | 30亿 | TSV | 链接分析、图计算 | Wikimedia |
| GitHub Events | 事件流 | JSON | 流处理、实时分析 | GH Archive |
| Twitter Sample | 流式 | JSON | 文本处理、情感分析 | Twitter API |
| Web Server Logs | 可变 | Apache日志 | 日志解析、分析 | LogHub |
| IoT Sensor Data | 流式 | JSON | 时序数据、监控 | Kaggle |

#### 1.2 数据集选择算法

```python
def select_dataset(data_requirements: dict) -> dict:
    """
    根据数据需求选择最合适的公开数据集
    
    Args:
        data_requirements: {
            "data_type": "text_file",  # text_file/json/parquet
            "format": "CSV",
            "size": "medium",  # small/medium/large/huge
            "fields": ["timestamp", "value", "category"],
            "scenario": "aggregation",  # aggregation/join/filter
            "components": ["{source_component}", "{processor_component}"]
        }
    
    Returns:
        {
            "dataset": "Online Retail",
            "source": "UCI ML Repository",
            "download_url": "https://...",
            "size": "45MB",
            "format": "CSV",
            "fields": ["InvoiceNo", "StockCode", "Description", 
                      "Quantity", "InvoiceDate", "UnitPrice", 
                      "CustomerID", "Country"],
            "preprocessing": [
                "Remove rows with null CustomerID",
                "Convert InvoiceDate to timestamp"
            ]
        }
    """
    pass
```

#### 1.3 数据集下载脚本模板

```bash
#!/bin/bash
# download_dataset.sh
DATASET_NAME=${1:-"online_retail"}
DATA_DIR=${2:-"./test_data"}

mkdir -p $DATA_DIR

case $DATASET_NAME in
  "online_retail")
    wget -O $DATA_DIR/online_retail.csv \
      "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
    # 转换格式
    python3 scripts/convert_xlsx_to_csv.py \
      $DATA_DIR/Online_Retail.xlsx \
      $DATA_DIR/online_retail.csv
    ;;
  
  "page_views")
    wget -O $DATA_DIR/page_views.csv \
      "https://.../page_views.csv"
    ;;
  
  "nyc_taxi_sample")
    # 下载样本数据
    wget -O $DATA_DIR/nyc_taxi_sample.csv \
      "https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2023-01.csv"
    # 截取前100万条
    head -n 1000001 $DATA_DIR/nyc_taxi_sample.csv > $DATA_DIR/nyc_taxi_1m.csv
    ;;
esac

echo "Dataset $DATASET_NAME downloaded to $DATA_DIR"
```

---

### 策略二：Skill按需生成

当公开数据集不满足需求时，使用Skill生成定制数据。

#### 2.1 数据生成Prompt模板

```markdown
你是测试数据生成专家。请根据以下需求生成测试数据：

## 数据需求
- 数据类型: {data_type}
- 格式: {format}
- 规模: {size}
- 字段要求: {fields}
- 数据特征: {characteristics}
- 目标组件: {components}

## 生成要求
1. 字段说明
   - 每个字段的含义
   - 数据类型
   - 取值范围
   - 约束条件

2. 数据特征
   - 数据分布（均匀/偏斜/正态）
   - 是否包含边界值
   - 是否包含异常值
   - 是否包含空值

3. 数据量
   - 行数
   - 文件大小估计

4. 数据格式
   - 字段分隔符
   - 编码格式
   - 是否包含header

请生成数据并说明数据特征。
```

#### 2.2 数据生成脚本模板

```python
#!/usr/bin/env python3
"""
数据生成脚本
根据测试用例需求生成测试数据
"""

import random
import string
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker('zh_CN')

class DataGenerator:
    """通用数据生成器"""
    
    def __init__(self, config: dict):
        """
        初始化数据生成器
        
        Args:
            config: {
                "num_rows": 100000,
                "output_format": "csv",
                "output_path": "./test_data/data.csv",
                "fields": [
                    {
                        "name": "id",
                        "type": "integer",
                        "min": 1,
                        "max": 1000000
                    },
                    {
                        "name": "timestamp",
                        "type": "datetime",
                        "start": "2023-01-01",
                        "end": "2023-12-31"
                    },
                    {
                        "name": "value",
                        "type": "float",
                        "min": 0.0,
                        "max": 1000.0,
                        "distribution": "normal"
                    }
                ]
            }
        """
        self.config = config
        self.num_rows = config.get("num_rows", 10000)
        
    def generate(self) -> pd.DataFrame:
        """生成数据"""
        data = {}
        
        for field in self.config["fields"]:
            data[field["name"]] = self._generate_field(field)
        
        return pd.DataFrame(data)
    
    def _generate_field(self, field: dict):
        """生成单个字段"""
        field_type = field["type"]
        
        if field_type == "integer":
            return self._generate_integer(field)
        elif field_type == "float":
            return self._generate_float(field)
        elif field_type == "string":
            return self._generate_string(field)
        elif field_type == "datetime":
            return self._generate_datetime(field)
        elif field_type == "category":
            return self._generate_category(field)
        elif field_type == "boolean":
            return self._generate_boolean(field)
        else:
            raise ValueError(f"Unknown field type: {field_type}")
    
    def _generate_integer(self, field: dict):
        """生成整数"""
        min_val = field.get("min", 0)
        max_val = field.get("max", 1000000)
        distribution = field.get("distribution", "uniform")
        
        if distribution == "uniform":
            return np.random.randint(min_val, max_val + 1, self.num_rows)
        elif distribution == "normal":
            mean = (min_val + max_val) / 2
            std = (max_val - min_val) / 6
            values = np.random.normal(mean, std, self.num_rows)
            return np.clip(values, min_val, max_val).astype(int)
        elif distribution == "zipf":
            return np.random.zipf(1.5, self.num_rows)
    
    def _generate_float(self, field: dict):
        """生成浮点数"""
        min_val = field.get("min", 0.0)
        max_val = field.get("max", 1000.0)
        distribution = field.get("distribution", "uniform")
        
        if distribution == "uniform":
            return np.random.uniform(min_val, max_val, self.num_rows)
        elif distribution == "normal":
            mean = (min_val + max_val) / 2
            std = (max_val - min_val) / 6
            values = np.random.normal(mean, std, self.num_rows)
            return np.clip(values, min_val, max_val)
    
    def _generate_string(self, field: dict):
        """生成字符串"""
        pattern = field.get("pattern", "random")
        
        if pattern == "name":
            return [fake.name() for _ in range(self.num_rows)]
        elif pattern == "email":
            return [fake.email() for _ in range(self.num_rows)]
        elif pattern == "address":
            return [fake.address() for _ in range(self.num_rows)]
        elif pattern == "random":
            length = field.get("length", 10)
            return [''.join(random.choices(string.ascii_letters + string.digits, 
                                          k=length)) 
                   for _ in range(self.num_rows)]
    
    def _generate_datetime(self, field: dict):
        """生成日期时间"""
        start = datetime.strptime(field.get("start", "2023-01-01"), "%Y-%m-%d")
        end = datetime.strptime(field.get("end", "2023-12-31"), "%Y-%m-%d")
        
        delta = end - start
        random_seconds = np.random.randint(0, delta.total_seconds(), self.num_rows)
        
        return [start + timedelta(seconds=int(s)) for s in random_seconds]
    
    def _generate_category(self, field: dict):
        """生成分类数据"""
        categories = field.get("categories", ["A", "B", "C"])
        probabilities = field.get("probabilities", None)
        
        return np.random.choice(categories, self.num_rows, p=probabilities)
    
    def _generate_boolean(self, field: dict):
        """生成布尔值"""
        probability = field.get("probability_true", 0.5)
        
        return np.random.choice([True, False], self.num_rows, 
                               p=[probability, 1-probability])
    
    def save(self, df: pd.DataFrame, output_path: str, output_format: str = "csv"):
        """保存数据"""
        if output_format == "csv":
            df.to_csv(output_path, index=False)
        elif output_format == "json":
            df.to_json(output_path, orient="records", lines=True)
        elif output_format == "parquet":
            df.to_parquet(output_path, index=False)
        
        print(f"Generated {len(df)} rows to {output_path}")


# 预定义数据生成器

class TransactionDataGenerator(DataGenerator):
    """交易数据生成器"""
    
    def __init__(self, num_rows: int = 100000, output_path: str = "./transactions.csv"):
        config = {
            "num_rows": num_rows,
            "output_format": "csv",
            "output_path": output_path,
            "fields": [
                {"name": "transaction_id", "type": "integer", "min": 1},
                {"name": "customer_id", "type": "integer", "min": 1, "max": 10000},
                {"name": "product_id", "type": "integer", "min": 1, "max": 1000},
                {"name": "quantity", "type": "integer", "min": 1, "max": 100},
                {"name": "price", "type": "float", "min": 1.0, "max": 1000.0},
                {"name": "timestamp", "type": "datetime", "start": "2023-01-01", "end": "2023-12-31"},
                {"name": "store_id", "type": "integer", "min": 1, "max": 100},
                {"name": "payment_method", "type": "category", 
                 "categories": ["credit_card", "debit_card", "cash", "mobile"]}
            ]
        }
        super().__init__(config)


class LogDataGenerator(DataGenerator):
    """日志数据生成器"""
    
    def __init__(self, num_rows: int = 100000, output_path: str = "./logs.txt"):
        config = {
            "num_rows": num_rows,
            "output_format": "txt",
            "output_path": output_path,
            "fields": [
                {"name": "timestamp", "type": "datetime", "start": "2023-01-01", "end": "2023-12-31"},
                {"name": "level", "type": "category", 
                 "categories": ["INFO", "WARN", "ERROR", "DEBUG"]},
                {"name": "service", "type": "category",
                 "categories": ["api-gateway", "user-service", "order-service", "payment-service"]},
                {"name": "message", "type": "string", "pattern": "random", "length": 50}
            ]
        }
        super().__init__(config)


if __name__ == "__main__":
    # 示例用法
    generator = TransactionDataGenerator(num_rows=1000000)
    df = generator.generate()
    generator.save(df, "./test_data/transactions.csv")
```

---

## 数据需求分析

### 输入：测试用例JSON

```json
{
  "test_case_id": "TC_001",
  "scenario": {
    "description": "source -> processor -> sink",
    "components": ["{source_component}", "{processor_component}", "{sink_component}"]
  },
  "data_requirements": {
    "input": {
      "source": "{source_component}",
      "type": "text_file",
      "format": "CSV",
      "size": "medium",
      "fields": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "value", "type": "float"},
        {"name": "category", "type": "string"}
      ],
      "characteristics": {
        "distribution": "normal",
        "null_percentage": 0.01,
        "duplicate_percentage": 0.001
      }
    },
    "expected_output": {
      "type": "aggregated_result",
      "format": "CSV",
      "validation": {
        "row_count": "reduced",
        "columns": ["category", "count", "sum"]
      }
    }
  }
}
```

### 输出：数据生成方案

```json
{
  "data_plan_id": "DP_001",
  "strategy": "public_dataset",
  "dataset": {
    "name": "Online Retail",
    "source": "UCI ML Repository",
    "download_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx",
    "size": "45MB",
    "format": "CSV",
    "fields_match": {
      "InvoiceNo": "id",
      "Description": "name",
      "Quantity": "value",
      "Country": "category"
    }
  },
  "preprocessing_steps": [
    {
      "step": 1,
      "action": "remove_nulls",
      "description": "Remove rows with null CustomerID"
    },
    {
      "step": 2,
      "action": "convert_types",
      "description": "Convert InvoiceDate to timestamp"
    },
    {
      "step": 3,
      "action": "filter_columns",
      "description": "Select required columns only"
    }
  ],
  "output_files": [
    {
      "path": "./test_data/input_data.csv",
      "size": "30MB",
      "rows": 400000
    },
    {
      "path": "./test_data/expected_output.csv",
      "size": "1MB",
      "rows": 38,
      "description": "Expected aggregation result for validation"
    }
  ]
}
```

---

## 数据生成工作流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        数据生成工作流                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  测试用例JSON                                                                │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Step 1: 数据需求分析                                                 │    │
│  │ - 解析测试用例中的data_requirements                                  │    │
│  │ - 提取字段需求、数据类型、规模、特征                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Step 2: 数据集匹配（公开数据集优先）                                  │    │
│  │ - 检查公开数据集库                                                   │    │
│  │ - 匹配字段、规模、格式                                               │    │
│  │ - 计算匹配度得分                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ├── 匹配度 >= 0.7 ──────────────────────────────────────────┐         │
│       │                                                            ▼         │
│       │                    ┌─────────────────────────────────────┐           │
│       │                    │ 策略一：公开数据集                  │           │
│       │                    │ - 生成下载脚本                      │           │
│       │                    │ - 生成预处理脚本                    │           │
│       │                    │ - 数据路径注入用例                  │           │
│       │                    └─────────────────────────────────────┘           │
│       │                                                                      │
│       ├── 匹配度 < 0.7 ──────────────────────────────────────────┐         │
│       │                                                            ▼         │
│       │                    ┌─────────────────────────────────────┐           │
│       │                    │ 策略二：Skill生成                    │           │
│       │                    │ - 生成数据生成脚本                   │           │
│       │                    │ - 执行数据生成                      │           │
│       │                    │ - 数据路径注入用例                  │           │
│       │                    └─────────────────────────────────────┘           │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Step 3: 生成测试预期输出（可选）                                     │    │
│  │ - 根据测试逻辑生成预期结果                                          │    │
│  │ - 用于结果验证                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Step 4: 输出数据生成报告                                            │    │
│  │ - 数据路径列表                                                      │    │
│  │ - 数据规模统计                                                      │    │
│  │ - 数据特征描述                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  数据准备完成，可进行测试脚本生成                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 数据生成脚本结构

```
test_data/
├── raw/                          # 原始数据
│   ├── online_retail.csv
│   └── nyc_taxi_sample.csv
├── processed/                    # 处理后数据
│   ├── input_data.csv           # 测试输入
│   ├── expected_output.csv      # 预期输出
│   └── test_config.json         # 数据配置
├── scripts/                      # 数据生成脚本
│   ├── download_dataset.sh      # 下载脚本
│   ├── generate_data.py         # 生成脚本
│   └── preprocess.py            # 预处理脚本
└── metadata/                     # 数据元信息
    ├── data_manifest.json       # 数据清单
    └── field_descriptions.md    # 字段说明
```

---

## 与其他Skill的协作

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  scenario-planner                                              │
│       │                                                         │
│       │ 输出: test_cases.json                                  │
│       │         └─ data_requirements                            │
│       ▼                                                         │
│  ┌─────────────────┐                                            │
│  │ data-generator  │ ◀── 公开数据集库                          │
│  │    (本Skill)    │                                            │
│  └─────────────────┘                                            │
│       │                                                         │
│       │ 输出: data_paths.json                                  │
│       │         └─ input_data_path                            │
│       │         └─ expected_output_path                       │
│       ▼                                                         │
│  test-script-generator                                         │
│       │                                                         │
│       │ 使用: 数据路径                                          │
│       ▼                                                         │
│  测试脚本 (pytest)                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 输出数据清单格式（完整输出结构）

### 输出文件路径
```
./output/data_manifest.json
./test_data/processed/input_data.csv
./test_data/processed/expected_output.csv
```

### 输出JSON结构

```json
{
  "data_manifest_id": "DM_001",
  "generation_timestamp": "2024-01-15T10:30:00Z",
  "status": "success|error",
  "errors": [],
  
  "input_source": "./output/test_cases.json",
  "test_case_ids": ["TC_001", "TC_002"],
  
  "strategy": "public_dataset|generated|hybrid",
  "strategy_reason": "匹配公开数据集Online Retail",
  
  "data_files": [
    {
      "file_id": "DF_001",
      "path": "./test_data/processed/input_data.csv",
      "type": "input",
      "format": "CSV",
      "size_bytes": 31457280,
      "row_count": 400000,
      "columns": [
        {"name": "id", "type": "integer", "nullable": false},
        {"name": "name", "type": "string", "nullable": false},
        {"name": "value", "type": "float", "nullable": false},
        {"name": "category", "type": "string", "nullable": true}
      ],
      "source": "public_dataset",
      "dataset_name": "Online Retail"
    },
    {
      "file_id": "DF_002",
      "path": "./test_data/processed/expected_output.csv",
      "type": "expected_output",
      "format": "CSV",
      "size_bytes": 1048576,
      "row_count": 38,
      "columns": [
        {"name": "category", "type": "string"},
        {"name": "count", "type": "integer"},
        {"name": "sum", "type": "float"}
      ],
      "source": "generated",
      "generation_logic": "groupBy category, count, sum"
    }
  ],
  
  "scripts_generated": [
    {
      "script_path": "./test_data/scripts/download_dataset.sh",
      "description": "Download Online Retail dataset",
      "executed": true
    },
    {
      "script_path": "./test_data/scripts/preprocess.py",
      "description": "Preprocess raw data for testing",
      "executed": true
    },
    {
      "script_path": "./test_data/scripts/generate_expected.py",
      "description": "Generate expected output",
      "executed": true
    }
  ],
  
  "validation": {
    "all_files_exist": true,
    "row_counts_match": true,
    "schemas_valid": true,
    "data_quality_score": 0.95
  },
  
  "output": {
    "path": "./output/data_manifest.json",
    "format": "json"
  },
  
  "next_skill": {
    "name": "test-script-generator",
    "reason": "数据已准备好，可生成测试脚本",
    "input_files": [
      "./output/test_cases.json",
      "./output/data_manifest.json"
    ]
  }
}
```

---

## 执行状态说明

| 状态 | 说明 | 后续操作 |
|------|------|----------|
| `success` | 数据生成完成 | 调用 test-script-generator |
| `error_download` | 公开数据集下载失败 | 尝试 Skill 生成 |
| `error_generation` | Skill 生成失败 | 报告错误，等待处理 |
| `partial` | 部分数据生成成功 | 继续生成剩余数据 |

---

## 执行命令

```bash
# 下载公开数据集
bash ./test_data/scripts/download_dataset.sh online_retail ./test_data/raw

# 预处理数据
python3 ./test_data/scripts/preprocess.py \
  --input ./test_data/raw/online_retail.csv \
  --output ./test_data/processed/input_data.csv

# 生成测试预期输出
python3 ./test_data/scripts/generate_data.py \
  --input ./test_data/processed/input_data.csv \
  --output ./test_data/processed/expected_output.csv \
  --type expected_output
```