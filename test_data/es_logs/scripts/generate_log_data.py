#!/usr/bin/env python3
"""
Elasticsearch日志数据生成脚本
生成用于日志分析测试的JSON格式日志数据
"""

import json
import random
from datetime import datetime, timedelta
import os

class LogDataGenerator:
    """日志数据生成器"""
    
    LEVELS = ["ERROR", "WARN", "INFO", "DEBUG"]
    LEVEL_WEIGHTS = [0.1, 0.2, 0.6, 0.1]
    
    SERVICES = ["user-service", "order-service", "payment-service", 
                "api-gateway", "inventory-service"]
    
    HOSTS = ["server-01", "server-02", "server-03", "server-04"]
    
    ERROR_MESSAGES = [
        "Database connection failed: timeout after 30s",
        "NullPointerException in UserService.java",
        "Failed to process payment: card declined",
        "Redis connection refused",
        "Memory allocation failed",
        "HTTP request timeout: 500 Internal Server Error",
        "Authentication failed: invalid token",
        "File not found: /data/config.yaml",
        "Thread pool exhausted",
        "Constraint violation: duplicate key"
    ]
    
    WARN_MESSAGES = [
        "High memory usage detected: 85% utilized",
        "Slow query detected: execution time 5s",
        "Connection pool nearing limit: 90% used",
        "Cache miss rate high: 30%",
        "Deprecated API called: v1/users",
        "Rate limit approaching: 95% of threshold",
        "Disk space low: 10% remaining",
        "Certificate expires in 30 days",
        "Response time degraded: avg 2s",
        "Unhandled exception caught"
    ]
    
    INFO_MESSAGES = [
        "User login successful",
        "Order created: order_id=12345",
        "Payment processed successfully",
        "Service started on port 8080",
        "Cache refreshed",
        "Configuration loaded",
        "Health check passed",
        "Request processed in 100ms",
        "Connection established",
        "Task completed successfully"
    ]
    
    DEBUG_MESSAGES = [
        "Cache hit for key: session_user_12345",
        "SQL query executed: SELECT * FROM users",
        "Entering method: processOrder()",
        "Variable state: count=100",
        "Thread spawned: worker-5",
        "HTTP request headers: {...}",
        "Validation passed: field=username",
        "Loop iteration: i=50",
        "Memory allocated: 1024 bytes",
        "Config value: timeout=30"
    ]
    
    def __init__(self, output_dir: str = "./test_data/es_logs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_timestamp(self, base_time: datetime, offset_minutes: int) -> str:
        """生成ISO8601格式时间戳"""
        ts = base_time + timedelta(minutes=offset_minutes)
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def generate_message(self, level: str) -> str:
        """根据日志级别生成消息"""
        if level == "ERROR":
            return random.choice(self.ERROR_MESSAGES)
        elif level == "WARN":
            return random.choice(self.WARN_MESSAGES)
        elif level == "INFO":
            return random.choice(self.INFO_MESSAGES)
        else:
            return random.choice(self.DEBUG_MESSAGES)
    
    def generate_log(self, base_time: datetime, index: int, level_override: str = None) -> dict:
        """生成单条日志"""
        level = level_override or random.choices(self.LEVELS, weights=self.LEVEL_WEIGHTS)[0]
        
        return {
            "timestamp": self.generate_timestamp(base_time, index),
            "level": level,
            "message": self.generate_message(level),
            "service": random.choice(self.SERVICES),
            "host": random.choice(self.HOSTS)
        }
    
    def generate_logs(self, count: int, level_filter: str = None, 
                      base_time: datetime = None) -> list:
        """生成多条日志"""
        if base_time is None:
            base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        logs = []
        for i in range(count):
            if level_filter:
                log = self.generate_log(base_time, i, level_filter)
            else:
                log = self.generate_log(base_time, i)
            logs.append(log)
        
        return logs
    
    def save_json(self, logs: list, filename: str):
        """保存JSON文件"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        print(f"Generated {len(logs)} logs to {filepath}")
        return filepath
    
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("Generating Elasticsearch log test data...")
        
        # 1. 小规模日志(100条) - 功能测试
        logs_small = self.generate_logs(100)
        self.save_json(logs_small, "logs_small.json")
        
        # 2. 中等规模日志(10000条) - 集成/性能测试
        logs_medium = self.generate_logs(10000)
        self.save_json(logs_medium, "logs_medium.json")
        
        # 3. 仅ERROR日志(50条) - 搜索测试
        logs_error = self.generate_logs(50, level_filter="ERROR")
        self.save_json(logs_error, "logs_error_only.json")
        
        # 4. 空日志文件 - 容错测试
        self.save_json([], "logs_empty.json")
        
        # 5. 预期聚合结果
        expected_agg = [
            {"level": "ERROR", "count": 10},
            {"level": "WARN", "count": 20},
            {"level": "INFO", "count": 60},
            {"level": "DEBUG", "count": 10}
        ]
        self.save_json(expected_agg, "expected_agg_result.json")
        
        print("All test data generated successfully!")


if __name__ == "__main__":
    generator = LogDataGenerator(output_dir="/home/z00878808/gitstore/spark/test_data/es_logs")
    generator.generate_all_test_data()