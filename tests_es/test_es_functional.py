"""
Elasticsearch日志分析功能测试
测试索引创建、文档操作、搜索查询、聚合分析
"""

import pytest
import json
import time


class TestESIndexManagement:
    """索引管理测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_create_index(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FUNC_001: 创建日志索引
        """
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
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("acknowledged") == True
        assert result.get("index") == es_index_name
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P2
    def test_delete_index(self, es_client, es_index_name):
        """
        TC_ES_FUNC_002: 删除索引
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        response = es_client['request']("DELETE", f"/{es_index_name}")
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("acknowledged") == True


class TestESDocumentOperations:
    """文档操作测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_index_single_document(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FUNC_003: 索引单条日志文档
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        doc = {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "ERROR",
            "message": "Database connection failed",
            "service": "user-service",
            "host": "server-01"
        }
        
        response = es_client['request']("PUT", f"/{es_index_name}/_doc/1", doc)
        
        assert response.status_code == 201
        result = response.json()
        assert result.get("result") == "created"
        assert result.get("_index") == es_index_name
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_bulk_index_documents(self, es_client, es_index_name, cleanup_index, 
                                   test_data_paths, load_log_data):
        """
        TC_ES_FUNC_004: 批量索引日志文档
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        
        bulk_body = ""
        for i, log in enumerate(logs[:100]):
            bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": i}}) + "\n"
            bulk_body += json.dumps(log) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        response = requests.post(
            f"{es_client['base_url']}/_bulk",
            headers=headers,
            data=bulk_body
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("errors") == False
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_get_document(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FUNC_008: 获取日志文档
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        doc = {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "ERROR",
            "message": "Test message",
            "service": "test-service",
            "host": "server-01"
        }
        es_client['request']("PUT", f"/{es_index_name}/_doc/test_id", doc)
        
        response = es_client['request']("GET", f"/{es_index_name}/_doc/test_id")
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("found") == True
        assert result["_source"]["level"] == "ERROR"
        
        cleanup_index(es_index_name)


class TestESSearchQueries:
    """搜索查询测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_match_query(self, es_client, es_index_name, cleanup_index,
                         test_data_paths, load_log_data):
        """
        TC_ES_FUNC_004: 全文搜索日志
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_error'])
        for i, log in enumerate(logs):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "query": {
                "match": {
                    "message": "failed"
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        assert result["hits"]["total"]["value"] > 0
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_term_query(self, es_client, es_index_name, cleanup_index,
                        test_data_paths, load_log_data):
        """
        TC_ES_FUNC_005: 按日志级别过滤
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs[:50]):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "query": {
                "term": {
                    "level": "ERROR"
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        
        hits = result["hits"]["hits"]
        for hit in hits:
            assert hit["_source"]["level"] == "ERROR"
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_range_query(self, es_client, es_index_name, cleanup_index,
                         test_data_paths, load_log_data):
        """
        TC_ES_FUNC_006: 时间范围查询
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs[:50]):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "query": {
                "range": {
                    "timestamp": {
                        "gte": "2024-01-15T00:00:00Z",
                        "lte": "2024-01-15T12:00:00Z"
                    }
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        assert result["hits"]["total"]["value"] > 0
        
        cleanup_index(es_index_name)
    
    @pytest.mark.functional
    @pytest.mark.P2
    def test_bool_query(self, es_client, es_index_name, cleanup_index,
                        test_data_paths, load_log_data):
        """
        TC_ES_FUNC_007: 布尔组合查询
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs[:50]):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"level": "ERROR"}}
                    ],
                    "filter": [
                        {"term": {"service": "user-service"}}
                    ]
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        
        hits = result["hits"]["hits"]
        for hit in hits:
            assert hit["_source"]["level"] == "ERROR"
            assert hit["_source"]["service"] == "user-service"
        
        cleanup_index(es_index_name)


class TestESAggregations:
    """聚合分析测试"""
    
    @pytest.mark.aggregation
    @pytest.mark.P1
    def test_terms_aggregation(self, es_client, es_index_name, cleanup_index,
                               test_data_paths, load_log_data):
        """
        TC_ES_AGG_001: 日志级别统计聚合
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "size": 0,
            "aggs": {
                "level_stats": {
                    "terms": {
                        "field": "level",
                        "size": 10
                    }
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        
        buckets = result["aggregations"]["level_stats"]["buckets"]
        assert len(buckets) > 0
        
        for bucket in buckets:
            assert bucket["key"] in ["ERROR", "WARN", "INFO", "DEBUG"]
            assert bucket["doc_count"] > 0
        
        cleanup_index(es_index_name)
    
    @pytest.mark.aggregation
    @pytest.mark.P2
    def test_service_aggregation(self, es_client, es_index_name, cleanup_index,
                                 test_data_paths, load_log_data):
        """
        TC_ES_AGG_002: 服务日志统计聚合
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "size": 0,
            "aggs": {
                "service_stats": {
                    "terms": {
                        "field": "service",
                        "size": 10
                    }
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        
        buckets = result["aggregations"]["service_stats"]["buckets"]
        assert len(buckets) > 0
        
        cleanup_index(es_index_name)
    
    @pytest.mark.aggregation
    @pytest.mark.P2
    def test_date_histogram_aggregation(self, es_client, es_index_name, cleanup_index,
                                        test_data_paths, load_log_data):
        """
        TC_ES_AGG_003: 时间序列聚合
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        for i, log in enumerate(logs):
            es_client['request']("PUT", f"/{es_index_name}/_doc/{i}", log)
        
        time.sleep(1)
        
        query = {
            "size": 0,
            "aggs": {
                "logs_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "hour"
                    }
                }
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        
        buckets = result["aggregations"]["logs_over_time"]["buckets"]
        assert len(buckets) > 0
        
        cleanup_index(es_index_name)


import requests