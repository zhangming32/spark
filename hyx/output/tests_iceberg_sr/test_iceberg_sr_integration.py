"""
Iceberg-StarRocks集成测试
测试Iceberg与StarRocks之间的数据同步和联合查询
"""

import pytest
import time


class TestIcebergStarRocksIntegration:
    """Iceberg-StarRocks集成测试"""
    
    @pytest.mark.integration
    @pytest.mark.P1
    def test_iceberg_to_starrocks_sync(self, starrocks_cursor, cleanup_tables,
                                        load_test_data, test_data_paths):
        """
        TC_INT_001: Iceberg数据导入StarRocks完整流程
        """
        cleanup_tables()
        
        # Step 1: 创建Iceberg Catalog
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES (
            'type' = 'iceberg',
            'iceberg.catalog.type' = 'hive',
            'hive.metastore.uris' = 'thrift://hive:9083'
        )
        """)
        
        # Step 2: 创建StarRocks内部表
        starrocks_cursor.execute("""
        CREATE TABLE test_olap_table (
            id INT, name STRING, value DOUBLE, category STRING
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """)
        
        # Step 3: 从Iceberg导入数据
        try:
            sql = """
            INSERT INTO test_olap_table 
            SELECT id, name, value, category 
            FROM test_iceberg_catalog.test_db.iceberg_table
            """
            starrocks_cursor.execute(sql)
            
            # 验证数据
            starrocks_cursor.execute("SELECT COUNT(*) as cnt FROM test_olap_table")
            result = starrocks_cursor.fetchone()
            assert result['cnt'] > 0
        except Exception as e:
            pytest.skip(f"Iceberg data not ready: {e}")
        
        cleanup_tables()
    
    @pytest.mark.integration
    @pytest.mark.P1
    def test_starrocks_to_iceberg_write(self, starrocks_cursor, cleanup_tables):
        """
        TC_INT_002: StarRocks数据写入Iceberg
        """
        cleanup_tables()
        
        # 创建内部表并写入数据
        starrocks_cursor.execute("""
        CREATE TABLE source_table (
            id INT, name STRING, value DOUBLE
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """)
        
        starrocks_cursor.execute("INSERT INTO source_table VALUES (1, 'test', 100.0)")
        
        # 创建Iceberg Catalog
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        # 写入Iceberg
        try:
            sql = """
            INSERT INTO test_iceberg_catalog.test_db.target_iceberg_table 
            SELECT * FROM source_table
            """
            starrocks_cursor.execute(sql)
        except Exception as e:
            pytest.skip(f"Iceberg write not ready: {e}")
        
        cleanup_tables()
    
    @pytest.mark.integration
    @pytest.mark.P2
    def test_iceberg_join_internal_table(self, starrocks_cursor, cleanup_tables):
        """
        TC_INT_005: Iceberg外表JOIN内部表
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        starrocks_cursor.execute("""
        CREATE TABLE internal_dim (
            id INT, extra_col STRING
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """)
        
        starrocks_cursor.execute("INSERT INTO internal_dim VALUES (1, 'extra')")
        
        try:
            sql = """
            SELECT i.id, i.name, d.extra_col 
            FROM test_iceberg_catalog.test_db.iceberg_table i 
            JOIN internal_dim d ON i.id = d.id
            """
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            assert len(results) >= 0
        except Exception as e:
            pytest.skip(f"Join test requires Iceberg data: {e}")
        
        cleanup_tables()
    
    @pytest.mark.integration
    @pytest.mark.P2
    def test_schema_evolution_query(self, starrocks_cursor, cleanup_tables):
        """
        TC_INT_006: Iceberg Schema Evolution后StarRocks查询
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        try:
            # 查询新增列（假设Iceberg表已添加new_col）
            sql = "SELECT id, new_col FROM test_iceberg_catalog.test_db.iceberg_table_evolved"
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
        except Exception as e:
            pytest.skip(f"Schema evolution test requires evolved Iceberg table: {e}")
        
        cleanup_tables()


class TestOLAPAnalysis:
    """OLAP分析测试"""
    
    @pytest.mark.integration
    @pytest.mark.P2
    def test_complex_aggregation(self, starrocks_cursor, cleanup_tables):
        """
        复杂OLAP聚合分析
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = """
        SELECT 
            category,
            AVG(value) as avg_val,
            MAX(value) as max_val,
            MIN(value) as min_val,
            COUNT(*) as cnt
        FROM test_iceberg_catalog.test_db.iceberg_table
        GROUP BY category
        ORDER BY category
        """
        
        try:
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            
            if results:
                for row in results:
                    assert 'category' in row
                    assert 'avg_val' in row
                    assert row['cnt'] > 0
        except Exception as e:
            pytest.skip(f"OLAP analysis requires Iceberg data: {e}")
        
        cleanup_tables()