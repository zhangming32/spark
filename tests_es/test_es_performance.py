"""
Elasticsearch性能测试
测试不同数据规模的索引、搜索、聚合性能
"""

import pytest
import json
import time
import requests


class TestESPerformance:
    """性能测试类"""
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_small_data_indexing_performance(self, es_client, es_index_name, 
                                              cleanup_index, test_data_paths, 
                                              load_log_data):
        """
        TC_ES_PERF_001: 小数据量索引性能(100条)
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_small'])
        
        start_time = time.time()
        
        bulk_body = ""
        for i, log in enumerate(logs):
            bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": i}}) + "\n"
            bulk_body += json.dumps(log) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        response = requests.post(
            f"{es_client['base_url']}/_bulk",
            headers=headers,
            data=bulk_body
        )
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 1000
        
        print(f"Small data indexing time: {elapsed_ms:.2f}ms")
        
        cleanup_index(es_index_name)
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_medium_data_indexing_performance(self, es_client, es_index_name, 
                                               cleanup_index, test_data_paths, 
                                               load_log_data):
        """
        TC_ES_PERF_002: 中等数据量索引性能(10000条)
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_medium'])
        
        start_time = time.time()
        
        bulk_body = ""
        for i, log in enumerate(logs):
            bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": i}}) + "\n"
            bulk_body += json.dumps(log) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        response = requests.post(
            f"{es_client['base_url']}/_bulk",
            headers=headers,
            data=bulk_body
        )
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 5000
        
        print(f"Medium data indexing time: {elapsed_ms:.2f}ms")
        
        cleanup_index(es_index_name)
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_search_performance(self, es_client, es_index_name, cleanup_index,
                                 test_data_paths, load_log_data):
        """
        TC_ES_PERF_003: 搜索查询性能
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_medium'])
        
        bulk_body = ""
        for i, log in enumerate(logs):
            bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": i}}) + "\n"
            bulk_body += json.dumps(log) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        requests.post(f"{es_client['base_url']}/_bulk", headers=headers, data=bulk_body)
        
        time.sleep(2)
        
        query = {
            "query": {
                "match": {
                    "message": "error"
                }
            }
        }
        
        start_time = time.time()
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 100
        
        print(f"Search query time: {elapsed_ms:.2f}ms")
        
        cleanup_index(es_index_name)
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_aggregation_performance(self, es_client, es_index_name, cleanup_index,
                                      test_data_paths, load_log_data):
        """
        TC_ES_PERF_004: 聚合分析性能
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        logs = load_log_data(test_data_paths['logs_medium'])
        
        bulk_body = ""
        for i, log in enumerate(logs):
            bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": i}}) + "\n"
            bulk_body += json.dumps(log) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        requests.post(f"{es_client['base_url']}/_bulk", headers=headers, data=bulk_body)
        
        time.sleep(2)
        
        query = {
            "size": 0,
            "aggs": {
                "level_stats": {
                    "terms": {
                        "field": "level"
                    }
                }
            }
        }
        
        start_time = time.time()
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 200
        
        print(f"Aggregation time: {elapsed_ms:.2f}ms")
        
        cleanup_index(es_index_name)