# Real-Time Change Data Capture (CDC) Pipeline using PostgreSQL, Debezium, and Kafka

## Overview

This project demonstrates a fully local, end-to-end real-time data streaming pipeline using open-source tools. It captures database changes from a PostgreSQL source and streams them into Apache Kafka using Debezium. The captured events can then be consumed by downstream systems, such as another PostgreSQL database, Elasticsearch, or custom Python applications.

This setup helps understand how modern data architectures enable real-time analytics, synchronization, and event-driven processing through Change Data Capture (CDC).

## Architecture

      +-------------+
      | PostgreSQL  |
      | (Source DB) |
      +------+------ +
             |
             | Logical Replication (WAL)
             v
     +-------+--------+
     |   Debezium     |
     | Kafka Connect  |
     +-------+--------+
             |
             | Change Events (INSERT, UPDATE, DELETE)
             v
     +-------+--------+
     |   Apache Kafka |
     +-------+--------+
             |
      +------+------ +
      |   Consumers  |
      | (Python/DB)  |
      +------------- +

## Components

| Component                 | Description                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| PostgreSQL (pg-source)    | Source database. Configured with logical replication to emit changes through Write-Ahead Logs (WAL).   |
| Zookeeper                 | Manages Kafka broker coordination and leader election.                                                 |
| Kafka Broker              | Stores and streams Debezium’s change events as Kafka topics.                                           |
| Debezium Connect          | Connects PostgreSQL and Kafka, continuously reading the WAL and publishing CDC events to Kafka topics. |
| PostgreSQL (pg-analytics) | Acts as a downstream analytics database for consuming processed data.                                  |
| Adminer                   | A lightweight web-based SQL client used to inspect and query both PostgreSQL databases.                |
| Python Consumer           | A sample consumer that listens to Kafka topics and writes events into the analytics database.          |

## Technology Stack

- Docker & Docker Compose
- PostgreSQL 15
- Debezium 3.2
- Apache Kafka 7.6 (Confluent)
- Python 3 (Confluent Kafka Client)

## Folder Structure

```
Change_Data_Capture_Pipeline/
|   docker-compose.yml
|   README.md
+---analytics-initdb
|       01-init-analytics.sql
+---connectors
|       register-postgres.json
+---consumer
|       consumer.py
|       dockerfile
|       requirements.txt
\---source-initdb
        01-init-source.sql
```

## How It Works

1. The source PostgreSQL database is configured with `wal_level=logical`, enabling logical replication.
2. Debezium Connect reads the Write-Ahead Logs (WAL) from PostgreSQL using a replication slot.
3. Each database change (insert, update, delete) is converted into a structured event and written to a Kafka topic.
4. Kafka stores and manages these topics for reliable delivery.
5. Consumers, such as the provided Python script or other sinks, can subscribe to these topics and perform real-time data processing or replication.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Caged1964/Change-Data-Capture-CDC-Pipeline.git
cd Change-Data-Capture-CDC-Pipeline
```

### 2. Start All Services

```bash
docker compose up -d
```

Check running containers:

```bash
docker ps
```

Expected containers:

- zookeeper
- kafka
- kafka-connect
- pg-source
- pg-analytics
- adminer

### 3. Accessing the Databases via Adminer

Adminer runs on port 8080.

Open a browser and go to:  
http://localhost:8080

#### Source Database Login

- System: PostgreSQL
- Server: pg-source
- Username: dbz_source
- Password: dbz_source
- Database: ordersdb

#### Analytics Database Login

- System: PostgreSQL
- Server: pg-analytics
- Username: dbz_analytics
- Password: dbz_analytics
- Database: analyticsdb

You can use Adminer to view schema, execute queries, and validate whether changes are being replicated.

### 4. Register the Debezium Connector

Register the PostgreSQL connector with Kafka Connect using the configuration file located at `connectors/register-postgres.json`.

```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json"   --data @connectors/register-postgres.json   http://localhost:8083/connectors
```

Check the connector status:

```bash
curl http://localhost:8083/connectors/orders-connector/status | jq
```

### 5. Insert Sample Data into Source Database

Access the source PostgreSQL instance:

```bash
docker exec -it pg-source psql -U dbz_source -d ordersdb
```

Insert a record:

```sql
INSERT INTO orders (customer_id, customer_name, total, status)
VALUES (108, 'John Wick', 450.75, 'CREATED');
```

This change will immediately appear in Kafka under the topic `dbserver1.public.orders`.

### 6. Consume Kafka Messages Using Python

Install dependencies:

```bash
pip install -r consumer/requirements.txt
```

Run the consumer:

```bash
python consumer/consumer.py
```

The script connects to Kafka (localhost:29092), listens to the topic `dbserver1.public.orders`, and logs the streamed events. It can also insert processed data into the analytics database.

### 7. Stop All Services

To gracefully shut down all running containers:

```bash
docker compose down
```

This stops and removes all containers, networks, and temporary volumes.

## Monitoring and Troubleshooting

Kafka Connect Logs:

```bash
docker logs -f kafka-connect
```

Kafka Topics:

```bash
docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092
```

Check Connector Status:

```bash
curl http://localhost:8083/connectors/orders-connector/status | jq
```

Inspect Connector Configuration:

```bash
curl http://localhost:8083/connectors/orders-connector | jq
```

PostgreSQL Access (Source or Analytics):

```bash
docker exec -it pg-source psql -U dbz_source -d ordersdb
docker exec -it pg-analytics psql -U dbz_analytics -d analyticsdb
```

## Key Concepts

### Change Data Capture (CDC)

A method of identifying and capturing changes made to data in a database so that they can be replicated or processed downstream in real time.

### Write-Ahead Log (WAL)

PostgreSQL records every data change in the WAL before applying it to the actual data files. Debezium uses these logs to capture changes non-intrusively.

### Debezium

A distributed open-source platform built on top of Kafka Connect that streams changes from databases into Kafka topics.

### Kafka Topics

Each table’s changes are published to a dedicated Kafka topic (for example, `dbserver1.public.orders`).

### Consumers

Applications or connectors that subscribe to topics to process or store change events (e.g., a Python script or sink connector).

## Extending the Pipeline

This setup can be extended to:

- Use Elasticsearch or OpenSearch as a sink for search capabilities.
- Integrate with ksqlDB for stream processing.
- Add monitoring with Prometheus and Grafana.
- Implement schema evolution and data transformations using Kafka Streams.
