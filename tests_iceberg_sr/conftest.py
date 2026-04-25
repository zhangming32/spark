"""
pytest配置文件 - Iceberg-StarRocks集成测试
"""

import pytest
import os
import yaml
import json
import mysql.connector
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
def starrocks_connection(test_config):
    """StarRocks数据库连接fixture"""
    conn = mysql.connector.connect(
        host=test_config['starrocks']['host'],
        port=test_config['starrocks']['fe_port'],
        user=test_config['starrocks']['user'],
        password=test_config['starrocks']['password'],
        database=test_config['starrocks']['database']
    )
    
    yield conn
    
    conn.close()


@pytest.fixture(scope="session")
def starrocks_cursor(starrocks_connection):
    """StarRocks游标fixture"""
    cursor = starrocks_connection.cursor(dictionary=True)
    yield cursor
    cursor.close()


@pytest.fixture(scope="function")
def test_data_paths(test_config):
    """测试数据路径fixture"""
    return {
        "iceberg_small": test_config['data']['iceberg_small'],
        "iceberg_medium": test_config['data']['iceberg_medium'],
        "starrocks_import": test_config['data']['starrocks_import'],
        "expected_agg": test_config['data']['expected_agg']
    }


@pytest.fixture(scope="function")
def load_test_data(test_data_paths):
    """加载测试数据fixture"""
    def load_json(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return load_json


@pytest.fixture(scope="function")
def cleanup_tables(starrocks_cursor, test_config):
    """清理测试表"""
    def cleanup():
        cursor = starrocks_cursor
        try:
            cursor.execute("DROP TABLE IF EXISTS test_iceberg_table")
            cursor.execute("DROP TABLE IF EXISTS test_olap_table")
            cursor.execute("DROP EXTERNAL CATALOG IF EXISTS test_iceberg_catalog")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    return cleanup


def execute_sql(cursor, sql):
    """执行SQL并返回结果"""
    try:
        cursor.execute(sql)
        if cursor.description:
            return cursor.fetchall()
        return None
    except Exception as e:
        return {"error": str(e)}