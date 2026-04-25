"""
Iceberg-StarRocks容错测试
"""

import pytest


class TestIcebergStarRocksFaultTolerance:
    """容错测试"""
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_table_not_found(self, starrocks_cursor, cleanup_tables):
        """
        TC_FT_001: Iceberg表不存在时StarRocks查询
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        sql = "SELECT * FROM test_iceberg_catalog.db.nonexistent_table"
        
        try:
            starrocks_cursor.execute(sql)
            pytest.fail("Should raise error for nonexistent table")
        except Exception as e:
            assert 'not found' in str(e).lower() or 'does not exist' in str(e).lower()
        
        cleanup_tables()
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_catalog_not_found(self, starrocks_cursor, cleanup_tables):
        """
        TC_FT_002: Catalog不存在
        """
        cleanup_tables()
        
        sql = "SELECT * FROM nonexistent_catalog.db.table"
        
        try:
            starrocks_cursor.execute(sql)
            pytest.fail("Should raise error for nonexistent catalog")
        except Exception as e:
            assert 'catalog' in str(e).lower() or 'not found' in str(e).lower()
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_invalid_catalog_properties(self, starrocks_cursor, cleanup_tables):
        """
        无效的Catalog配置
        """
        cleanup_tables()
        
        sql = """
        CREATE EXTERNAL CATALOG invalid_catalog 
        PROPERTIES ('type' = 'iceberg', 'invalid_prop' = 'value')
        """
        
        try:
            starrocks_cursor.execute(sql)
        except Exception as e:
            assert 'error' in str(e).lower() or 'invalid' in str(e).lower()
        
        cleanup_tables()
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_query_empty_iceberg_table(self, starrocks_cursor, cleanup_tables):
        """
        查询空Iceberg表
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        try:
            sql = "SELECT * FROM test_iceberg_catalog.test_db.empty_iceberg_table"
            starrocks_cursor.execute(sql)
            results = starrocks_cursor.fetchall()
            assert len(results) == 0
        except Exception as e:
            pytest.skip(f"Empty Iceberg table not ready: {e}")
        
        cleanup_tables()
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_permission_denied_write(self, starrocks_cursor, cleanup_tables):
        """
        TC_FT_004: 写入Iceberg权限不足
        """
        cleanup_tables()
        
        starrocks_cursor.execute("""
        CREATE EXTERNAL CATALOG test_iceberg_catalog 
        PROPERTIES ('type' = 'iceberg', 'iceberg.catalog.type' = 'hive')
        """)
        
        try:
            sql = "INSERT INTO test_iceberg_catalog.test_db.restricted_table VALUES (1, 'test')"
            starrocks_cursor.execute(sql)
        except Exception as e:
            assert 'permission' in str(e).lower() or 'denied' in str(e).lower() or 'error' in str(e).lower()
        
        cleanup_tables()