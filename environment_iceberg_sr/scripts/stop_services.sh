#!/bin/bash
set -e

echo "=== 停止Iceberg-StarRocks环境 ==="

cd "$(dirname "$0")/.."

docker-compose down

echo "环境已停止"