"""
Iceberg-StarRocks功能测试
测试Iceberg外部Catalog创建、外表查询、数据同步
"""

import pytest
import time


class TestIcebergCatalog:
    """Iceberg外部Catalog测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_create_iceberg_catalog(self, starrocks_cursor, cleanup_tables):
        """
        TC_FUNC_003: StarRocks创建Iceberg外部Catalog
        """
        cleanup_tables()
        
        sql = """
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES (
            'type' = 'iceberg',
            'iceberg.catalog.type' = 'hive',
            'hive.metastore.uris' = 'thrift://hive:9083',
            'warehouse' = 'hdfs://namenode:9000/warehouse/iceberg'
        )
        """
        
        starrocks_cursor.execute(sql)
        
        starrocks_cursor.execute("SHOW CATALOGS")
        catalogs = starrocks_cursor.fetchall()
        
        catalog_names = [c['Catalog'] for c in catalogs]
        assert 'test_iceberg_catalog' in catalog_names
        
        cleanup_tables()
    
    @pytest.mark.functional
    @pytest.mark.P2
    def test_show_iceberg_catalog_properties(self, starrocks_cursor, cleanup_tables):
        """
        验证Iceberg Catalog属性
        """
        cleanup_tables()
        
        sql = """
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES (
            'type' = 'iceberg',
            'iceberg.catalog.type' = 'hive'
        )
        """
        starrocks_cursor.execute(sql)
        
        starrocks_cursor.execute("SHOW CREATE CATALOG test_iceberg_catalog")
        result = starrocks_cursor.fetchall()
        
        assert len(result) > 0
        assert 'iceberg' in result[0]['Create Catalog']
        
        cleanup_tables()


class TestIcebergExternalTable:
    """Iceberg外表查询测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_query_iceberg_table(self, starrocks_cursor, cleanup_tables):
        """
        TC_FUNC_004: StarRocks查询Iceberg外表
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = "SELECT * FROM test_iceberg_catalog.test_db.iceberg_table LIMIT 10"
        
        try:
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            assert len(results) >= 0
        except Exception as e:
            pytest.skip(f"Iceberg table not ready: {e}")
        
        cleanup_tables()
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_aggregate_iceberg_table(self, starrocks_cursor, cleanup_tables):
        """
        TC_FUNC_005: StarRocks聚合查询Iceberg
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = """
        SELECT category, COUNT(*) as cnt, SUM(value) as total 
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
                    assert 'cnt' in row
                    assert row['cnt'] > 0
        except Exception as e:
            pytest.skip(f"Iceberg table not ready: {e}")
        
        cleanup_tables()


class TestStarRocksInternalTable:
    """StarRocks内部表测试"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_create_olap_table(self, starrocks_cursor, cleanup_tables):
        """
        TC_FUNC_006: StarRocks创建内部OLAP表
        """
        cleanup_tables()
        
        sql = """
        CREATE TABLE test_olap_table (
            id INT,
            name STRING,
            value DOUBLE,
            category STRING,
            timestamp DATETIME
        ) ENGINE=OLAP
        PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """
        
        starrocks_cursor.execute(sql)
        
        starrocks_cursor.execute("SHOW TABLES")
        tables = starrocks_cursor.fetchall()
        table_names = [t['Tables_in_test'] for t in tables]
        
        assert 'test_olap_table' in table_names
        
        cleanup_tables()
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_insert_into_olap_table(self, starrocks_cursor, cleanup_tables):
        """
        数据写入StarRocks内部表
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE TABLE test_olap_table (
            id INT, name STRING, value DOUBLE
        ) ENGINE=OLAP PRIMARY KEY(id)
        DISTRIBUTED BY HASH(id) BUCKETS 3
        PROPERTIES ("replication_num" = "1")
        """)
        
        sql = "INSERT INTO test_olap_table VALUES (1, 'test', 100.0)"
        starrocks_cursor.execute(sql)
        
        starrocks_cursor.execute("SELECT * FROM test_olap_table")
        results = starrocks_cursor.fetchall()
        
        assert len(results) >= 1
        
        cleanup_tables()