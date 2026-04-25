#!/usr/bin/env python3
"""
Iceberg-StarRocks测试数据生成脚本
生成用于Iceberg和StarRocks集成测试的数据
"""

import json
import random
from datetime import datetime, timedelta
import csv
import os

class IcebergStarRocksDataGenerator:
    """测试数据生成器"""
    
    CATEGORIES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    
    def __init__(self, output_dir: str = "./test_data/iceberg_sr"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_timestamp(self, base_time: datetime, offset_minutes: int) -> str:
        """生成ISO8601格式时间戳"""
        ts = base_time + timedelta(minutes=offset_minutes)
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def generate_row(self, id: int, base_time: datetime) -> dict:
        """生成单行数据"""
        return {
            "id": id,
            "name": f"user_{id}",
            "value": round(random.uniform(0.0, 1000.0), 2),
            "category": random.choice(self.CATEGORIES),
            "timestamp": self.generate_timestamp(base_time, id)
        }
    
    def generate_data(self, count: int, base_time: datetime = None) -> list:
        """生成多条数据"""
        if base_time is None:
            base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        return [self.generate_row(i, base_time) for i in range(1, count + 1)]
    
    def save_json(self, data: list, filename: str):
        """保存JSON格式"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Generated {len(data)} rows to {filepath}")
    
    def save_csv(self, data: list, filename: str):
        """保存CSV格式（StarRocks导入）"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'value', 'category', 'timestamp'])
            writer.writeheader()
            writer.writerows(data)
        print(f"Generated {len(data)} rows to {filepath}")
    
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("Generating Iceberg-StarRocks test data...")
        
        # 小规模数据(100条) - 功能测试
        small_data = self.generate_data(100)
        self.save_json(small_data, "iceberg_data_small.json")
        self.save_csv(small_data, "starrocks_import_small.csv")
        
        # 中等规模数据(10000条) - 集成/性能测试
        medium_data = self.generate_data(10000)
        self.save_json(medium_data, "iceberg_data_medium.json")
        self.save_csv(medium_data, "starrocks_import_medium.csv")
        
        # 预期聚合结果
        expected_agg = [
            {"category": cat, "count": random.randint(80, 120), "total": round(random.uniform(5000, 15000), 2)}
            for cat in self.CATEGORIES
        ]
        self.save_json(expected_agg, "expected_aggregation.json")
        
        print("All test data generated successfully!")


if __name__ == "__main__":
    generator = IcebergStarRocksDataGenerator(output_dir="/home/z00878808/gitstore/spark/test_data/iceberg_sr")
    generator.generate_all_test_data()