"""
Elasticsearch容错测试
测试错误处理和异常场景
"""

import pytest
import json
import requests


class TestESFaultTolerance:
    """容错测试类"""
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_index_not_found_error(self, es_client):
        """
        TC_ES_FT_001: 索引不存在错误
        """
        response = es_client['request']("GET", "/nonexistent_index/_search")
        
        assert response.status_code == 404
        result = response.json()
        assert result.get("error", {}).get("type") == "index_not_found_exception"
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_document_not_found(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FT_002: 文档不存在查询
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        response = es_client['request']("GET", f"/{es_index_name}/_doc/nonexistent_id")
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("found") == False
        
        cleanup_index(es_index_name)
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_empty_index_search(self, es_client, es_index_name, cleanup_index,
                                 test_data_paths, load_log_data):
        """
        TC_ES_FT_003: 空索引查询
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        query = {
            "query": {
                "match_all": {}
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", query)
        
        assert response.status_code == 200
        result = response.json()
        assert result["hits"]["total"]["value"] == 0
        
        cleanup_index(es_index_name)
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_invalid_query_dsl(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FT_004: 无效QueryDSL
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        invalid_query = {
            "query": {
                "invalid_field": "value"
            }
        }
        
        response = es_client['request']("POST", f"/{es_index_name}/_search", invalid_query)
        
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        
        cleanup_index(es_index_name)
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P3
    def test_bulk_partial_failure(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FT_005: 批量写入部分失败
        """
        es_client['request']("PUT", f"/{es_index_name}")
        
        bulk_body = ""
        
        valid_doc = {"level": "INFO", "message": "valid"}
        bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": "1"}}) + "\n"
        bulk_body += json.dumps(valid_doc) + "\n"
        
        bulk_body += json.dumps({"index": {"_index": es_index_name, "_id": "2"}}) + "\n"
        bulk_body += json.dumps({"invalid_field": "value"}) + "\n"
        
        headers = {"Content-Type": "application/x-ndjson"}
        response = requests.post(
            f"{es_client['base_url']}/_bulk",
            headers=headers,
            data=bulk_body
        )
        
        assert response.status_code == 200
        result = response.json()
        
        items = result.get("items", [])
        assert len(items) == 2
        
        cleanup_index(es_index_name)
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P3
    def test_field_type_conflict(self, es_client, es_index_name, cleanup_index):
        """
        TC_ES_FT_006: 字段类型冲突
        """
        mapping = {
            "mappings": {
                "properties": {
                    "level": {"type": "keyword"}
                }
            }
        }
        es_client['request']("PUT", f"/{es_index_name}", mapping)
        
        valid_doc = {"level": "ERROR"}
        es_client['request']("PUT", f"/{es_index_name}/_doc/1", valid_doc)
        
        invalid_doc = {"level": 123}
        response = es_client['request']("PUT", f"/{es_index_name}/_doc/2", invalid_doc)
        
        cleanup_index(es_index_name)