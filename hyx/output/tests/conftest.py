"""
pytest配置文件
提供测试fixtures和配置

版本: v2.0
"""

import pytest
import os
import yaml
from pyspark.sql import SparkSession
from pathlib import Path


def load_config():
    """加载测试配置"""
    config_path = Path(__file__).parent / "config" / "test_config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {
        "hdfs": {
            "namenode_url": "hdfs://localhost:9000",
            "webhdfs_url": "http://localhost:9870",
            "user": "root"
        },
        "spark": {
            "master": "local[*]",
            "app_name": "HDFSSparkTest"
        },
        "data": {
            "input_path": "./test_data/input",
            "output_path": "./test_data/output",
            "expected_path": "./test_data/expected"
        }
    }


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return load_config()


@pytest.fixture(scope="session")
def spark_session():
    """Spark Session fixture"""
    spark = SparkSession.builder \
        .appName("HDFSSparkIntegrationTest") \
        .master("local[*]") \
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse") \
        .config("spark.driver.memory", "2g") \
        .config("spark.ui.enabled", "false") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    yield spark
    
    spark.stop()


@pytest.fixture(scope="function")
def test_data_paths(test_config):
    """测试数据路径fixture"""
    base_input = test_config["data"]["input_path"]
    return {
        "input_small": f"{base_input}/data_small.csv",
        "input_medium": f"{base_input}/data_medium.csv",
        "input_boundary": f"{base_input}/data_boundary.csv",
        "input_empty": f"{base_input}/empty.csv",
        "output_path": f"{test_config['data']['output_path']}/result/",
        "expected_path": f"{test_config['data']['expected_path']}/expected_aggregation.csv"
    }


@pytest.fixture(scope="function")
def cleanup_output(test_data_paths):
    """清理输出目录"""
    output_path = test_data_paths["output_path"]
    
    yield
    
    if os.path.exists(output_path):
        import shutil
        shutil.rmtree(output_path, ignore_errors=True)


@pytest.fixture(scope="function")
def benchmark():
    """性能基准fixture"""
    import time
    
    class Benchmark:
        def __init__(self):
            self.start_time = None
            self.elapsed = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.elapsed = time.time() - self.start_time
            return self.elapsed
        
        def assert_under(self, threshold_seconds):
            assert self.elapsed < threshold_seconds, \
                f"耗时{self.elapsed:.2f}s超过阈值{threshold_seconds}s"
    
    return Benchmark()


# pytest markers 注册
def pytest_configure(config):
    config.addinivalue_line("markers", "functional: 功能测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "fault_tolerance: 容错测试")
    config.addinivalue_line("markers", "boundary: 边界值测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "P1: 优先级P1")
    config.addinivalue_line("markers", "P2: 优先级P2")
    config.addinivalue_line("markers", "P3: 优先级P3")