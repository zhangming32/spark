# Apache Spark 设计文档

**版本**: Spark 4.x  
**文档日期**: 2026-04-23  
**文档类型**: 综合设计报告

---

## 目录

1. [概述](#1-概述)
2. [系统架构](#2-系统架构)
3. [功能模块清单](#3-功能模块清单)
4. [核心抽象与数据模型](#4-核心抽象与数据模型)
5. [调度系统设计](#5-调度系统设计)
6. [内存与存储管理](#6-内存与存储管理)
7. [容错机制](#7-容错机制)
8. [与其他组件交互关系](#8-与其他组件交互关系)
9. [对外API设计](#9-对外api设计)
10. [第三方生态集成](#10-第三方生态集成)
11. [性能优化策略](#11-性能优化策略)
12. [安全机制](#12-安全机制)
13. [监控与运维](#13-监控与运维)
14. [设计演进历史](#14-设计演进历史)

---

## 1. 概述

### 1.1 项目背景

Apache Spark 源于 UC Berkeley AMPLab 的研究项目，旨在解决 MapReduce 在多轮迭代计算中的性能瓶颈。传统 MapReduce 模型基于无环数据流，每次操作都需要从稳定存储读取和写入数据，导致：

- **迭代算法效率低**：机器学习、图算法（如 PageRank）需要多次数据加载
- **交互式数据挖掘延迟高**：无法在内存中保持数据供多次查询
- **流处理能力不足**：难以维护跨时间的聚合状态

### 1.2 设计目标

| 目标 | 描述 | 实现方案 |
|------|------|----------|
| **高性能** | 内存计算，避免重复 I/O | RDD 内存持久化 |
| **容错性** | 自动恢复节点故障 | Lineage 血统重建 |
| **易用性** | 多语言 API、高层抽象 | Scala/Python/Java/R/SQL |
| **统一引擎** | SQL、ML、流处理、图计算统一 | Spark SQL、MLlib、Streaming、GraphX |
| **可扩展性** | 支持多种集群管理器 | Standalone、YARN、Kubernetes |

### 1.3 核心创新：RDD（Resilient Distributed Dataset）

RDD 是 Spark 的核心抽象，提供：

- **内存持久化**：跨操作保持数据在内存，无需写入磁盘
- **容错重建**：记录数据来源（Lineage），失败时自动重建
- **分布式分区**：数据自动分区到集群节点并行处理
- **惰性执行**：Transformation 操作延迟执行，优化执行计划

### 1.4 版本演进

| 版本 | 时间 | 重要特性 |
|------|------|----------|
| 0.x | 2010-2012 | HotCloud 论文发布，RDD 核心设计 |
| 1.0 | 2014-05 | Spark SQL、DataFrame API |
| 1.3 | 2015-03 | Structured Streaming 预览 |
| 1.6 | 2016-01 | Dataset API |
| 2.0 | 2016-07 | Structured Streaming 正式版、统一 DataFrame/Dataset |
| 2.2 | 2017-07 | 移除 Java 7 支持 |
| 2.4 | 2018-11 | Kubernetes 原生支持 |
| 3.0 | 2020-06 | Adaptive Query Execution (AQE)、Python 3.7+ |
| 3.4 | 2023-04 | Spark Connect 架构 |
| 4.0 | 2024 | Scala 2.13、Java 17/21、Python 3.10+ |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Apache Spark Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────── 应用层 (Application Layer) ─────────────────┐           │
│  │                                                               │           │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │           │
│  │   │ Spark SQL │ │  MLlib   │ │Streaming │ │ GraphX   │       │           │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘       │           │
│  │                                                               │           │
│  │   ┌──────────────────────────────────────────────────┐       │           │
│  │   │           DataFrame / Dataset API                  │       │           │
│  │   └──────────────────────────────────────────────────┘       │           │
│  │                                                               │           │
│  └───────────────────────────────────────────────────────────────┘           │
│                               │                                               │
│                               ▼                                               │
│  ┌───────────────── 核心层 (Core Layer) ───────────────────────┐           │
│  │                                                               │           │
│  │   ┌──────────────────────────────────────────────────────┐   │           │
│  │   │                 SparkContext                           │   │           │
│  │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │   │           │
│  │   │  │DAGSch..│ │TaskSch..│ │Scheduler│ │ContextClean│  │   │           │
│  │   │  │  er    │ │  er     │ │ Backend │ │   er       │  │   │           │
│  │   │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │   │           │
│  │   └──────────────────────────────────────────────────────┘   │           │
│  │                                                               │           │
│  │   ┌──────────────────────────────────────────────────────┐   │           │
│  │   │                   SparkEnv                             │   │           │
│  │   │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │   │           │
│  │   │  │BlockMgr │ │RpcEnv    │ │Serializer│ │MetricsSys│ │   │           │
│  │   │  │  er     │ │          │ │          │ │   tem    │ │   │           │
│  │   │  └─────────┘ └──────────┘ └──────────┘ └──────────┘ │   │           │
│  │   └──────────────────────────────────────────────────────┘   │           │
│  │                                                               │           │
│  │   ┌──────────────────────────────────────────────────────┐   │           │
│  │   │                     RDD                               │   │           │
│  │   │  Transformations: map, filter, reduceByKey, join...  │   │           │
│  │   │  Actions: collect, count, save, reduce...            │   │           │
│  │   └──────────────────────────────────────────────────────┘   │           │
│  │                                                               │           │
│  └───────────────────────────────────────────────────────────────┘           │
│                               │                                               │
│                               ▼                                               │
│  ┌───────────────── 集群层 (Cluster Layer) ───────────────────┐           │
│  │                                                               │           │
│  │   ┌──────────────────────────────────────────────────────┐   │           │
│  │   │                Cluster Manager                         │   │           │
│  │   │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │   │           │
│  │   │  │Standalone │ │   YARN    │ │    Kubernetes     │  │   │           │
│  │   │  └───────────┘ └───────────┘ └───────────────────┘  │   │           │
│  │   └──────────────────────────────────────────────────────┘   │           │
│  │                                                               │           │
│  └───────────────────────────────────────────────────────────────┘           │
│                               │                                               │
│                               ▼                                               │
│  ┌───────────────── 执行层 (Execution Layer) ─────────────────┐           │
│  │                                                               │           │
│  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │           │
│  │   │   Worker 1   │ │   Worker 2   │ │   Worker N   │       │           │
│  │   │  ┌────────┐ │ │  ┌────────┐ │ │  ┌────────┐ │       │           │
│  │   │  │Executor│ │ │  │Executor│ │ │  │Executor│ │       │           │
│  │   │  │ ┌────┐ │ │ │  │ ┌────┐ │ │ │  │ ┌────┐ │ │       │           │
│  │   │  │ │Task│ │ │ │  │ │Task│ │ │ │  │ │Task│ │ │       │           │
│  │   │  │ │ 1  │ │ │ │  │ │ 1  │ │ │ │  │ │ 1  │ │ │       │           │
│  │   │  │ │Task│ │ │ │  │ │Task│ │ │ │  │ │Task│ │ │       │           │
│  │   │  │ │ 2  │ │ │ │  │ │ 2  │ │ │ │  │ │ 2  │ │ │       │           │
│  │   │  │ └────┘ │ │ │  │ └────┘ │ │ │  │ └────┘ │ │       │           │
│  │   │  └────────┘ │ │  └────────┘ │ │  └────────┘ │       │           │
│  │   └──────────────┘ └──────────────┘ └──────────────┘       │           │
│  │                                                               │           │
│  └───────────────────────────────────────────────────────────────┘           │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 运行时组件

#### 2.2.1 Driver Program（驱动程序）

| 组件 | 描述 | 文件位置 |
|------|------|----------|
| **SparkContext** | 主入口点，创建调度器、环境 | `core/src/main/scala/org/apache/spark/SparkContext.scala` |
| **DAGScheduler** | 将 Job 划分为 Stage | `core/src/main/scala/org/apache/spark/scheduler/DAGScheduler.scala` |
| **TaskScheduler** | 分配 Task 到 Executor | `core/src/main/scala/org/apache/spark/scheduler/TaskSchedulerImpl.scala` |
| **SchedulerBackend** | 与集群管理器通信 | `core/src/main/scala/org/apache/spark/scheduler/SchedulerBackend.scala` |

#### 2.2.2 SparkEnv（执行环境）

| 组件 | 描述 |
|------|------|
| **BlockManager** | 数据块存储管理 |
| **RpcEnv** | RPC 通信环境（Netty） |
| **Serializer** | 序列化器（Java/Kryo） |
| **MemoryManager** | 内存分配管理 |
| **MetricsSystem** | 监控指标收集 |
| **BroadcastManager** | 广播变量管理 |
| **MapOutputTracker** | Shuffle 输出位置追踪 |
| **ShuffleManager** | Shuffle 操作管理 |

#### 2.2.3 Executor（执行器）

| 组件 | 描述 |
|------|------|
| **TaskRunner** | 执行具体任务的线程 |
| **BlockManager** | 本地数据块存储 |
| **MemoryStore** | 内存存储 |
| **DiskStore** | 磁盘存储 |

### 2.3 术语定义

| 术语 | 定义 |
|------|------|
| **Application** | 用户 Spark 程序，包含 Driver 和 Executor |
| **Driver Program** | 运行 main() 并创建 SparkContext 的进程 |
| **Cluster Manager** | 资源分配服务（Standalone/YARN/K8s） |
| **Worker Node** | 可运行应用代码的集群节点 |
| **Executor** | Worker 上运行的进程，执行 Task 并存储数据 |
| **Task** | 发送到 Executor 的工作单元 |
| **Job** | Spark Action 触发的并行计算（由多个 Task 组成） |
| **Stage** | Job 的子任务集，Stage 之间有依赖关系 |
| **RDD** | 弹性分布式数据集，Spark 核心抽象 |
| **Partition** | RDD 的数据分片 |
| **Shuffle** | 数据重分区操作（跨节点数据交换） |

---

## 3. 功能模块清单

### 3.1 Spark Core

核心运行引擎，提供分布式计算基础能力。

#### 3.1.1 RDD API

| 功能类别 | API | 描述 |
|----------|-----|------|
| **创建** | `parallelize()`, `textFile()`, `hadoopRDD()` | 从集合/文件创建 RDD |
| **Transformation** | `map`, `filter`, `flatMap`, `mapPartitions` | 转换操作（惰性执行） |
| **Key-Value** | `reduceByKey`, `groupByKey`, `join`, `cogroup` | 键值对操作 |
| **Shuffle** | `repartition`, `coalesce`, `partitionBy` | 分区操作 |
| **Action** | `collect`, `count`, `reduce`, `saveAsTextFile` | 触发执行的操作 |
| **Persistence** | `cache()`, `persist()`, `unpersist()` | 内存/磁盘持久化 |

#### 3.1.2 共享变量

| 类型 | API | 用途 |
|------|-----|------|
| **Broadcast Variable** | `broadcast()` | 向所有节点分发只读变量 |
| **Accumulator** | `longAccumulator()`, `doubleAccumulator()`, `collectionAccumulator()` | 跨任务累加变量 |

#### 3.1.3 调度控制

| API | 描述 |
|-----|------|
| `setJobGroup()` | 设置作业组，便于管理和取消 |
| `cancelJob()`, `cancelJobGroup()` | 取消作业 |
| `setLocalProperty()` | 设置线程级本地属性 |
| `requestExecutors()`, `killExecutors()` | 动态资源管理 |

### 3.2 Spark SQL

结构化数据处理模块。

#### 3.2.1 DataFrame/Dataset API

| API | 描述 |
|-----|------|
| `select()`, `filter()`, `where()` | 选择和过滤 |
| `groupBy()`, `agg()` | 聚合操作 |
| `join()`, `union()`, `intersect()` | 集合操作 |
| `withColumn()`, `drop()` | 列操作 |
| `createOrReplaceTempView()` | 创建临时视图 |

#### 3.2.2 SQL 支持

```sql
-- 支持 ANSI SQL 标准
SELECT col1, SUM(col2) FROM table GROUP BY col1
INSERT INTO table VALUES (...)
CREATE TABLE ... USING parquet
```

#### 3.2.3 Catalyst 优化器

| 阶段 | 功能 |
|------|------|
| **解析** | SQL -> Unresolved Logical Plan |
| **分析** | Unresolved -> Resolved Logical Plan |
| **优化** | Logical Plan -> Optimized Logical Plan |
| **物理规划** | Optimized Logical Plan -> Physical Plan |
| **代码生成** | Physical Plan -> RDD 执行代码 |

### 3.3 Structured Streaming

流处理模块，基于 DataFrame API。

#### 3.3.1 输入源

| 源类型 | 描述 |
|--------|------|
| `socket` | Socket 文本流 |
| `file` | 文件流（自动检测新文件） |
| `kafka` | Kafka 消息流 |
| `rate` | 测试数据生成器 |

#### 3.3.2 输出模式

| 模式 | 描述 |
|------|------|
| `append` | 只输出新数据 |
| `complete` | 输出完整结果集 |
| `update` | 输出更新的行 |

#### 3.3.3 触发器

| 触发器 | 描述 |
|--------|------|
| `ProcessingTime(interval)` | 固定间隔触发 |
| `ContinuousTrigger(interval)` | 连续处理模式 |
| `Once()` | 单次执行 |
| `AvailableNow()` | 处理所有可用数据 |

### 3.4 MLlib

机器学习库。

#### 3.4.1 算法分类

| 类别 | 算法 |
|------|------|
| **分类** | LogisticRegression, DecisionTree, RandomForest, GBTClassifier, NaiveBayes |
| **回归** | LinearRegression, DecisionTreeRegressor, RandomForestRegressor, GBTRegressor |
| **聚类** | KMeans, BisectingKMeans, GaussianMixture, LDA |
| **协同过滤** | ALS |
| **降维** | PCA |
| **特征工程** | Tokenizer, HashingTF, Word2Vec, OneHotEncoder, StandardScaler |
| **管道** | Pipeline, PipelineModel |

### 3.5 GraphX

图计算引擎。

#### 3.5.1 核心抽象

| 抽象 | 描述 |
|------|------|
| **Graph** | 属性图（VertexRDD + EdgeRDD） |
| **VertexRDD** | 顶点集合 |
| **EdgeRDD** | 边集合 |

#### 3.5.2 图操作

| API | 描述 |
|-----|------|
| `mapVertices()`, `mapEdges()` | 映射变换 |
| `subgraph()` | 子图提取 |
| `joinVertices()` | 顶点数据连接 |
| `aggregateMessages()` | 消息聚合 |
| `pageRank()` | PageRank 算法 |
| `connectedComponents()` | 连通分量 |
| `triangleCount()` | 三角计数 |

### 3.6 Spark Connect

客户端-服务器架构分离（Spark 3.4+）。

| 特性 | 描述 |
|------|------|
| **远程连接** | 客户端无需本地 Spark 环境 |
| **轻量客户端** | 减少客户端依赖 |
| **多语言支持** | PySpark、Scala、Go、Rust、Swift |
| **协议** | 基于 Protobuf 的 RPC |

---

## 4. 核心抽象与数据模型

### 4.1 RDD（Resilient Distributed Dataset）

#### 4.1.1 RDD 属性

```scala
abstract class RDD[T](
    var prev: RDD[_],           // 父 RDD（Lineage）
    var deps: Seq[Dependency[_]], // 依赖关系
    var partitions: Array[Partition], // 分区数组
    var partitioner: Option[Partitioner], // 分区器
    var preferredLocations: Map[Int, Seq[String]] // 位置偏好
) {
    def compute(split: Partition, context: TaskContext): Iterator[T]
    def getPartitions: Array[Partition]
    def getDependencies: Seq[Dependency[_]]
    def getPreferredLocations(split: Partition): Seq[String]
}
```

#### 4.1.2 RDD 类型

| RDD 类型 | 描述 | 创建方式 |
|----------|------|----------|
| **ParallelCollectionRDD** | 从集合创建 | `parallelize()` |
| **HadoopRDD** | 从 Hadoop 文件创建 | `textFile()`, `hadoopFile()` |
| **MapPartitionsRDD** | 转换操作结果 | `map()`, `filter()` |
| **ShuffledRDD** | Shuffle 操作结果 | `reduceByKey()`, `groupByKey()` |
| **CoGroupedRDD** | CoGroup 结果 | `cogroup()` |
| **UnionRDD** | 合并结果 | `union()` |

#### 4.1.3 依赖类型

| 依赖类型 | 描述 | Shuffle |
|----------|------|---------|
| **NarrowDependency** | 父分区对应固定子分区 | 无 |
| **ShuffleDependency** | 父分区对应不确定子分区 | 有 |

### 4.2 DataFrame/Dataset

#### 4.2.1 DataFrame

```scala
type DataFrame = Dataset[Row]  // Scala
class DataFrame extends Dataset[Row]  // Java/Python
```

| 特性 | 描述 |
|------|------|
| **结构化** | 列名和类型已知 |
| **优化执行** | Catalyst 优化器 |
| **API 统一** | 与 SQL 可互换 |

#### 4.2.2 Dataset

```scala
class Dataset[T] {
    def rdd: RDD[T]              // 转换为 RDD
    def queryExecution: QueryExecution // 查询执行计划
    def sparkSession: SparkSession // Spark 会话
}
```

### 4.3 Partitioner

分区策略决定数据分布。

| Partitioner | 描述 |
|-------------|------|
| **HashPartitioner** | 基于键哈希值分区 |
| **RangePartitioner** | 基于键范围分区 |
| **Custom Partitioner** | 用户自定义分区器 |

---

## 5. 调度系统设计

### 5.1 调度层次

```
┌─────────────────────────────────────────────────────────┐
│                    Spark 调度层次                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  用户代码                                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌──────────────┐                                        │
│  │ SparkContext │                                        │
│  │   runJob()   │                                        │
│  └──────────────┘                                        │
│      │                                                   │
│      ▼                                                   │
│  ┌──────────────┐                                        │
│  │ DAGScheduler │ ← Stage 级调度                         │
│  │              │   - 构建 DAG                           │
│  │              │   - 划分 Stage                         │
│  │              │   - 提交 TaskSet                       │
│  └──────────────┘                                        │
│      │                                                   │
│      ▼                                                   │
│  ┌──────────────┐                                        │
│  │TaskScheduler │ ← Task 级调度                          │
│  │    Impl      │   - 分配 Task 到 Executor              │
│  │              │   - 推测执行                           │
│  │              │   - 失败重试                           │
│  └──────────────┘                                        │
│      │                                                   │
│      ▼                                                   │
│  ┌──────────────┐                                        │
│  │SchedulerBackend│ ← 与集群管理器交互                   │
│  │              │   - 资源请求                           │
│  │              │   - Executor 管理                      │
│  └──────────────┘                                        │
│      │                                                   │
│      ▼                                                   │
│  ┌──────────────┐                                        │
│  │ClusterManager│ ← YARN/K8s/Standalone                  │
│  └──────────────┘                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.2 DAGScheduler

#### 5.2.1 Stage 划分规则

```
Job = Action 触发
Stage = Shuffle 边界划分
Task = 每个 Partition 一个
```

| Stage 类型 | 描述 |
|------------|------|
| **ShuffleMapStage** | 中间 Stage，输出供下游使用 |
| **ResultStage** | 最终 Stage，计算 Action 结果 |

#### 5.2.2 核心方法

| 方法 | 描述 |
|------|------|
| `runJob()` | 提交 Job 执行 |
| `submitStage()` | 提交 Stage |
| `submitMissingTasks()` | 提交缺失 Task |
| `handleTaskCompletion()` | 处理 Task 完成 |
| `handleStageFailure()` | 处理 Stage 失败 |

### 5.3 TaskScheduler

#### 5.3.1 调度模式

| 模式 | 描述 |
|------|------|
| **FIFO** | 先进先出 |
| **FAIR** | 公平调度（按 Pool 分配） |

#### 5.3.2 推测执行

| 配置 | 描述 |
|------|------|
| `spark.speculation=true` | 开启推测执行 |
| `spark.speculation.interval` | 检查间隔 |
| `spark.speculation.multiplier` | 触发阈值倍数 |

### 5.4 SchedulerBackend 类型

| Backend | 集群管理器 | 描述 |
|---------|------------|------|
| **LocalSchedulerBackend** | local | 本地单机执行 |
| **StandaloneSchedulerBackend** | Standalone | Spark 内置集群 |
| **CoarseGrainedSchedulerBackend** | YARN/K8s | 细粒度资源调度 |

---

## 6. 内存与存储管理

### 6.1 BlockManager

数据块存储管理核心组件。

#### 6.1.1 存储层次

```
┌─────────────────────────────────────────────────────────┐
│                  BlockManager 存储层次                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  Memory Store                     │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │         Execution Memory (60%)              │ │   │
│  │  │    - Shuffle/Join/Sort/Aggregation          │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │         Storage Memory (40%)               │ │   │
│  │  │    - RDD Cache/Broadcast Variables         │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  Disk Store                       │   │
│  │  - 本地磁盘存储                                   │   │
│  │  - Shuffle 中间数据                               │   │
│  │  - 持久化到磁盘的 RDD                             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              External Block Store                 │   │
│  │  - Tachyon/Alluxio                                │   │
│  │  - 分布式内存存储                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 6.1.2 StorageLevel

| StorageLevel | 描述 | 使用场景 |
|---------------|------|----------|
| `MEMORY_ONLY` | 仅内存，不序列化 | 内存充足 |
| `MEMORY_ONLY_SER` | 仅内存，序列化 | 内存受限，对象大 |
| `MEMORY_AND_DISK` | 内存优先，溢出到磁盘 | 内存不确定 |
| `MEMORY_AND_DISK_SER` | 内存优先，序列化，溢出磁盘 | 内存受限 |
| `DISK_ONLY` | 仅磁盘 | 内存严重不足 |
| `MEMORY_ONLY_2` | 内存 + 2副本 | 高容错需求 |
| `OFF_HEAP` | 堆外内存 | 避免GC开销 |

### 6.2 MemoryManager

#### 6.2.1 内存分配

| 区域 | 比例 | 用途 |
|------|------|------|
| **Execution Memory** | 60% | Shuffle、Join、Sort、Aggregation |
| **Storage Memory** | 40% | RDD Cache、Broadcast |
| **System Reserved** | 300MB | Spark 内部使用 |

#### 6.2.2 内存配置

| 配置项 | 描述 |
|--------|------|
| `spark.executor.memory` | Executor 内存总量 |
| `spark.memory.fraction` | 执行+存储内存比例（默认0.75） |
| `spark.memory.storageFraction` | 存储内存边界（默认0.5） |
| `spark.executor.memoryOverhead` | 堆外内存开销 |

---

## 7. 容错机制

### 7.1 Lineage 血统机制

RDD 记录其构建过程，失败时可重建。

```
RDD Lineage 示例：

textFile("hdfs://...")
    │
    ▼ map(s => s.length)
    │
    ▼ filter(x => x > 10)
    │
    ▼ reduceByKey((a,b) => a+b)
    │
    ▼
Result RDD

如果某个 Partition 丢失：
→ 根据血缘关系重建
→ 从祖先 RDD 重新计算
```

### 7.2 失败恢复策略

| 失败类型 | 恢复策略 |
|----------|----------|
| **Task 失败** | 重试（最多4次） |
| **Stage 失败** | 重试整个 Stage |
| **Executor 失败** | 在其他 Executor 重试 |
| **Driver 失败** | 需集群模式支持自动恢复 |

### 7.3 Checkpoint 检查点

将 RDD 写入可靠存储，截断 Lineage。

```scala
sc.setCheckpointDir("hdfs://checkpoint-dir")
rdd.checkpoint()
```

| 配置 | 描述 |
|------|------|
| `spark.checkpoint.dir` | 检查点目录 |

### 7.4 Write Ahead Log (WAL)

Structured Streaming 使用 WAL 确保可靠性。

| 配置 | 描述 |
|------|------|
| `spark.sql.streaming.checkpointLocation` | 流处理检查点位置 |

---

## 8. 与其他组件交互关系

### 8.1 集群管理器集成

#### 8.1.1 Standalone 模式

```
┌─────────────────────────────────────────────────────────┐
│                 Standalone Cluster                       │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Master (spark://host:port)            │  │
│  │  - 资源分配                                        │  │
│  │  - Worker 管理                                     │  │
│  │  - Application 管理                                │  │
│  └───────────────────────────────────────────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │   Worker 1   │ │   Worker 2   │ │   Worker N   │    │
│  │              │ │              │ │              │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

| 配置 | 描述 |
|------|------|
| `spark.master=spark://host:port` | Master 地址 |
| `SPARK_MASTER_PORT` | Master 端口 |
| `SPARK_WORKER_CORES` | Worker 核数 |
| `SPARK_WORKER_MEMORY` | Worker 内存 |

#### 8.1.2 YARN 模式

```
┌─────────────────────────────────────────────────────────┐
│                     YARN 集成                            │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              ResourceManager                       │  │
│  └───────────────────────────────────────────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │              ApplicationMaster                     │  │
│  │  - 向 RM 申请资源                                   │  │
│  │  - 启动 Executor                                   │  │
│  │  - 监控 Executor                                    │  │
│  └───────────────────────────────────────────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ NodeManager  │ │ NodeManager  │ │ NodeManager  │    │
│  │  ┌────────┐ │ │  ┌────────┐ │ │  ┌────────┐ │    │
│  │  │Executor│ │ │  │Executor│ │ │  │Executor│ │    │
│  │  └────────┘ │ │  └────────┘ │ │  └────────┘ │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

| 部署模式 | 描述 |
|----------|------|
| **yarn-client** | Driver 在客户端 |
| **yarn-cluster** | Driver 在 AM 中 |

#### 8.1.3 Kubernetes 模式

```
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes 集成                         │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │                 Kubernetes API Server              │  │
│  └───────────────────────────────────────────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │                 Spark Driver Pod                   │  │
│  │  - 运行 SparkContext                               │  │
│  │  - 与 K8s API 交互                                 │  │
│  └───────────────────────────────────────────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │Executor Pod 1│ │Executor Pod 2│ │Executor Pod N│    │
│  │              │ │              │ │              │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

| 配置 | 描述 |
|------|------|
| `spark.master=k8s://...` | K8s API Server 地址 |
| `spark.kubernetes.container.image` | Spark 容器镜像 |
| `spark.kubernetes.namespace` | K8s namespace |

### 8.2 数据源集成

#### 8.2.1 内置数据源

| 数据源 | 格式 | API |
|--------|------|-----|
| **HDFS** | 文件 | `textFile()`, `hadoopFile()` |
| **Local FS** | 文件 | `textFile()` |
| **Parquet** | 列式 | `spark.read.parquet()` |
| **ORC** | 列式 | `spark.read.orc()` |
| **Avro** | 行式 | `spark.read.avro()` |
| **JSON** | 文本 | `spark.read.json()` |
| **CSV** | 文本 | `spark.read.csv()` |
| **Hive** | 表 | `spark.read.table()` |
| **JDBC** | 数据库 | `spark.read.jdbc()` |

#### 8.2.2 第三方连接器

| 连接器 | 数据源 |
|--------|--------|
| **spark-redshift** | Amazon Redshift |
| **mongo-spark** | MongoDB |
| **cassandra-spark** | Cassandra |
| **elasticsearch-hadoop** | Elasticsearch |
| **neo4j-spark-connector** | Neo4j |
| **azure-cosmos-spark** | Azure Cosmos DB |
| **kafka** | Kafka（内置） |
| **hbase-spark** | Apache HBase |

#### 8.2.3 HBase 详细集成说明

Apache HBase 是基于 Hadoop 的分布式列式 NoSQL 数据库，Spark 通过 `hbase-spark` 连接器实现读写操作。

**HBase 与 Spark 交互架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Spark + HBase 集成架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Spark Application                  │   │
│  │  ┌───────────────────────────────────────────────┐ │   │
│  │  │               SparkSession                      │ │   │
│  │  │  .read.format("hbase")                         │ │   │
│  │  │  .option("hbase.columns.mapping", ...)         │ │   │
│  │  │  .option("hbase.table", "table_name")          │ │   │
│  │  │  .load()                                       │ │   │
│  │  └───────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              hbase-spark Connector                   │   │
│  │  - DataFrame/Dataset API                             │   │
│  │  - RDD API (HBaseInputFormat/HBaseOutputFormat)     │   │
│  │  - Bulk Put/Delete                                   │   │
│  │  - Scan Filter 推送                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Apache HBase                          │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │              HMaster (Master)                  │  │   │
│  │  │  - Region 分配                                 │  │   │
│  │  │  - 表管理                                      │  │   │
│  │  │  - 负载均衡                                    │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │   │
│  │  │ RegionServer │ │ RegionServer │ │ RegionServer │ │   │
│  │  │  ┌────────┐ │ │  ┌────────┐ │ │  ┌────────┐ │ │   │
│  │  │  │Region 1│ │ │  │Region 2│ │ │  │Region N│ │ │   │
│  │  │  │┌──────┐│ │ │  │┌──────┐│ │ │  │┌──────┐│ │ │   │
│  │  │  ││Store ││ │ │  ││Store ││ │ │  ││Store ││ │ │   │
│  │  │  ││┌────┐││ │ │  ││┌────┐││ │ │  ││┌────┐││ │ │   │
│  │  │  │││HFile│││ │ │  │││HFile│││ │ │  │││HFile│││ │ │   │
│  │  │  ││└────┘││ │ │  ││└────┘││ │ │  ││└────┘││ │ │   │
│  │  │  │└──────┘│ │ │  │└──────┘│ │ │  │└──────┘│ │ │   │
│  │  │  └────────┘ │ │  └────────┘ │ │  └────────┘ │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │               HDFS (底层存储)                   │  │   │
│  │  │  - HFile 文件存储                               │  │   │
│  │  │  - WAL (Write-Ahead Log)                        │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**集成方式：**

| 方式 | 描述 | API |
|------|------|-----|
| **DataFrame API** | 通过 DataSource API 读写 | `spark.read.format("hbase")` |
| **RDD API** | 使用 Hadoop InputFormat | `newAPIHadoopRDD()` |
| **Bulk 操作** | 批量写入/删除 | `hbaseRDD.bulkPut()`, `hbaseRDD.bulkDelete()` |

**DataFrame API 示例：**

```scala
// 读取 HBase 表
val df = spark.read
    .format("org.apache.hadoop.hbase.spark")
    .option("hbase.table", "my_table")
    .option("hbase.columns.mapping", "cf1:col1 STRING, cf1:col2 INT, cf2:col3 DOUBLE")
    .load()

// 写入 HBase 表
df.write
    .format("org.apache.hadoop.hbase.spark")
    .option("hbase.table", "my_table")
    .option("hbase.columns.mapping", "cf1:col1, cf1:col2, cf2:col3")
    .save()
```

**RDD API 示例：**

```scala
import org.apache.hadoop.hbase.{HBaseConfiguration, TableName}
import org.apache.hadoop.hbase.client.{ConnectionFactory, Put, Scan}
import org.apache.hadoop.hbase.mapreduce.{TableInputFormat, TableOutputFormat}
import org.apache.hadoop.hbase.io.ImmutableBytesWritable
import org.apache.hadoop.hbase.util.Bytes

// 配置 HBase
val hbaseConf = HBaseConfiguration.create()
hbaseConf.set("hbase.zookeeper.quorum", "zk1,zk2,zk3")
hbaseConf.set(TableInputFormat.INPUT_TABLE, "my_table")

// 读取 HBase 表为 RDD
val hbaseRDD = sc.newAPIHadoopRDD(
    hbaseConf,
    classOf[TableInputFormat],
    classOf[ImmutableBytesWritable],
    classOf[org.apache.hadoop.hbase.client.Result]
)

// 写入 HBase 表
hbaseConf.set(TableOutputFormat.OUTPUT_TABLE, "my_table")
rdd.map(row => {
    val put = new Put(Bytes.toBytes(row._1))
    put.addColumn(Bytes.toBytes("cf"), Bytes.toBytes("col"), Bytes.toBytes(row._2))
    (new ImmutableBytesWritable, put)
}).saveAsNewAPIHadoopDataset(hbaseConf)
```

**主要配置参数：**

| 配置 | 描述 |
|------|------|
| `hbase.zookeeper.quorum` | ZooKeeper 集群地址 |
| `hbase.zookeeper.property.clientPort` | ZooKeeper 端口（默认2181） |
| `hbase.table` | HBase 表名 |
| `hbase.columns.mapping` | 列映射配置 |
| `hbase.rowkey.mapping` | RowKey 映射 |
| `hbase.spark.use.hbase.context` | 是否使用 HBaseContext |

**HBaseContext 高级 API：**

```scala
import org.apache.hadoop.hbase.spark.HBaseContext

val hbaseContext = new HBaseContext(sc, hbaseConf)

// Bulk Put
hbaseContext.bulkPut(rdd, TableName.valueOf("my_table"), 
    (row, put) => {
        put.addColumn(Bytes.toBytes("cf"), Bytes.toBytes("col"), Bytes.toBytes(row))
    })

// Bulk Delete
hbaseContext.bulkDelete(rdd, TableName.valueOf("my_table"), 
    (row) => new Delete(Bytes.toBytes(row)))

// Scan 并返回 RDD
val scan = new Scan()
val resultRDD = hbaseContext.hbaseScanRDD(TableName.valueOf("my_table"), scan)
```

**优化策略：**

| 策略 | 描述 |
|------|------|
| **Scan Filter 推送** | 将 Spark 过滤条件推送到 HBase Server 端 |
| **Region 分区并行** | 每个 HBase Region 对应一个 Spark Partition |
| **Bulk 加载** | 使用 HFile Bulk Load 加速批量写入 |
| **缓存策略** | 对频繁读取的数据使用 RDD cache |

**依赖配置：**

```xml
<dependency>
    <groupId>org.apache.hbase</groupId>
    <artifactId>hbase-spark</artifactId>
    <version>${hbase.version}</version>
</dependency>
<dependency>
    <groupId>org.apache.hbase</groupId>
    <artifactId>hbase-client</artifactId>
    <version>${hbase.version}</version>
</dependency>
```

**典型应用场景：**

| 场景 | 描述 |
|------|------|
| **实时数据仓库** | HBase 存储实时数据，Spark 周期性批处理分析 |
| **CDC 数据同步** | HBase 作为 CDC 源，Spark 处理变更数据 |
| **机器学习特征存储** | HBase 存储特征数据，Spark 进行特征工程 |
| **实时推荐系统** | HBase 存储用户画像，Spark 计算推荐结果 |
| **日志分析** | HBase 存储实时日志，Spark 进行历史分析 |

### 8.3 表格式集成

| 表格式 | 特性 |
|--------|------|
| **Delta Lake** | ACID 事务、时间旅行、Schema演进 |
| **Apache Hudi** | Upsert、增量处理 |
| **Apache Iceberg** | Schema演进、分区演进、隐藏分区 |
| **Lance** | ML/LLM 列式格式 |

### 8.4 生态系统集成

| 类别 | 工具 | 集成方式 |
|------|------|----------|
| **工作流调度** | Apache Airflow | SparkSubmitOperator |
| **数据转换** | dbt-spark | dbt adapter |
| **ML平台** | MLflow | Spark MLlib集成 |
| **Notebook** | Zeppelin | Spark interpreter |
| **SQL Gateway** | Kyuubi | 多租户SQL服务 |
| **数据质量** | python-deequ | PySpark集成 |

---

## 9. 对外API设计

### 9.1 语言绑定

| 语言 | API 包 | 入口类 |
|------|--------|--------|
| **Scala** | `org.apache.spark.*` | `SparkContext`, `SparkSession` |
| **Python** | `pyspark.*` | `SparkContext`, `SparkSession` |
| **Java** | `org.apache.spark.api.java.*` | `JavaSparkContext` |
| **R** | `SparkR::*` | `sparkR.session()` |
| **SQL** | ANSI SQL | `spark.sql()` |

### 9.2 SparkContext API

#### 9.2.1 初始化

```scala
// Scala
val conf = new SparkConf()
    .setAppName("MyApp")
    .setMaster("spark://host:port")
val sc = new SparkContext(conf)

// Python
from pyspark import SparkContext, SparkConf
conf = SparkConf().setAppName("MyApp").setMaster("local[*]")
sc = SparkContext(conf=conf)

// Java
SparkConf conf = new SparkConf().setAppName("MyApp").setMaster("local");
JavaSparkContext sc = new JavaSparkContext(conf);
```

#### 9.2.2 RDD 创建

| 方法 | 描述 |
|------|------|
| `parallelize(seq, numSlices)` | 从集合创建 |
| `textFile(path, minPartitions)` | 读取文本文件 |
| `hadoopFile(path, format, keyClass, valueClass)` | 读取 Hadoop 文件 |
| `wholeTextFiles(path)` | 读取整个文本文件 |
| `binaryFiles(path)` | 读取二进制文件 |
| `sequenceFile(path)` | 读取 SequenceFile |
| `newAPIHadoopRDD()` | 新 API Hadoop RDD |

#### 9.2.3 共享变量

| 方法 | 描述 |
|------|------|
| `broadcast(value)` | 创建广播变量 |
| `longAccumulator()` | 创建 Long 累加器 |
| `doubleAccumulator()` | 创建 Double 累加器 |
| `collectionAccumulator()` | 创建集合累加器 |

#### 9.2.4 资源管理

| 方法 | 描述 |
|------|------|
| `addJar(path)` | 添加 JAR 依赖 |
| `addFile(path)` | 添加文件依赖 |
| `requestExecutors(num)` | 请求数据 Executor |
| `killExecutors(ids)` | 杀死 Executor |
| `getExecutorMemoryStatus` | 获取 Executor 内存状态 |

#### 9.2.5 Job 管理

| 方法 | 描述 |
|------|------|
| `setJobGroup(id, desc, interrupt)` | 设置 Job 组 |
| `cancelJob(id)` | 取消 Job |
| `cancelJobGroup(id)` | 取消 Job 组 |
| `setLogLevel(level)` | 设置日志级别 |
| `stop()` | 停止 SparkContext |

### 9.3 SparkSession API

#### 9.3.1 初始化

```scala
val spark = SparkSession.builder()
    .appName("MyApp")
    .master("local[*]")
    .config("spark.some.config", "value")
    .getOrCreate()
```

#### 9.3.2 DataFrame/Dataset 操作

| 方法 | 描述 |
|------|------|
| `read.format(...).load()` | 读取数据源 |
| `createDataFrame(rdd)` | 从 RDD 创建 |
| `createDataset(seq)` | 从集合创建 Dataset |
| `sql(query)` | 执行 SQL 查询 |
| `table(name)` | 获取表 DataFrame |
| `udf.register(name, func)` | 注册 UDF |

### 9.4 DataFrame/Dataset API

#### 9.4.1 Transformation

| API | 描述 |
|-----|------|
| `select(col*)` | 选择列 |
| `filter(condition)` | 过滤行 |
| `groupBy(col*)` | 分组 |
| `agg(expr*)` | 聚合 |
| `join(other, condition)` | 连接 |
| `union(other)` | 合并 |
| `withColumn(name, expr)` | 添加/替换列 |
| `drop(col*)` | 删除列 |
| `distinct()` | 去重 |
| `limit(n)` | 限制行数 |
| `orderBy(col*)` | 排序 |
| `repartition(n)` | 重分区 |

#### 9.4.2 Action

| API | 描述 |
|-----|------|
| `collect()` | 收集所有行 |
| `count()` | 计数 |
| `first()` | 第一行 |
| `take(n)` | 取前 n 行 |
| `show(n)` | 显示 n 行 |
| `head(n)` | 头 n 行 |
| `write.format(...).save(path)` | 写入数据源 |
| `createOrReplaceTempView(name)` | 创建临时视图 |
| `foreach(func)` | 遍历每行 |
| `reduce(func)` | 归约 |

### 9.5 Streaming API

```scala
val stream = spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "host:port")
    .option("subscribe", "topic")
    .load()

val result = stream
    .groupBy("key")
    .count()

result.writeStream
    .outputMode("complete")
    .format("console")
    .start()
```

### 9.6 MLlib API

```scala
import org.apache.spark.ml.classification.LogisticRegression
import org.apache.spark.ml.feature.{Tokenizer, HashingTF}
import org.apache.spark.ml.Pipeline

val pipeline = new Pipeline()
    .setStages(Array(
        new Tokenizer().setInputCol("text").setOutputCol("words"),
        new HashingTF().setNumFeatures(1000).setInputCol("words").setOutputCol("features"),
        new LogisticRegression().setMaxIter(10).setRegParam(0.01)
    ))

val model = pipeline.fit(trainingData)
val predictions = model.transform(testData)
```

---

## 10. 第三方生态集成

### 10.1 连接器生态

| 数据源 | 连接器项目 | GitHub |
|--------|------------|---------|
| **Redshift** | spark-redshift | spark-redshift-community/spark-redshift |
| **MongoDB** | mongo-spark | mongodb/mongo-spark |
| **Cassandra** | spark-cassandra-connector | datastax/spark-cassandra-connector |
| **Elasticsearch** | elasticsearch-hadoop | elastic/elasticsearch-hadoop |
| **Neo4j** | neo4j-spark-connector | neo4j-contrib/neo4j-spark-connector |
| **Azure Cosmos DB** | azure-cosmos-spark | Azure/azure-cosmosdb-spark |
| **Azure Event Hubs** | azure-event-hubs-spark | Azure/azure-event-hubs-spark |
| **ClickHouse** | spark-clickhouse-connector | ClickHouse/spark-clickhouse-connector |
| **TiDB/TiKV** | tispark | pingcap/tispark |
| **OceanBase** | spark-connector-oceanbase | oceanbase/spark-connector-oceanbase |
| **Lance** | lance-spark | lancedb/lance-spark |
| **SQL Server** | sql-spark-connector | microsoft/sql-spark-connector |
| **HBase** | hbase-spark | apache/hbase-spark |
| **MySQL** | jdbc | 内置 JDBC |
| **PostgreSQL** | jdbc | 内置 JDBC |
| **Oracle** | jdbc | 内置 JDBC |
| **Snowflake** | snowflake-spark | snowflakedb/snowflake-spark |
| **BigQuery** | spark-bigquery | GoogleCloudPlatform/spark-bigquery |
| **Pulsar** | pulsar-spark | apache/pulsar-spark |
| **Druid** | spark-druid | apache/druid |
| **Pinot** | spark-pinot | apache/pinot |
| **Solr** | spark-solr | lucidworks/spark-solr |
| **Redis** | spark-redis | RedisLabs/spark-redis |
| **Presto/Trino** | spark-trino | 自定义JDBC |
| **Alluxio** | spark-alluxio | alluxio/alluxio |

### 10.2 重要组件交互详解

#### 10.2.1 ZooKeeper 协调服务

ZooKeeper 是 Spark 集群 HA 和协调的关键组件。

```
┌─────────────────────────────────────────────────────────────┐
│              Spark + ZooKeeper 协调架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ZooKeeper Ensemble (集群)                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │  ZK 1    │ │  ZK 2    │ │  ZK 3    │            │   │
│  │  │ (Leader) │ │(Follower)│ │(Follower)│            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Spark 使用场景                     │   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ Standalone Master HA                            ││   │
│  │  │ - 选举 Active Master                            ││   │
│  │  │ - 状态存储: /spark/master                       ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ HBase 集群协调                                   ││   │
│  │  │ - RegionServer 地址发现                          ││   │
│  │  │ - Master 选举                                    ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ Kafka 集群协调                                   ││   │
│  │  │ - Broker 注册                                    ││   │
│  │  │ - Topic/Partition 元数据                         ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

| 使用场景 | 配置 |
|----------|------|
| **Standalone Master HA** | `spark.deploy.zookeeper.url`, `spark.deploy.recoveryMode=zookeeper` |
| **HBase 连接** | `hbase.zookeeper.quorum` |
| **Kafka 连接** | `kafka.zookeeper.connect` |

#### 10.2.2 云存储系统

Spark 与主流云存储的集成：

| 云存储 | URI格式 | 特性 |
|--------|---------|------|
| **Amazon S3** | `s3a://bucket/path` | 支持Magic Committer优化 |
| **Azure Blob Storage** | `wasbs://container@account.blob.core.windows.net/path` | |
| **Azure Data Lake** | `abfs://container@account.dfs.core.windows.net/path` | |
| **Google Cloud Storage** | `gs://bucket/path` | |
| **MinIO** | `s3a://bucket/path` (S3兼容) | 私有化部署 |
| **Alluxio** | `alluxio://host:port/path` | 内存加速层 |

**S3 集成配置：**

| 配置 | 描述 |
|------|------|
| `spark.hadoop.fs.s3a.impl` | `org.apache.hadoop.fs.s3a.S3AFileSystem` |
| `spark.hadoop.fs.s3a.access.key` | AWS Access Key |
| `spark.hadoop.fs.s3a.secret.key` | AWS Secret Key |
| `spark.hadoop.fs.s3a.committer.name` | `magic` (推荐) |
| `spark.hadoop.fs.s3a.endpoint` | S3 Endpoint |

#### 10.2.3 消息队列集成

| 消息系统 | 集成方式 | 特性 |
|----------|----------|------|
| **Apache Kafka** | Structured Streaming内置 | 高吞吐、持久化、分区 |
| **Apache Pulsar** | pulsar-spark连接器 | 多租户、分层存储 |
| **RabbitMQ** | 自定义Receiver | AMQP协议 |
| **Azure Event Hubs** | azure-event-hubs-spark | Azure云原生 |

**Kafka 集成详解：**

```
┌─────────────────────────────────────────────────────────────┐
│                Spark + Kafka 流处理架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Apache Kafka Cluster                   │   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ Topic: events                                   ││   │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐            ││   │
│  │  │ │Partition│ │Partition│ │Partition│            ││   │
│  │  │ │   0     │ │   1     │ │   2     │            ││   │
│  │  │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │            ││   │
│  │  │ │ │Log  │ │ │ │Log  │ │ │ │Log  │ │            ││   │
│  │  │ │ │Offset│ │ │ │Offset│ │ │ │Offset│ │            ││   │
│  │  │ │ │0-N  │ │ │ │0-N  │ │ │ │0-N  │ │            ││   │
│  │  │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │            ││   │
│  │  │ └─────────┘ └─────────┘ └─────────┘            ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼ Consumer读取                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Structured Streaming                       │   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ readStream                                       ││   │
│  │  │   .format("kafka")                              ││   │
│  │  │   .option("kafka.bootstrap.servers", "...")     ││   │
│  │  │   .option("subscribe", "events")                ││   │
│  │  │   .option("startingOffsets", "earliest/latest") ││   │
│  │  │   .load()                                       ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ 处理逻辑                                         ││   │
│  │  │   .selectExpr("CAST(key AS STRING)", ...)       ││   │
│  │  │   .groupBy("key").count()                       ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────┐│   │
│  │  │ writeStream                                      ││   │
│  │  │   .format("kafka/console/file")                 ││   │
│  │  │   .option("checkpointLocation", "...")          ││   │
│  │  │   .start()                                      ││   │
│  │  └─────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Checkpoint: HDFS/S3 (存储Offset和状态)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Kafka 配置参数：**

| 配置 | 描述 |
|------|------|
| `kafka.bootstrap.servers` | Kafka Broker地址 |
| `subscribe` / `subscribePattern` | 订阅Topic |
| `startingOffsets` | 起始位置：earliest/latest |
| `endingOffsets` | 结束位置（批处理） |
| `maxOffsetsPerTrigger` | 每次触发最大Offset数 |
| `minPartitions` | 最小分区数 |

#### 10.2.4 OLAP 查询引擎集成

| 引擎 | 集成方式 | 特性 |
|------|----------|------|
| **Presto/Trino** | JDBC连接 | 跨源联邦查询 |
| **Apache Druid** | spark-druid | 实时OLAP分析 |
| **Apache Pinot** | spark-pinot | 实时OLAP、低延迟 |
| **ClickHouse** | spark-clickhouse-connector | 高性能OLAP |

**Presto/Trino 联邦查询示例：**

```scala
// 通过JDBC连接Presto/Trino
val prestoDF = spark.read
    .format("jdbc")
    .option("url", "jdbc:trino://host:8080/catalog/schema")
    .option("driver", "io.trino.jdbc.TrinoDriver")
    .option("user", "user")
    .option("query", "SELECT * FROM table")
    .load()
```

#### 10.2.5 GPU 加速计算

NVIDIA RAPIDS 加速 Spark 计算：

```
┌─────────────────────────────────────────────────────────────┐
│              Spark + RAPIDS GPU 加速架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Spark Application                  │   │
│  │                                                      │   │
│  │  Spark SQL / DataFrame API                           │   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌───────────────────────────────────────────────┐ │   │
│  │  │        RAPIDS Accelerator for Spark            │ │   │
│  │  │  - 自动将SQL操作映射到GPU                       │ │   │
│  │  │  - 支持join、filter、sort、agg等               │ │   │
│  │  │  - cuDF (GPU DataFrame)                        │ │   │
│  │  └───────────────────────────────────────────────┘ │   │
│  │         │                                            │   │
│  │         ▼                                            │   │
│  │  ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │ GPU Executor │ │ GPU Executor │                 │   │
│  │  │  ┌────────┐ │ │  ┌────────┐ │                 │   │
│  │  │  │ NVIDIA │ │ │  │ NVIDIA │ │                 │   │
│  │  │  │  GPU   │ │ │  │  GPU   │ │                 │   │
│  │  │  └────────┘ │ │  └────────┘ │                 │   │
│  │  └──────────────┘ └──────────────┘                 │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  性能提升: 5-20x (适合大规模数据处理)                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

| 配置 | 描述 |
|------|------|
| `spark.plugins` | `com.nvidia.spark.SQLPlugin` |
| `spark.rapids.sql.enabled` | `true` |
| `spark.executor.resource.gpu.amount` | GPU数量 |

**RAPIDS 支持的操作：**

| 操作 | GPU支持 |
|------|---------|
| `filter`, `where` | ✅ |
| `select`, `withColumn` | ✅ |
| `join` (Broadcast/SortMerge) | ✅ |
| `groupBy`, `agg` | ✅ |
| `sort`, `orderBy` | ✅ |
| `union`, `distinct` | ✅ |
| `window` | ✅ |
| UDF | 部分 |

#### 10.2.6 CDC 数据同步

Debezium + Spark 实现变更数据捕获：

```
┌─────────────────────────────────────────────────────────────┐
│               CDC 数据同步架构                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   MySQL      │ │ PostgreSQL   │ │  Oracle      │        │
│  │  (Source)    │ │  (Source)    │ │  (Source)    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│         │             │             │                        │
│         ▼             ▼             ▼                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Debezium                           │   │
│  │  - 捕获数据库变更 (INSERT/UPDATE/DELETE)             │   │
│  │  - 输出到 Kafka Topic                               │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Apache Kafka                        │   │
│  │  Topic: dbserver1.schema.table                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ Message Format (JSON/Avro):                  │   │   │
│  │  │ {                                             │   │   │
│  │  │   "op": "c/u/d",                              │   │   │
│  │  │   "before": {...},                            │   │   │
│  │  │   "after": {...},                             │   │   │
│  │  │   "source": {...}                             │   │   │
│  │  │ }                                             │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Spark Structured Streaming                 │   │
│  │  - 解析CDC消息                                       │   │
│  │  - 写入目标表 (Delta Lake / Hudi / Iceberg)         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Delta Lake   │ │    Hudi      │ │   Iceberg    │        │
│  │ (Target)     │ │  (Target)    │ │  (Target)    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 10.2.7 监控系统集成

| 监控系统 | 集成方式 | 特性 |
|----------|----------|------|
| **Prometheus + Grafana** | Metrics Sink | 实时监控、告警 |
| **Data Mechanics Delight** | Spark Agent | 可视化优化建议 |
| **DataFlint** | Spark Listener | 实时性能分析 |

**Prometheus 配置：**

```properties
# spark-defaults.conf
spark.metrics.conf.*.sink.prometheus.class=org.apache.spark.metrics.sink.PrometheusSink
spark.metrics.conf.*.sink.prometheus.port=8080
spark.metrics.conf.master.source.jvm.class=org.apache.spark.metrics.source.JvmSource
spark.metrics.conf.worker.source.jvm.class=org.apache.spark.metrics.source.JvmSource
spark.metrics.conf.driver.source.jvm.class=org.apache.spark.metrics.source.JvmSource
spark.metrics.conf.executor.source.jvm.class=org.apache.spark.metrics.source.JvmSource
```

### 10.3 表格式生态

| 格式 | 特性 | GitHub |
|------|------|---------|
| **Delta Lake** | ACID、时间旅行、Schema演进 | delta-io/delta |
| **Apache Hudi** | Upsert、增量处理、CDC | apache/hudi |
| **Apache Iceberg** | Schema演进、分区演进 | apache/iceberg |
| **Lance** | ML/LLM列式格式 | lancedb/lance |

### 10.4 基础设施生态

| 项目 | 功能 | GitHub |
|------|------|---------|
| **Kyuubi** | 多租户SQL Gateway | apache/kyuubi |
| **Spark Job Server** | REST Job管理 | spark-jobserver/spark-jobserver |
| **Zeppelin** | Notebook | apache/zeppelin |
| **MLflow** | ML生命周期管理 | mlflow/mlflow |
| **Data Mechanics Delight** | Spark监控UI | datamechanics/delight |
| **DataFlint** | Spark监控 | dataflint/spark |
| **Spark Operator** | K8s Operator | kubeflow/spark-operator |
| **Alluxio** | 内存加速存储层 | alluxio/alluxio |

### 10.5 应用生态

| 项目 | 功能 | GitHub |
|------|------|---------|
| **Apache Mahout** | ML算法（已迁移到Spark） | apache/mahout |
| **ADAM** | 基因数据分析 | bigdatagenomics/adam |
| **TransmogrifAI** | AutoML | salesforce/TransmogrifAI |
| **Spark NLP** | NLP处理 | JohnSnowLabs/spark-nlp |
| **Rumble** | JSONiq引擎 | rumbledb/rumble |
| **Hamilton** | PySpark工作流 | DAGWorks-Inc/hamilton |
| **ScaleDP** | 文档处理AI | stabrise/scaledp |

### 10.6 语言绑定生态

| 语言 | 项目 | GitHub |
|------|------|---------|
| **C#/F#** | Mobius | Microsoft/Mobius |
| **Clojure** | Geni | zero-one-group/geni |
| **Julia** | Spark.jl | dfdx/Spark.jl |
| **Kotlin** | kotlin-spark-api | JetBrains/kotlin-spark-api |
| **Go** | spark-connect-go | apache/spark-connect-go |
| **Rust** | spark-connect-rust | apache/spark-connect-rust |
| **Swift** | spark-connect-swift | apache/spark-connect-swift |

---

## 11. 性能优化策略

### 11.1 Catalyst 优化器

#### 11.1.1 优化规则

| 规则 | 描述 |
|------|------|
| **Predicate Pushdown** | 过滤条件推到数据源 |
| **Column Pruning** | 调整读取的列 |
| **Constant Folding** | 常量表达式预计算 |
| **Combine Filters** | 合并多个过滤条件 |
| **Combine Limits** | 合并多个 Limit |
| **Join Reordering** | 调整 Join 顺序 |
| **Broadcast Join** | 小表广播到大表 |

#### 11.1.2 Adaptive Query Execution (AQE)

| 特性 | 配置 | 描述 |
|------|------|------|
| **动态合并 Shuffle 分区** | `spark.sql.adaptive.coalescePartitions.enabled` | 自动合并小分区 |
| **动态切换 Join 策略** | `spark.sql.adaptive.localShuffleReader.enabled` | 运行时选择 Join 类型 |
| **动态优化 Sort Merge Join** | `spark.sql.adaptive.optimizeSkewedJoin.enabled` | 处理数据倾斜 |
| **动态 Join Reorder** | `spark.sql.adaptive.joinReorder.enabled` | 运行时调整 Join 顺序 |

### 11.2 内存优化

| 配置 | 描述 | 建议值 |
|------|------|--------|
| `spark.executor.memory` | Executor 内存 | 根据集群资源 |
| `spark.memory.fraction` | 执行+存储比例 | 0.75 |
| `spark.memory.storageFraction` | 存储边界 | 0.5 |
| `spark.serializer` | 序列化器 | `org.apache.spark.serializer.KryoSerializer` |
| `spark.rdd.compress` | RDD压缩 | `true`（节省内存） |
| `spark.executor.memoryOverhead` | 堆外内存 | executor.memory * 10% |

### 11.3 Shuffle 优化

| 配置 | 描述 | 建议值 |
|------|------|--------|
| `spark.sql.shuffle.partitions` | Shuffle分区数 | 根据数据量调整 |
| `spark.shuffle.compress` | Shuffle压缩 | `true` |
| `spark.shuffle.spill.compress` | 溢出压缩 | `true` |
| `spark.shuffle.sort.bypassMergeThreshold` | 跳过Sort阈值 | 200 |

### 11.4 数据倾斜处理

| 方案 | 描述 |
|------|------|
| **Repartition** | 手动重分区 |
| **Salting** | 加盐打散热点Key |
| **Broadcast Join** | 避免 Shuffle |
| **AQE Skewed Join** | 自动处理倾斜 |

### 11.5 并行度调整

| 配置 | 描述 | 计算公式 |
|------|------|----------|
| `spark.default.parallelism` | RDD默认并行度 | CPU核数 * 2~4 |
| `spark.sql.shuffle.partitions` | SQL Shuffle分区 | 数据量/128MB |

---

## 12. 安全机制

### 12.1 认证

| 认证方式 | 配置 | 描述 |
|----------|------|------|
| **Kerberos** | `spark.yarn.principal`, `spark.yarn.keytab` | YARN Kerberos |
| **SASL** | `spark.authenticate=true` | RPC认证 |
| **Token** | 动态Token | Spark内部通信 |

### 12.2 加密

| 加密类型 | 配置 | 描述 |
|----------|------|------|
| **RPC加密** | `spark.network.crypto.enabled=true` | Netty加密 |
| **UI加密** | `spark.ui.ssl.enabled=true` | Web UI SSL |
| **存储加密** | 文件系统加密 | HDFS透明加密 |

### 12.3 权限控制

| 机制 | 配置 | 描述 |
|------|------|------|
| **ACL** | `spark.acls.enable=true` | 访问控制列表 |
| **UI权限** | `spark.ui.view.acls` | UI查看权限 |
| **修改权限** | `spark.modify.acls` | 修改权限 |

---

## 13. 监控与运维

### 13.1 Web UI

| 端口 | 默认值 | 描述 |
|------|--------|------|
| **Driver UI** | 4040 | 应用UI |
| **Master UI** | 8080 | Standalone Master UI |
| **Worker UI** | 8081 | Standalone Worker UI |
| **History Server** | 18080 | 历史应用UI |

#### 13.1.1 UI 页面

| 页面 | 内容 |
|------|------|
| **Jobs** | Job列表、状态、时间 |
| **Stages** | Stage详情、Task统计 |
| **Storage** | RDD内存使用 |
| **Environment** | 配置环境 |
| **Executors** | Executor状态、内存 |
| **SQL** | SQL执行计划 |

### 13.2 Metrics System

| Sink | 配置 | 描述 |
|------|------|------|
| **Console** | `console` | 控制台输出 |
| **CSV** | `csv` | CSV文件 |
| **Graphite** | `graphite` | Graphite服务 |
| **Prometheus** | `prometheus` | Prometheus |

### 13.3 Event Logging

| 配置 | 描述 |
|------|------|
| `spark.eventLog.enabled=true` | 启用事件日志 |
| `spark.eventLog.dir` | 事件日志目录 |
| `spark.eventLog.compress` | 压缩事件日志 |
| `spark.history.fs.logDirectory` | History Server日志目录 |

### 13.4 常用监控指标

| 指标 | 描述 |
|------|------|
| `executor.cpuTime` | Executor CPU时间 |
| `executor.memoryUsed` | 内存使用 |
| `driver.BlockManager.diskUsage` | 磁盘使用 |
| `application.startTime` | 应用启动时间 |
| `jvm.heap.usage` | JVM堆使用率 |

---

## 14. 设计演进历史

### 14.1 核心论文时间线

| 论文 | 会议/期刊 | 年份 | 贡献 |
|------|-----------|------|------|
| **Spark: Cluster Computing with Working Sets** | HotCloud | 2010 | Spark原型设计 |
| **Resilient Distributed Datasets** | NSDI (Best Paper) | 2012 | RDD核心抽象 |
| **Shark: SQL and Rich Analytics at Scale** | SIGMOD | 2013 | SQL集成 |
| **Discretized Streams** | SOSP | 2013 | 流处理模型 |
| **GraphX** | OSDI | 2014 | 图计算统一 |
| **Spark SQL** | SIGMOD | 2015 | Catalyst优化器 |
| **SparkR** | SIGMOD | 2016 | R语言集成 |
| **MLlib** | JMLR | 2016 | ML算法库 |

### 14.2 主要版本特性演进

| 版本 | 特性 | 影响 |
|------|------|------|
| **0.x** | RDD、内存计算 | 核心架构确立 |
| **1.0** | Spark SQL、DataFrame | 结构化数据支持 |
| **1.6** | Dataset API | 类型安全API |
| **2.0** | Structured Streaming、统一API | 流批一体 |
| **2.2** | 移除Java7 | Java版本升级 |
| **2.4** | Kubernetes支持 | 云原生部署 |
| **3.0** | AQE、Python3 | 自适应优化 |
| **3.4** | Spark Connect | 客户端分离 |
| **4.0** | Scala2.13、Java17+ | 现代化语言支持 |

### 14.3 关键设计决策

| 决策 | 原因 | 结果 |
|------|------|------|
| **内存持久化** | MapReduce I/O瓶颈 | 100x性能提升 |
| **Lineage容错** | 避免数据复制开销 | 高效容错 |
| **惰性执行** | 优化执行计划 | 减少计算 |
| **统一引擎** | 多种计算需求 | SQL/ML/流/图统一 |
| **Catalyst优化器** | SQL性能 | 自动优化 |
| **Spark Connect** | 客户端轻量化 | 多语言扩展 |

---

## 附录

### A. 配置参数分类索引

| 类别 | 参数示例 |
|------|----------|
| **应用配置** | `spark.app.name`, `spark.master` |
| **执行配置** | `spark.executor.memory`, `spark.executor.cores` |
| **内存配置** | `spark.memory.fraction`, `spark.memory.storageFraction` |
| **Shuffle配置** | `spark.sql.shuffle.partitions`, `spark.shuffle.compress` |
| **网络配置** | `spark.driver.port`, `spark.blockManager.port` |
| **序列化配置** | `spark.serializer`, `spark.kryo.classesToRegister` |
| **UI配置** | `spark.ui.port`, `spark.ui.enabled` |
| **安全配置** | `spark.authenticate`, `spark.acls.enable` |

### B. API 快速索引

| API 类 | 文档链接 |
|--------|----------|
| **SparkContext** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/SparkContext.html) |
| **SparkSession** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/SparkSession.html) |
| **RDD** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/rdd/RDD.html) |
| **DataFrame** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/Dataset.html) |
| **StreamingQuery** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/streaming/StreamingQuery.html) |
| **Pipeline** | [ScalaDoc](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/ml/Pipeline.html) |

### C. 代码结构索引

| 目录 | 内容 |
|------|------|
| `core/src/main/scala/org/apache/spark/` | 核心组件 |
| `core/src/main/scala/org/apache/spark/scheduler/` | 调度器 |
| `core/src/main/scala/org/apache/spark/storage/` | 存储管理 |
| `core/src/main/scala/org/apache/spark/rdd/` | RDD实现 |
| `sql/core/src/main/scala/org/apache/spark/sql/` | SQL引擎 |
| `sql/catalyst/src/main/scala/org/apache/spark/sql/catalyst/` | Catalyst优化器 |
| `streaming/src/main/scala/org/apache/spark/streaming/` | 流处理 |
| `mllib/src/main/scala/org/apache/spark/ml/` | ML库 |
| `graphx/src/main/scala/org/apache/spark/graphx/` | 图计算 |

---

## 参考文档

1. [Apache Spark 官方文档](https://spark.apache.org/docs/latest/)
2. [Spark Cluster Overview](https://spark.apache.org/docs/latest/cluster-overview.html)
3. [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html)
4. [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
5. [Structured Streaming Guide](https://spark.apache.org/docs/latest/streaming/index.html)
6. [MLlib Guide](https://spark.apache.org/docs/latest/ml-guide.html)
7. [GraphX Guide](https://spark.apache.org/docs/latest/graphx-programming-guide.html)
8. [Spark Research Papers](https://spark.apache.org/research.html)
9. [Third-Party Projects](https://spark.apache.org/third-party-projects.html)
10. Spark 源码分析（本地 spark/core 模块）

---

**文档维护**: 本文档基于 Spark 4.x 版本编写，建议定期更新以跟进版本演进。