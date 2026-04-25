#!/bin/bash
set -e

echo "=== 启动Iceberg-StarRocks环境 ==="

cd "$(dirname "$0")/.."

docker-compose up -d

echo "等待服务启动..."
sleep 30

# 检查Hive Metastore
echo "检查Hive Metastore..."
max_retries=20
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if nc -z localhost 9083; then
        echo "Hive Metastore已启动"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "等待Hive Metastore... ($retry_count/$max_retries)"
    sleep 5
done

# 检查StarRocks FE
echo "检查StarRocks FE..."
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:9030 > /dev/null 2>&1; then
        echo "StarRocks FE已启动"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "等待StarRocks FE... ($retry_count/$max_retries)"
    sleep 5
done

# 检查MinIO
echo "检查MinIO..."
if curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo "MinIO已启动"
fi

echo ""
echo "=== 环境已就绪 ==="
echo ""
echo "Hive Metastore: thrift://localhost:9083"
echo "StarRocks FE: http://localhost:9030"
echo "StarRocks HTTP: http://localhost:8030"
echo "MinIO: http://localhost:9000"
echo ""
echo "测试命令:"
echo "  pytest tests_iceberg_sr/ -v"
echo "  pytest tests_iceberg_sr/ -v -m integration"