-- Create replication role if it does not already exist.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dbz_source') THEN
    CREATE ROLE dbz_source WITH REPLICATION LOGIN PASSWORD 'dbz_source';
  ELSE
    -- make sure it has LOGIN and REPLICATION and password (safe to run repeatedly)
    ALTER ROLE dbz_source WITH REPLICATION LOGIN PASSWORD 'dbz_source';
  END IF;
END
$$;

-- Create the orders table if missing
CREATE TABLE IF NOT EXISTS public.orders (
  id SERIAL PRIMARY KEY,
  customer_id INT,
  customer_name TEXT,
  total NUMERIC(10,2),
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Ensure full row images to allow Debezium to produce 'before' for updates/deletes
ALTER TABLE public.orders REPLICA IDENTITY FULL;

-- Create publication (drop/recreate to be safe for re-runs)
DO $$
BEGIN
   IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'dbz_publication') THEN
      -- Do nothing if publication already exists for the right table;
      -- you could add logic to check membership, but simplest is to recreate:
      PERFORM 1;
   ELSE
      CREATE PUBLICATION dbz_publication FOR TABLE public.orders;
   END IF;
END
$$;