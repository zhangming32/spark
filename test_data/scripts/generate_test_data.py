#!/usr/bin/env python3
"""
测试数据生成脚本
用于生成HDFS-Spark-HDFS测试所需的CSV数据文件
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

def generate_test_data(output_dir: str = "./test_data/input"):
    """生成测试数据"""
    os.makedirs(output_dir, exist_ok=True)
    
    categories = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    # 生成小规模数据 (100行)
    print("生成小规模数据...")
    small_data = {
        "id": range(1, 101),
        "category": np.random.choice(categories, 100),
        "value": np.random.uniform(0, 1000, 100)
    }
    df_small = pd.DataFrame(small_data)
    df_small.to_csv(f"{output_dir}/data_small.csv", index=False)
    print(f"  已生成: {output_dir}/data_small.csv (100行)")
    
    # 生成中等规模数据 (100000行)
    print("生成中等规模数据...")
    medium_data = {
        "id": range(1, 100001),
        "category": np.random.choice(categories, 100000),
        "value": np.random.uniform(0, 1000, 100000)
    }
    df_medium = pd.DataFrame(medium_data)
    df_medium.to_csv(f"{output_dir}/data_medium.csv", index=False)
    print(f"  已生成: {output_dir}/data_medium.csv (100000行)")
    
    # 生成大规模数据 (1000000行)
    print("生成大规模数据...")
    large_data = {
        "id": range(1, 1000001),
        "category": np.random.choice(categories, 1000000),
        "value": np.random.uniform(0, 1000, 1000000)
    }
    df_large = pd.DataFrame(large_data)
    df_large.to_csv(f"{output_dir}/data_large.csv", index=False)
    print(f"  已生成: {output_dir}/data_large.csv (1000000行)")
    
    # 生成空文件 (仅header)
    print("生成空文件...")
    empty_df = pd.DataFrame(columns=["id", "category", "value"])
    empty_df.to_csv(f"{output_dir}/empty.csv", index=False)
    print(f"  已生成: {output_dir}/empty.csv (0行)")
    
    print("测试数据生成完成！")

def generate_expected_output(input_path: str = "./test_data/input/data_small.csv",
                             output_dir: str = "./test_data/expected"):
    """生成预期输出数据（聚合结果）"""
    os.makedirs(output_dir, exist_ok=True)
    
    print("生成预期聚合结果...")
    df = pd.read_csv(input_path)
    
    expected = df.groupby("category").agg(
        count=("id", "count"),
        total=("value", "sum")
    ).reset_index()
    
    expected.to_csv(f"{output_dir}/expected_aggregation.csv", index=False)
    print(f"  已生成: {output_dir}/expected_aggregation.csv")
    print(f"  行数: {len(expected)}")
    
    return expected

if __name__ == "__main__":
    generate_test_data()
    generate_expected_output()