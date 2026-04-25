#!/bin/bash
set -e

echo "=== Elasticsearch测试环境初始化 ==="

cd "$(dirname "$0")/.."

# 创建必要的目录
echo "创建目录结构..."
mkdir -p test_data/es_logs/scripts
mkdir -p logs

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 检查端口是否可用
echo "检查端口..."
if lsof -i:9200 &> /dev/null; then
    echo "警告: 端口9200已被占用"
fi

if lsof -i:5601 &> /dev/null; then
    echo "警告: 端口5601已被占用"
fi

# 设置脚本权限
chmod +x scripts/*.sh 2>/dev/null || true

echo "环境初始化完成！"