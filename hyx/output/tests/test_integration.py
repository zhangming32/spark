"""
集成测试: HDFS -> Spark -> HDFS
测试从HDFS读取数据，经Spark处理后写回HDFS的完整流程

测试用例版本: v2.0
用例数量: 18个 (覆盖functional/integration/fault_tolerance/boundary/performance)
"""

import pytest
import os
import time
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, DoubleType, StructType, StructField


class TestHDFSSparkFunctional:
    """功能测试类"""
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_hdfs_read_success(self, spark_session, test_data_paths):
        """
        TC_FUNC_001: HDFS读取CSV文件
        验证从HDFS正确读取CSV格式文件
        """
        input_path = test_data_paths["input_small"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        assert df.count() == 100, "数据行数应为100"
        assert len(df.columns) == 3, "列数应为3"
        assert set(df.columns) == {"id", "category", "value"}, "列名应为id,category,value"
        
        schema = df.schema
        assert schema["id"].dataType == IntegerType(), "id应为IntegerType"
        assert schema["category"].dataType == StringType(), "category应为StringType"
        assert schema["value"].dataType == DoubleType(), "value应为DoubleType"
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_schema_validation(self, spark_session, test_data_paths):
        """
        TC_FUNC_006: Schema验证
        验证读取数据的Schema正确性
        """
        input_path = test_data_paths["input_small"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        expected_schema = StructType([
            StructField("id", IntegerType(), nullable=True),
            StructField("category", StringType(), nullable=True),
            StructField("value", DoubleType(), nullable=True)
        ])
        
        actual_fields = [(f.name, f.dataType) for f in df.schema.fields]
        expected_fields = [(f.name, f.dataType) for f in expected_schema.fields]
        
        assert actual_fields == expected_fields, f"Schema不匹配: {actual_fields} vs {expected_fields}"
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_spark_aggregation(self, spark_session, test_data_paths):
        """
        TC_FUNC_003: Spark聚合计算
        验证Spark聚合计算功能正确性
        """
        input_path = test_data_paths["input_small"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        result = df.groupBy("category") \
            .agg(
                F.count("*").alias("count"),
                F.sum("value").alias("total")
            )
        
        assert result.count() == 10, "聚合后应有10个category"
        assert set(result.columns) == {"category", "count", "total"}, "列名正确"
        
        count_sum = result.agg(F.sum("count")).collect()[0][0]
        assert count_sum == 100, f"count总和应为100，实际为{count_sum}"
    
    @pytest.mark.functional
    @pytest.mark.P1
    def test_hdfs_write_success(self, spark_session, test_data_paths, cleanup_output):
        """
        TC_FUNC_002: HDFS写入CSV文件
        验证结果正确写入
        """
        input_path = test_data_paths["input_small"]
        output_path = test_data_paths["output_path"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        result = df.groupBy("category") \
            .agg(F.count("*").alias("count"), F.sum("value").alias("total"))
        
        result.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        assert os.path.exists(output_path), "输出目录应存在"
        
        files = os.listdir(output_path)
        csv_files = [f for f in files if f.endswith(".csv")]
        assert len(csv_files) > 0, "应有CSV文件输出"
    
    @pytest.mark.functional
    @pytest.mark.P2
    def test_spark_filter(self, spark_session, test_data_paths):
        """
        TC_FUNC_004: Spark过滤操作
        """
        input_path = test_data_paths["input_small"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        threshold = 500
        filtered = df.filter(F.col("value") > threshold)
        
        assert filtered.count() > 0, "应有满足条件的记录"
        
        min_value = filtered.agg(F.min("value")).collect()[0][0]
        assert min_value > threshold, f"最小值{min_value}应大于{threshold}"
    
    @pytest.mark.functional
    @pytest.mark.P2
    def test_spark_sort(self, spark_session, test_data_paths):
        """
        TC_FUNC_005: Spark排序操作
        """
        input_path = test_data_paths["input_small"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        sorted_df = df.orderBy("category")
        
        categories = sorted_df.select("category").collect()
        category_list = [row["category"] for row in categories]
        
        assert category_list == sorted(category_list), "结果应按category升序排列"


class TestHDFSSparkIntegration:
    """集成测试类"""
    
    @pytest.mark.integration
    @pytest.mark.P1
    def test_full_pipeline(self, spark_session, test_data_paths, cleanup_output):
        """
        TC_INT_001: HDFS->Spark->HDFS完整流程
        """
        input_path = test_data_paths["input_small"]
        output_path = test_data_paths["output_path"]
        
        # Step 1: 读取数据
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        input_count = df.count()
        assert input_count == 100, "Step 1: 数据读取成功，100行"
        
        # Step 2: 聚合计算
        result = df.groupBy("category") \
            .agg(F.count("*").alias("count"), F.sum("value").alias("total"))
        
        output_count = result.count()
        assert output_count == 10, "Step 2: 聚合结果10行"
        
        count_sum = result.agg(F.sum("count")).collect()[0][0]
        assert count_sum == 100, "Step 2: count总和=输入行数"
        
        # Step 3: 写入结果
        result.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        assert os.path.exists(output_path), "Step 3: 写入成功"
        
        # Step 4: 验证结果
        result_read = spark_session.read \
            .option("header", "true") \
            .csv(output_path)
        
        assert result_read.count() == 10, "Step 4: 结果可读，10行"
    
    @pytest.mark.integration
    @pytest.mark.P1
    def test_data_integrity(self, spark_session, test_data_paths, cleanup_output):
        """
        TC_INT_004: 数据完整性端到端验证
        """
        input_path = test_data_paths["input_small"]
        output_path = test_data_paths["output_path"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        input_categories = df.select("category").distinct().count()
        input_value_sum = df.agg(F.sum("value")).collect()[0][0]
        
        result = df.groupBy("category") \
            .agg(F.count("*").alias("count"), F.sum("value").alias("total"))
        
        result.write.mode("overwrite").option("header", "true").csv(output_path)
        
        output_categories = result.count()
        output_count_sum = result.agg(F.sum("count")).collect()[0][0]
        output_value_sum = result.agg(F.sum("total")).collect()[0][0]
        
        assert output_categories == input_categories, "category数量一致"
        assert output_count_sum == 100, "count总和=输入行数"
        assert abs(output_value_sum - input_value_sum) < 1.0, "total总和≈输入value总和"


class TestHDFSSparkFaultTolerance:
    """容错测试类"""
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_read_empty_file(self, spark_session, test_data_paths):
        """
        TC_FT_002: HDFS读取空文件
        """
        input_path = test_data_paths["input_empty"]
        
        df = spark_session.read \
            .option("header", "true") \
            .csv(input_path)
        
        assert df.count() == 0, "空文件应返回空DataFrame"
        assert len(df.columns) == 3, "Schema应保留"
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_process_empty_dataframe(self, spark_session):
        """
        TC_FT_004: Spark处理空DataFrame
        """
        empty_df = spark_session.createDataFrame([], "id INT, category STRING, value DOUBLE")
        
        result = empty_df.groupBy("category").count()
        
        assert result.count() == 0, "空数据聚合应为空"
    
    @pytest.mark.fault_tolerance
    @pytest.mark.P2
    def test_read_nonexistent_file(self, spark_session):
        """
        TC_FT_001: HDFS读取不存在文件
        """
        nonexistent_path = "/nonexistent/path.csv"
        
        with pytest.raises(Exception) as exc_info:
            spark_session.read.csv(nonexistent_path)
        
        assert "not exist" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower(), \
            f"应为文件不存在异常: {exc_info.value}"


class TestHDFSSparkBoundary:
    """边界值测试类"""
    
    @pytest.mark.boundary
    @pytest.mark.P2
    def test_boundary_id_zero(self, spark_session, test_data_paths):
        """
        TC_BOUND_001: id边界值0
        """
        input_path = test_data_paths["input_boundary"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        row_with_id_zero = df.filter(F.col("id") == 0)
        assert row_with_id_zero.count() == 1, "应有id=0的记录"
        
        row = row_with_id_zero.collect()[0]
        assert row["id"] == 0, f"id应为0，实际为{row['id']}"
    
    @pytest.mark.boundary
    @pytest.mark.P2
    def test_boundary_id_large(self, spark_session, test_data_paths):
        """
        TC_BOUND_002: id边界值999999
        """
        input_path = test_data_paths["input_boundary"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        row_with_large_id = df.filter(F.col("id") == 999999)
        assert row_with_large_id.count() == 1, "应有id=999999的记录"
    
    @pytest.mark.boundary
    @pytest.mark.P2
    def test_boundary_negative_value(self, spark_session, test_data_paths):
        """
        TC_BOUND_003: value负数边界值
        """
        input_path = test_data_paths["input_boundary"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        negative_values = df.filter(F.col("value") < 0)
        assert negative_values.count() > 0, "应有负数value记录"
    
    @pytest.mark.boundary
    @pytest.mark.P2
    def test_null_category(self, spark_session, test_data_paths):
        """
        TC_FT_006: 读取包含null值的数据
        TC_BOUND_004: category为空字符串
        """
        input_path = test_data_paths["input_boundary"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        null_categories = df.filter(F.col("category").isNull() | (F.col("category") == ""))
        assert null_categories.count() > 0, "应有category为null或空的记录"


class TestHDFSSparkPerformance:
    """性能测试类"""
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_medium_data_read_performance(self, spark_session, test_data_paths):
        """
        TC_PERF_002: HDFS中等数据量读取性能
        """
        input_path = test_data_paths["input_medium"]
        
        start = time.time()
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        count = df.count()
        elapsed = time.time() - start
        
        assert count == 100000, f"读取行数应为100000，实际为{count}"
        assert elapsed < 30, f"读取耗时应<30s，实际为{elapsed:.2f}s"
        
        print(f"性能数据: 读取100000行耗时 {elapsed:.2f}s")
    
    @pytest.mark.performance
    @pytest.mark.P3
    def test_aggregation_performance(self, spark_session, test_data_paths):
        """
        TC_PERF_003: Spark聚合性能
        """
        input_path = test_data_paths["input_medium"]
        
        df = spark_session.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(input_path)
        
        start = time.time()
        result = df.groupBy("category") \
            .agg(F.count("*").alias("count"), F.sum("value").alias("total"))
        result.count()
        elapsed = time.time() - start
        
        assert elapsed < 10, f"聚合耗时应<10s，实际为{elapsed:.2f}s"
        
        print(f"性能数据: 聚合100000行耗时 {elapsed:.2f}s")