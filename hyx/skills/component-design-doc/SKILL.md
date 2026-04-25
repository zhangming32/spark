---
name: component-design-doc
description: Generate comprehensive design documentation for any software component. Input component name and automatically produce complete design document covering architecture, APIs, integration, ecosystem, and optimization strategies.
license: MIT
compatibility: Requires web access for fetching official documentation and local codebase for source analysis.
metadata:
  author: opencode
  version: "1.0"
  generatedBy: "opencode"
---

Generate comprehensive design documentation for any software component.

**Usage**: Simply input any component name and this skill will automatically generate a complete design document.

**示例输入**: "Spark", "Kafka", "Flink", "HBase", "Redis", "MySQL", "HDFS", etc.

---

## Workflow

### Phase 1: Information Gathering

Collect information from multiple sources:

1. **Official Documentation**
   - Main documentation page
   - Architecture overview
   - API reference
   - Programming guides
   - Configuration reference

2. **Research Papers** (if available)
   - Original design papers
   - Conference papers (SIGMOD, OSDI, SOSP, etc.)
   - Journal publications

3. **Third-party Integration**
   - Official integration list
   - Connector ecosystem
   - Compatible systems

4. **Local Source Code** (if available)
   - Core components analysis
   - Key classes and interfaces
   - Internal architecture

5. **Community Resources**
   - GitHub repository
   - Issue tracker patterns
   - StackOverflow common questions

### Phase 2: Document Structure

Generate document with standard sections:

```
1. Overview
   - Background and motivation
   - Design goals
   - Core innovations
   - Version history

2. System Architecture
   - Overall architecture diagram
   - Runtime components
   - Terminology definitions

3. Feature/Module List
   - Core features
   - Optional modules
   - Feature matrix

4. Core Abstractions
   - Data models
   - Key interfaces
   - Design patterns used

5. Internal Design
   - Scheduling/Coordination
   - Memory/Storage management
   - Network/RPC design
   - Thread model

6. Fault Tolerance
   - Failure detection
   - Recovery mechanisms
   - Consistency guarantees

7. External Integration
   - Cluster managers
   - Data sources
   - Storage systems
   - Message queues
   - Monitoring systems

8. API Reference
   - Language bindings
   - Core APIs
   - Configuration APIs
   - Extension APIs

9. Ecosystem
   - Official connectors
   - Third-party projects
   - Compatible formats

10. Performance Optimization
    - Tuning parameters
    - Best practices
    - Common bottlenecks

11. Security
    - Authentication
    - Encryption
    - Authorization

12. Monitoring & Operations
    - Metrics
    - Logging
    - Health checks
    - Troubleshooting

13. Design Evolution
    - Key papers timeline
    - Version milestones
    - Major decisions

Appendix
    - Configuration index
    - API quick reference
    - Code structure
    - References
```

### Phase 3: Diagram Generation

Generate ASCII diagrams for:

| Diagram Type | Purpose |
|--------------|---------|
| Overall Architecture | Component layers and interactions |
| Runtime Flow | How components interact during execution |
| Integration Architecture | External system connections |
| Data Flow | How data moves through system |
| Internal Components | Subsystem breakdown |
| Deployment Modes | Different deployment options |

**Diagram Style Guide**:
```
┌─────────────────────────────────────────────────────────────┐
│                      Title                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Component                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │
│  │  │ Sub-comp│ │ Sub-comp│ │ Sub-comp│              │   │
│  │  │    A    │ │    B    │ │    C    │              │   │
│  │  └─────────┘ └─────────┘ └─────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  External    │ │  External    │ │  External    │        │
│  │  System A    │ │  System B    │ │  System C    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Phase 4: Component Type Handling

Different component types require different focus areas:

#### Big Data Frameworks (Spark, Flink, Hadoop, Beam)
- Focus on: Distributed execution, data partitioning, shuffle, fault tolerance
- Extra sections: DAG execution, resource scheduling

#### Message Systems (Kafka, Pulsar, RabbitMQ, ActiveMQ)
- Focus on: Message delivery guarantees, partitioning, replication, consumer groups
- Extra sections: Offset management, exactly-once semantics

#### Databases (HBase, Cassandra, MongoDB, Redis, MySQL)
- Focus on: Data model, replication, consistency levels, query patterns
- Extra sections: Write path, read path, compaction

#### Storage Systems (HDFS, S3, Alluxio, MinIO)
- Focus on: Block management, replication, consistency, access patterns
- Extra sections: Namenode/Datanode architecture

#### Query Engines (Presto, Trino, Druid, ClickHouse)
- Focus on: Query planning, distributed execution, caching
- Extra sections: Connector framework, cost-based optimization

#### Coordination Services (ZooKeeper, Etcd, Consul)
- Focus on: Consensus protocol, session management, watch mechanism
- Extra sections: ZAB/Raft protocol details

#### ML/AI Frameworks (TensorFlow, PyTorch, MLflow)
- Focus on: Model lifecycle, training, serving, distributed execution
- Extra sections: GPU utilization, checkpointing

#### Stream Processing (Flink, Spark Streaming, Storm)
- Focus on: Windowing, state management, watermarking, backpressure
- Extra sections: Checkpointing, exactly-once processing

---

## Execution Steps

When user provides component name:

### Step 1: Identify Component Type
Ask user if unclear:
```
Component: <name>
Detected type: <big-data/message-queue/database/etc.>

