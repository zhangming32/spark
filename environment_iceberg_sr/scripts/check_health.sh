#!/bin/bash

echo "=== Iceberg-StarRocks健康检查 ==="

# Hive Metastore
if nc -z localhost 9083; then
    echo "✓ Hive Metastore: 健康 (端口9083)"
else
    echo "✗ Hive Metastore: 不健康"
fi

# StarRocks FE
if curl -s http://localhost:9030 > /dev/null 2>&1; then
    echo "✓ StarRocks FE: 健康"
else
    echo "✗ StarRocks FE: 不健康"
fi

# StarRocks HTTP
if curl -s http://localhost:8030 > /dev/null 2>&1; then
    echo "✓ StarRocks HTTP: 健康"
else
    echo "✗ StarRocks HTTP: 不健康"
fi

# MinIO
if curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo "✓ MinIO: 健康"
else
    echo "✗ MinIO: 不健康"
fi

# PostgreSQL
if nc -z localhost 5432; then
    echo "✓ PostgreSQL: 健康"
else
    echo "✗ PostgreSQL: 不健康"
fi

echo "=== 健康检查完成 ==="