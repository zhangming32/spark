#!/bin/bash
set -e

echo "=== 启动Elasticsearch测试环境 ==="

cd "$(dirname "$0")/.."

# 启动Docker Compose
echo "启动Docker容器..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查Elasticsearch健康状态
echo "检查Elasticsearch..."
max_retries=20
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:9200/_cluster/health | grep -q "green\|yellow"; then
        echo "Elasticsearch已启动"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "等待Elasticsearch启动... ($retry_count/$max_retries)"
    sleep 5
done

if [ $retry_count -eq $max_retries ]; then
    echo "错误: Elasticsearch启动超时"
    exit 1
fi

# 检查Kibana（可选）
echo "检查Kibana..."
if curl -s http://localhost:5601 > /dev/null 2>&1; then
    echo "Kibana已启动"
else
    echo "Kibana正在启动..."
fi

echo ""
echo "=== Elasticsearch测试环境已就绪 ==="
echo ""
echo "Elasticsearch: http://localhost:9200"
echo "Kibana: http://localhost:5601"
echo ""
echo "测试命令:"
echo "  pytest tests_es/ -v"
echo "  pytest tests_es/ -v -m functional"
echo "  pytest tests_es/ -v -m P1"