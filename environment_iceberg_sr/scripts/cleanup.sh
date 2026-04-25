#!/bin/bash
set -e

echo "=== 清理Iceberg-StarRocks环境 ==="

cd "$(dirname "$0")/.."

docker-compose down -v

docker system prune -f

rm -rf test_data/iceberg_sr/*.json
rm -rf test_data/iceberg_sr/*.csv
rm -rf logs/*

echo "清理完成"