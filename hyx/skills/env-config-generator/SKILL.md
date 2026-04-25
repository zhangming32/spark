---
name: env-config-generator
description: 根据测试用例需求生成测试环境配置，包括docker-compose、环境变量、部署脚本等。确保测试环境与生产环境一致。
license: MIT
metadata:
  author: opencode
  version: "1.0"
---

根据测试用例需求生成测试环境配置，确保环境隔离和可重复性。

---

## 输入

### 1. 测试用例JSON（抽象模板）

```json
{
  "test_suite": {
    "components": ["{component_1}", "{component_2}", "{component_3}"],
    "environment_requirements": {
      "{component_1}": {
        "version": "{version}",
        "nodes": {nodes},
        "config": {
          "{config_key}": "{config_value}"
        }
      },
      "{component_2}": {
        "version": "{version}",
        "mode": "{mode}",
        "config": {
          "{config_key}": "{config_value}"
        }
      },
      "{component_3}": {
        "version": "{version}",
        "{config_item}": "{value}"
      }
    }
  }
}
```

### 2. 数据清单JSON

```json
{
  "data_manifest_id": "DM_001",
  "data_files": [
    {
      "file_id": "DF_001",
      "path": "./test_data/processed/input_data.csv",
      "type": "input"
    }
  ]
}
```

---

## 输出

### 环境配置结构（通用模板）

```
environment/
├── docker-compose.yaml          # Docker编排文件
├── .env                         # 环境变量
├── config/                      # 配置文件目录（根据组件动态生成）
│   ├── {component_1}/
│   │   ├── {config_file_1}
│   │   └── {config_file_2}
│   ├── {component_2}/
│   │   ├── {config_file_1}
│   │   └── {config_file_2}
│   └── {component_3}/
│       ├── {config_file_1}
│       └── {config_file_2}
├── scripts/                     # 部署脚本
│   ├── setup_env.sh            # 环境初始化
│   ├── start_services.sh       # 启动服务
│   ├── stop_services.sh        # 停止服务
│   ├── check_health.sh         # 健康检查
│   └── cleanup.sh              # 清理环境
└── test_config.yaml            # 测试配置
```

---

## Docker Compose模板（示例）

以下为典型组件的docker-compose示例模板，实际输出根据用户涉及的组件动态生成：

### docker-compose.yaml示例（包含storage、compute、streaming组件）

```yaml
version: '3.8'

services:
  # Hadoop HDFS
  namenode:
    image: apache/hadoop:3.3.6
    container_name: test-namenode
    hostname: namenode
    environment:
      - HADOOP_CLUSTER_NAME=test-cluster
      - HDFS_NAMENODE_USER=root
    ports:
      - "9870:9870"   # NameNode Web UI
      - "9000:9000"   # NameNode RPC
    volumes:
      - ./config/hdfs:/opt/hadoop/etc/hadoop
      - namenode-data:/hadoop/dfs/name
    command: hdfs namenode
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9870"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - test-network

  datanode:
    image: apache/hadoop:3.3.6
    container_name: test-datanode
    hostname: datanode
    environment:
      - HDFS_DATANODE_USER=root
    ports:
      - "9864:9864"   # DataNode Web UI
      - "9866:9866"   # DataNode Data Transfer
    volumes:
      - ./config/hdfs:/opt/hadoop/etc/hadoop
      - datanode-data:/hadoop/dfs/data
    depends_on:
      namenode:
        condition: service_healthy
    command: hdfs datanode
    networks:
      - test-network

  # Spark
  spark-master:
    image: apache/spark:3.5.0
    container_name: test-spark-master
    hostname: spark-master
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark-master
      - SPARK_MASTER_PORT=7077
      - SPARK_MASTER_WEBUI_PORT=8080
    ports:
      - "8080:8080"   # Spark Master Web UI
      - "7077:7077"   # Spark Master
    volumes:
      - ./config/spark:/opt/spark/conf
      - ./test_data:/test_data
    command: bin/spark-class org.apache.spark.deploy.master.Master
    networks:
      - test-network

  spark-worker:
    image: apache/spark:3.5.0
    container_name: test-spark-worker
    hostname: spark-worker
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER=spark://spark-master:7077
      - SPARK_WORKER_CORES=2
      - SPARK_WORKER_MEMORY=2g
      - SPARK_WORKER_WEBUI_PORT=8081
    ports:
      - "8081:8081"   # Spark Worker Web UI
    volumes:
      - ./config/spark:/opt/spark/conf
      - ./test_data:/test_data
    depends_on:
      - spark-master
    command: bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
    networks:
      - test-network

  # Kafka (可选)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: test-zookeeper
    hostname: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    networks:
      - test-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: test-kafka
    hostname: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
    volumes:
      - ./config/kafka:/etc/kafka
      - kafka-data:/var/lib/kafka/data
    networks:
      - test-network

volumes:
  namenode-data:
  datanode-data:
  kafka-data:

networks:
  test-network:
    driver: bridge
```

