"""
pytest配置文件 - Elasticsearch测试
提供测试fixtures和配置
"""

import pytest
import json
import os
import yaml
from pathlib import Path
import requests


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
def es_client(test_config):
    """Elasticsearch客户端fixture"""
    es_host = test_config['elasticsearch']['host']
    es_port = test_config['elasticsearch']['port']
    base_url = f"http://{es_host}:{es_port}"
    
    def make_request(method, path, data=None):
        url = f"{base_url}{path}"
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=json.dumps(data))
        elif method == "PUT":
            response = requests.put(url, headers=headers, data=json.dumps(data))
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return response
    
    yield {
        "base_url": base_url,
        "request": make_request,
        "host": es_host,
        "port": es_port
    }


@pytest.fixture(scope="session")
def es_index_name(test_config):
    """测试索引名称"""
    return test_config['elasticsearch']['test_index']


@pytest.fixture(scope="function")
def test_data_paths(test_config):
    """测试数据路径fixture"""
    return {
        "logs_small": test_config['data']['logs_small'],
        "logs_medium": test_config['data']['logs_medium'],
        "logs_error": test_config['data']['logs_error'],
        "logs_empty": test_config['data']['logs_empty'],
        "expected_agg": test_config['data']['expected_agg']
    }


@pytest.fixture(scope="function")
def load_log_data(test_data_paths):
    """加载日志数据fixture"""
    def load_json(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return load_json


@pytest.fixture(scope="function")
def cleanup_index(es_client, es_index_name):
    """清理测试索引"""
    def delete_index(index_name):
        try:
            response = es_client['request']("DELETE", f"/{index_name}")
            return response.status_code in [200, 404]
        except Exception:
            return False
    
    yield delete_index


@pytest.fixture(scope="function")
def create_test_index(es_client, es_index_name):
    """创建测试索引"""
    mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "level": {"type": "keyword"},
                "message": {"type": "text"},
                "service": {"type": "keyword"},
                "host": {"type": "keyword"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
    
    response = es_client['request']("PUT", f"/{es_index_name}", mapping)
    
    yield response
    
    es_client['request']("DELETE", f"/{es_index_name}")