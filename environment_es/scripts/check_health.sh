#!/bin/bash

echo "=== Elasticsearch健康检查 ==="

# 检查Elasticsearch集群状态
echo "检查Elasticsearch集群..."
response=$(curl -s http://localhost:9200/_cluster/health)

if echo "$response" | grep -q "green\|yellow"; then
    status=$(echo "$response" | grep -o '"status":"[^"]*"')
    echo "✓ Elasticsearch集群: 健康 ($status)"
else
    echo "✗ Elasticsearch集群: 不健康"
fi

# 检查节点数
nodes=$(curl -s http://localhost:9200/_cat/nodes?v | tail -n +2 | wc -l)
echo "节点数: $nodes"

# 检查索引
indices=$(curl -s http://localhost:9200/_cat/indices?v)
echo "索引列表:"
echo "$indices"

# 检查Kibana
if curl -s http://localhost:5601 > /dev/null 2>&1; then
    echo "✓ Kibana: 健康"
else
    echo "✗ Kibana: 不健康或未启动"
fi

echo ""
echo "=== 健康检查完成 ==="