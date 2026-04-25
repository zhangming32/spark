#!/bin/bash
set -e

echo "=== 清理Elasticsearch测试环境 ==="

cd "$(dirname "$0")/.."

# 停止服务
echo "停止服务..."
docker-compose down -v

# 清理Docker资源
echo "清理Docker资源..."
docker system prune -f

# 清理测试数据（可选）
read -p "是否清理测试数据? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理测试数据..."
    rm -rf test_data/es_logs/*.json
fi

echo "清理完成"