Is this correct? Or specify: [big-data] [message] [database] [storage] [query-engine] [coordination] [ml] [streaming] [other]
```

### Step 2: Gather Official Docs
Fetch from official sources:
- Main docs: `<component>.apache.org/docs/latest/` (for Apache projects)
- Or: `<component>.io/docs/` (for other projects)
- GitHub: `github.com/<org>/<component>`

### Step 3: Analyze Source Code
If local codebase exists:
```
Find core source files
Read main entry classes
Identify key interfaces
Map component hierarchy
```

### Step 4: Research Integration
Search for:
- Integration documentation
- Connector lists
- Compatibility matrices
- Third-party project lists

### Step 5: Generate Document
Create comprehensive document following structure template.

### Step 6: Review with User
Ask user to review and identify gaps:
```
Document generated. Please review:
1. Missing components?
2. Incorrect integration descriptions?
3. Need more detail on specific section?
```

---

## Common Components Quick Reference

| Component | Type | Official Site | Key Papers |
|-----------|------|---------------|------------|
| Apache Spark | Big Data | spark.apache.org | RDD (NSDI'12), Spark SQL (SIGMOD'15) |
| Apache Flink | Streaming | flink.apache.org | Dataflow Model (VLDB'15) |
| Apache Kafka | Message | kafka.apache.org | Kafka Paper (SIGMOD'11) |
| Apache HBase | Database | hbase.apache.org | Bigtable (OSDI'06) |
| Apache Cassandra | Database | cassandra.apache.org | Dynamo (SOSP'07) |
| Apache Hadoop | Storage | hadoop.apache.org | GFS (SOSP'03), MapReduce (OSDI'04) |
| Apache HDFS | Storage | hadoop.apache.org | GFS (SOSP'03) |
| Apache ZooKeeper | Coordination | zookeeper.apache.org | ZooKeeper Paper (USENIX'08) |
| Apache Pulsar | Message | pulsar.apache.org | Pulsar Paper (SIGMOD'18) |
| Presto/Trino | Query Engine | trino.io | Presto Paper (SIGMOD'12) |
| Apache Druid | OLAP | druid.apache.org | Druid Paper (SIGMOD'14) |
| ClickHouse | OLAP | clickhouse.com | ClickHouse Paper |
| Redis | Database | redis.io | Redis Documentation |
| Elasticsearch | Search | elastic.co | Elasticsearch Guide |
| MongoDB | Database | mongodb.com | MongoDB Manual |
| Delta Lake | Table Format | delta.io | Delta Lake Paper |
| Apache Iceberg | Table Format | iceberg.apache.org | Iceberg Design |
| Apache Hudi | Table Format | hudi.apache.org | Hudi Design |

---

## Output Format

Default output location:
```
<current-directory>/<component>-design-document.md
```

Or specify output path when invoking.

---

## Quality Checklist

Before finalizing, verify:

- [ ] All major components documented
- [ ] Architecture diagrams included
- [ ] Integration with common systems covered
- [ ] API reference complete
- [ ] Configuration parameters indexed
- [ ] Performance tuning guidance included
- [ ] Security considerations addressed
- [ ] Monitoring/logging documented
- [ ] References to official sources included
- [ ] Version history captured

---

## Example Invocation

```
User: Generate design document for Apache Flink

Assistant: [Follows workflow]
1. Detects type: Stream Processing
2. Fetches flink.apache.org docs
3. Reads local source if available
4. Generates comprehensive document
5. Outputs: flink-design-document.md
```

---

## Notes

- For Apache projects, always check `research.html` page for papers
- For newer components without papers, focus on design docs and RFCs
- Always reference official documentation URLs
- Include GitHub links for connectors and ecosystem
- Keep diagrams simple but informative
- Use consistent terminology from official docs