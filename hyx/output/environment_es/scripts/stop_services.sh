#!/bin/bash
set -e

echo "=== 停止Elasticsearch测试环境 ==="

cd "$(dirname "$0")/.."

docker-compose down

echo "测试环境已停止"