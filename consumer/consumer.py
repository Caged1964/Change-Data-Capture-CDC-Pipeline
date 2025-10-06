# consumer/consumer.py
from confluent_kafka import Consumer
import psycopg2, json, time, os, sys

# Configuration - USE HOST-EXPOSED KAFKA PORT (29092)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "dbserver1.public.orders")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5433"))
PG_DB = os.getenv("PG_DB", "analyticsdb")
PG_USER = os.getenv("PG_USER", "dbz_analytics")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dbz_analytics")

consumer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': 'analytics-consumer-group',
    'auto.offset.reset': 'earliest'
}

print(f"Connecting to Kafka broker at: {KAFKA_BOOTSTRAP}, topic: {KAFKA_TOPIC}")
consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

# Connect to analytics Postgres
pg_conn = psycopg2.connect(
    host=PG_HOST, port=PG_PORT, database=PG_DB, user=PG_USER, password=PG_PASSWORD
)
pg_cur = pg_conn.cursor()

def upsert_order(data):
    # data is expected to have keys: id, customer_id, customer_name, total, status, created_at
    pg_cur.execute("""
        INSERT INTO orders_analytics (id, customer_id, customer_name, total, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
          customer_id = EXCLUDED.customer_id,
          customer_name = EXCLUDED.customer_name,
          total = EXCLUDED.total,
          status = EXCLUDED.status,
          created_at = EXCLUDED.created_at;
    """, (
        data.get('id'),
        data.get('customer_id'),
        data.get('customer_name'),
        float(data.get('total')) if data.get('total') is not None else None,
        data.get('status'),
        data.get('created_at')
    ))
    pg_conn.commit()

print("📡 Listening for new events... (Ctrl+C to stop)")

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            print("⚠️ Kafka error:", msg.error())
            continue

        try:
            raw = msg.value().decode('utf-8')
            event = json.loads(raw)
            # Debezium often wraps the envelope in 'payload' (Connect wrapper) or the envelope may be the root.
            payload = event.get('payload', event)

            # inserts/updates -> 'after' contains the new row
            if payload.get('after'):
                after = payload['after']
                upsert_order(after)
                print(f"✅ Upserted order {after.get('id')}")
            # deletes -> op == 'd' and 'before' contains the deleted row
            elif payload.get('op') == 'd':
                before = payload.get('before')
                if before and before.get('id'):
                    pg_cur.execute("DELETE FROM orders_analytics WHERE id = %s", (before['id'],))
                    pg_conn.commit()
                    print(f"❌ Deleted order {before.get('id')}")
            else:
                # Not expected type; print a short summary for debugging:
                print("ℹ️ Received event (unhandled):", {k: payload.get(k) for k in ("op","after","before")})
        except Exception as e:
            print("❌ Error processing message:", e)
            print("Raw message:", msg.value())
except KeyboardInterrupt:
    print("🛑 Stopping consumer...")
finally:
    consumer.close()
    pg_cur.close()
    pg_conn.close()
