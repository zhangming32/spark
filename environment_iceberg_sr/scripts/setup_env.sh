#!/bin/bash
set -e

echo "=== Iceberg-StarRocks环境初始化 ==="

cd "$(dirname "$0")/.."

mkdir -p test_data/iceberg_sr/scripts logs

chmod +x scripts/*.sh 2>/dev/null || true

echo "环境初始化完成！"