---

## 配置文件模板

### 1. HDFS配置

#### core-site.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://namenode:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/tmp/hadoop-${user.name}</value>
    </property>
    <property>
        <name>hadoop.proxyuser.root.hosts</name>
        <value>*</value>
    </property>
    <property>
        <name>hadoop.proxyuser.root.groups</name>
        <value>*</value>
    </property>
</configuration>
```

#### hdfs-site.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.blocksize</name>
        <value>134217728</value> <!-- 128MB -->
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/hadoop/dfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/hadoop/dfs/data</value>
    </property>
    <property>
        <name>dfs.webhdfs.enabled</name>
        <value>true</value>
    </property>
    <property>
        <name>dfs.permissions.enabled</name>
        <value>false</value>
    </property>
</configuration>
```

### 2. Spark配置

#### spark-defaults.conf

```
# Spark Master
spark.master                      spark://spark-master:7077

# Application
spark.app.name                    IntegrationTest
spark.driver.memory               2g
spark.executor.memory            2g
spark.executor.cores             2

# Serialization
spark.serializer                 org.apache.spark.serializer.KryoSerializer

# SQL
spark.sql.warehouse.dir          /tmp/spark-warehouse
spark.sql.shuffle.partitions     10

# UI
spark.ui.enabled                 true
spark.ui.port                    4040

# Event Log
spark.eventLog.enabled           true
spark.eventLog.dir               /tmp/spark-events

# Dynamic Allocation
spark.dynamicAllocation.enabled  false
```

#### spark-env.sh

```bash
#!/bin/bash

# Java
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Spark
export SPARK_MASTER_HOST=spark-master
export SPARK_MASTER_PORT=7077
export SPARK_MASTER_WEBUI_PORT=8080

export SPARK_WORKER_CORES=2
export SPARK_WORKER_MEMORY=2g
export SPARK_WORKER_WEBUI_PORT=8081

# Hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
```

### 3. Kafka配置

#### server.properties

```
# Broker
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://kafka:9092

# Zookeeper
zookeeper.connect=zookeeper:2181

# Log
log.dirs=/var/lib/kafka/data
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

# Replication
num.partitions=3
default.replication.factor=1
offsets.topic.replication.factor=1
transaction.state.log.min.isr=1
transaction.state.log.replication.factor=1

# Group
group.initial.rebalance.delay.ms=0
```

---

## 环境变量

### .env

```bash
# Hadoop
HADOOP_VERSION=3.3.6
HDFS_NAMENODE_USER=root
HDFS_DATANODE_USER=root
HDFS_REPLICATION=1
HDFS_BLOCK_SIZE=134217728

# Spark
SPARK_VERSION=3.5.0
SPARK_MASTER_HOST=spark-master
SPARK_MASTER_PORT=7077
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2

# Kafka
KAFKA_VERSION=7.5.0
KAFKA_BROKER_ID=1
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
KAFKA_NUM_PARTITIONS=3

# Test Data
TEST_DATA_DIR=./test_data
INPUT_DATA_PATH=/test_data/processed/input_data.csv
OUTPUT_DATA_PATH=/test_data/output/result
EXPECTED_DATA_PATH=/test_data/expected/expected_output.csv

# Network
NETWORK_NAME=test-network
```

---

## 部署脚本

### 1. setup_env.sh - 环境初始化

