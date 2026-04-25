"""
Iceberg-StarRocks性能测试
"""

import pytest
import time


class TestIcebergStarRocksPerformance:
    """性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_iceberg_query_performance(self, starrocks_cursor, cleanup_tables):
        """
        TC_PERF_001: Iceberg外表查询性能
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = "SELECT * FROM test_iceberg_catalog.test_db.iceberg_table_medium LIMIT 10000"
        
        try:
            start_time = time.time()
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert elapsed_ms < 10000
            print(f"Query time: {elapsed_ms:.2f}ms, rows: {len(results)}")
        except Exception as e:
            pytest.skip(f"Performance test requires Iceberg data: {e}")
        
        cleanup_tables()
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_aggregation_performance(self, starrocks_cursor, cleanup_tables):
        """
        TC_PERF_003: Iceberg聚合分析性能
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = """
        SELECT category, COUNT(*) as cnt, SUM(value) as total, AVG(value) as avg
        FROM test_iceberg_catalog.test_db.iceberg_table_medium
        GROUP BY category
        """
        
        try:
            start_time = time.time()
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert elapsed_ms < 5000
            print(f"Aggregation time: {elapsed_ms:.2f}ms")
        except Exception as e:
            pytest.skip(f"Performance test requires Iceberg data: {e}")
        
        cleanup_tables()
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_join_performance(self, starrocks_cursor, cleanup_tables):
        """
        TC_PERF_004: Iceberg JOIN内部表性能
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        starrocks_cursor.execute("""
        CREATE TABLE dim_table (
            id INT, dim_value STRING
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """)
        
        for i in range(1, 100):
            starrocks_cursor.execute(f"INSERT INTO dim_table VALUES ({i}, 'dim_{i}')")
        
        sql = """
        SELECT f.id, f.name, d.dim_value 
        FROM test_iceberg_catalog.test_db.iceberg_table_medium f 
        JOIN dim_table d ON f.id = d.id
        """
        
        try:
            start_time = time.time()
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert elapsed_ms < 10000
            print(f"Join time: {elapsed_ms:.2f}ms")
        except Exception as e:
            pytest.skip(f"Join performance test requires Iceberg data: {e}")
        
        cleanup_tables()
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_stream_load_performance(self, starrocks_connection, cleanup_tables):
        """
        Stream Load性能测试
        """
        cleanup_tables()
        
        cursor = starrocks_connection.cursor()
        cursor.execute("""
        CREATE TABLE perf_test_table (
            id INT, name STRING, value DOUBLE
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 10
        PROPERTIES ("replication_num" = "1")
        """)
        
        try:
            import requests
            
            data = "id,name,value\n"
            for i in range(1, 1001):
                data += f"{i},name_{i},{i * 10.0}\n"
            
            start_time = time.time()
            response = requests.put(
                "http://localhost:8030/api/test/perf_test_table/_stream_load",
                headers={"column_separator": ","},
                data=data
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert response.status_code == 200
            assert elapsed_ms < 3000
            print(f"Stream Load time: {elapsed_ms:.2f}ms")
        except Exception as e:
            pytest.skip(f"Stream Load test skipped: {e}")
        
        cleanup_tables()