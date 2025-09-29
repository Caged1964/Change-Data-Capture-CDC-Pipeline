CREATE TABLE IF NOT EXISTS orders_analytics (
  id INT PRIMARY KEY,
  customer_id INT,
  customer_name TEXT,
  total NUMERIC(10,2),
  status TEXT,
  created_at TIMESTAMPTZ,
  synced_at TIMESTAMPTZ DEFAULT now()
);