```bash
#!/bin/bash
set -e

echo "=== 测试环境初始化 ==="

# 加载环境变量
source .env

# 创建必要的目录
echo "创建目录结构..."
mkdir -p config/hdfs config/spark config/kafka
mkdir -p test_data/raw test_data/processed test_data/output test_data/expected
mkdir -p scripts
mkdir -p logs

# 生成配置文件
echo "生成配置文件..."

# HDFS配置
cat > config/hdfs/core-site.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://namenode:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/tmp/hadoop-${user.name}</value>
    </property>
</configuration>
EOF

cat > config/hdfs/hdfs-site.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>${HDFS_REPLICATION}</value>
    </property>
    <property>
        <name>dfs.blocksize</name>
        <value>${HDFS_BLOCK_SIZE}</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/hadoop/dfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/hadoop/dfs/data</value>
    </property>
    <property>
        <name>dfs.webhdfs.enabled</name>
        <value>true</value>
    </property>
    <property>
        <name>dfs.permissions.enabled</name>
        <value>false</value>
    </property>
</configuration>
EOF

# Spark配置
cat > config/spark/spark-defaults.conf <<EOF
spark.master                      spark://spark-master:7077
spark.app.name                    IntegrationTest
spark.driver.memory               ${SPARK_DRIVER_MEMORY}
spark.executor.memory            ${SPARK_EXECUTOR_MEMORY}
spark.executor.cores             ${SPARK_EXECUTOR_CORES}
spark.serializer                 org.apache.spark.serializer.KryoSerializer
spark.sql.warehouse.dir          /tmp/spark-warehouse
spark.eventLog.enabled           true
spark.eventLog.dir               /tmp/spark-events
EOF

# Kafka配置
cat > config/kafka/server.properties <<EOF
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://kafka:9092
zookeeper.connect=zookeeper:2181
log.dirs=/var/lib/kafka/data
num.partitions=${KAFKA_NUM_PARTITIONS}
default.replication.factor=1
offsets.topic.replication.factor=1
transaction.state.log.min.isr=1
transaction.state.log.replication.factor=1
group.initial.rebalance.delay.ms=0
EOF

echo "配置文件生成完成！"

# 设置权限
chmod +x scripts/*.sh

echo "环境初始化完成！"
```

### 2. start_services.sh - 启动服务

```bash
#!/bin/bash
set -e

echo "=== 启动测试环境 ==="

# 加载环境变量
source .env

# 启动Docker Compose
echo "启动Docker容器..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查NameNode
echo "检查NameNode..."
until curl -s http://localhost:9870 > /dev/null; do
    echo "等待NameNode启动..."
    sleep 5
done
echo "NameNode已启动"

# 检查DataNode
echo "检查DataNode..."
until curl -s http://localhost:9864 > /dev/null; do
    echo "等待DataNode启动..."
    sleep 5
done
echo "DataNode已启动"

# 检查Spark Master
echo "检查Spark Master..."
until curl -s http://localhost:8080 > /dev/null; do
    echo "等待Spark Master启动..."
    sleep 5
done
echo "Spark Master已启动"

# 检查Spark Worker
echo "检查Spark Worker..."
until curl -s http://localhost:8081 > /dev/null; do
    echo "等待Spark Worker启动..."
    sleep 5
done
echo "Spark Worker已启动"

# 检查Kafka（可选）
if docker ps | grep -q test-kafka; then
    echo "检查Kafka..."
    until docker exec test-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
        echo "等待Kafka启动..."
        sleep 5
    done
    echo "Kafka已启动"
fi

# 创建HDFS目录
echo "创建HDFS测试目录..."
docker exec test-namenode hdfs dfs -mkdir -p /test_data/input
docker exec test-namenode hdfs dfs -mkdir -p /test_data/output
docker exec test-namenode hdfs dfs -mkdir -p /test_data/expected

echo "=== 测试环境已就绪 ==="
echo "NameNode Web UI: http://localhost:9870"
echo "Spark Master Web UI: http://localhost:8080"
echo "Spark Worker Web UI: http://localhost:8081"
```

### 3. stop_services.sh - 停止服务

```bash
#!/bin/bash
set -e

echo "=== 停止测试环境 ==="

# 停止Docker Compose
echo "停止Docker容器..."
docker-compose down

echo "测试环境已停止"
```

### 4. check_health.sh - 健康检查

```bash
#!/bin/bash

echo "=== 服务健康检查 ==="

# 检查NameNode
if curl -s http://localhost:9870 > /dev/null; then
    echo "✓ NameNode: 健康"
else
    echo "✗ NameNode: 不健康"
fi

# 检查DataNode
if curl -s http://localhost:9864 > /dev/null; then
    echo "✓ DataNode: 健康"
else
    echo "✗ DataNode: 不健康"
fi

# 检查Spark Master
if curl -s http://localhost:8080 > /dev/null; then
    echo "✓ Spark Master: 健康"
else
    echo "✗ Spark Master: 不健康"
fi

# 检查Spark Worker
if curl -s http://localhost:8081 > /dev/null; then
    echo "✓ Spark Worker: 健康"
else
    echo "✗ Spark Worker: 不健康"
fi

# 检查Kafka
if docker exec test-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✓ Kafka: 健康"
else
    echo "✗ Kafka: 不健康或未启动"
fi

# 检查ZooKeeper
if docker exec test-zookeeper zkServer.sh status > /dev/null 2>&1; then
    echo "✓ ZooKeeper: 健康"
else
    echo "✗ ZooKeeper: 不健康或未启动"
fi

echo "=== 健康检查完成 ==="
```

### 5. cleanup.sh - 清理环境

```bash
#!/bin/bash
set -e

echo "=== 清理测试环境 ==="

# 停止服务
echo "停止服务..."
./scripts/stop_services.sh

# 清理Docker资源
echo "清理Docker资源..."
docker-compose down -v
docker system prune -f

# 清理测试数据
echo "清理测试数据..."
rm -rf test_data/output/*
rm -rf test_data/processed/*
rm -rf logs/*

# 清理临时文件
echo "清理临时文件..."
rm -rf /tmp/hadoop-*
rm -rf /tmp/spark-*

echo "清理完成"
```

---

## 测试配置文件

### test_config.yaml

```yaml
# 测试环境配置
environment: docker

# HDFS配置
hdfs:
  namenode_url: "http://localhost:9870"
  namenode_host: "namenode"
  namenode_port: 9000
  user: "root"
  base_path: "/test_data"
  
# Spark配置
spark:
  master: "spark://spark-master:7077"
  app_name: "IntegrationTest"
  driver_memory: "2g"
  executor_memory: "2g"
  executor_cores: 2
  config:
    spark.sql.warehouse.dir: "/tmp/spark-warehouse"
    spark.serializer: "org.apache.spark.serializer.KryoSerializer"
    
# Kafka配置（可选）
kafka:
  bootstrap_servers: "localhost:9092"
  zookeeper_connect: "localhost:2181"
  topics:
    - name: "test-topic"
      partitions: 3
      replication_factor: 1
      
# 数据配置
data:
  input_path: "/test_data/input/input_data.csv"
  output_path: "/test_data/output/result"
  expected_path: "/test_data/expected/expected_output.csv"
  local_input_path: "./test_data/processed/input_data.csv"
  local_output_path: "./test_data/output/result"
  
# 测试配置
test:
  timeout: 300
  retry: 3
  parallel: true
  benchmark: true
  
# Web UI
web_ui:
  hdfs: "http://localhost:9870"
  spark_master: "http://localhost:8080"
  spark_worker: "http://localhost:8081"
```

---

## 环境配置生成Prompt

```markdown
你是环境配置专家。请根据以下测试需求生成环境配置：

## 测试用例
{test_cases_json}

## 数据清单
{data_manifest_json}

## 环境要求
{environment_requirements}

## 生成要求

1. **Docker Compose配置**
   - 包含所有需要的组件服务
   - 配置正确的网络和依赖
   - 设置健康检查
   - 映射必要的端口

2. **组件配置文件**
   - HDFS: core-site.xml, hdfs-site.xml
   - Spark: spark-defaults.conf, spark-env.sh
   - Kafka: server.properties
   - 根据测试用例需求调整参数

3. **环境变量**
   - 版本号
   - 资源配置
   - 路径配置
   - 网络配置

4. **部署脚本**
   - 环境初始化
   - 服务启动
   - 服务停止
   - 健康检查
   - 环境清理

5. **测试配置**
   - 集成到pytest的配置文件
   - 数据路径配置
   - 超时和重试配置

请生成完整的环境配置文件。
```

---

## 使用流程

```bash
# 1. 初始化环境
./scripts/setup_env.sh

# 2. 启动服务
./scripts/start_services.sh

# 3. 检查健康
./scripts/check_health.sh

# 4. 运行测试
pytest tests/

# 5. 停止服务
./scripts/stop_services.sh

# 6. 清理环境（可选）
./scripts/cleanup.sh
```

---

## 与其他Skill的协作

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  scenario-planner                                              │
│       │                                                         │
│       │ 输出: test_cases.json (含环境需求)                     │
│       ▼                                                         │
│  data-generator                                                │
│       │                                                         │
│       │ 输出: data_manifest.json                               │
│       ▼                                                         │
│  test-script-generator                                         │
│       │                                                         │
│       │ 输出: test_*.py                                        │
│       ▼                                                         │
│  ┌─────────────────┐                                            │
│  │ env-config-     │                                            │
│  │ generator       │ ◀── 测试用例环境需求                      │
│  │   (本Skill)     │                                            │
│  └─────────────────┘                                            │
│       │                                                         │
│       │ 输出: docker-compose.yaml, 配置文件, 部署脚本         │
│       ▼                                                         │
│  测试环境就绪                                                   │
│       │                                                         │
│       ▼                                                         │
│  执行测试脚本                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```