-- 1. Create Dimension Table: Shipping Lanes
CREATE TABLE IF NOT EXISTS dim_shipping_lanes (
    lane_id VARCHAR(20) PRIMARY KEY,
    origin_hub VARCHAR(50) NOT NULL,
    destination_hub VARCHAR(50) NOT NULL,
    mode_of_transport VARCHAR(20) DEFAULT 'Ocean',
    contracted_base_rate_usd NUMERIC(10, 2) NOT NULL
);

-- 2. Create Fact Table: Freight Transactions & Spot Market Benchmark Data
CREATE TABLE IF NOT EXISTS fact_freight_transactions (
    transaction_id SERIAL PRIMARY KEY,
    lane_id VARCHAR(20) REFERENCES dim_shipping_lanes(lane_id),
    transaction_date DATE NOT NULL,
    actual_rate_paid_usd NUMERIC(10, 2) NOT NULL,
    market_spot_rate_usd NUMERIC(10, 2) NOT NULL,
    carrier_name VARCHAR(50) NOT NULL,
    transit_days INT NOT NULL
);

-- 3. Seed Multi-Modal Shipping Lanes Dimension Data
INSERT INTO dim_shipping_lanes (lane_id, origin_hub, destination_hub, mode_of_transport, contracted_base_rate_usd)
VALUES 
    -- Ocean Lanes
    ('LANE-001', 'Mundra Port', 'Rotterdam Port', 'Ocean', 2800.00),
    ('LANE-002', 'Cochin Port', 'Hamburg Port', 'Ocean', 2600.00),
    ('LANE-003', 'Chennai Port', 'Port of Singapore', 'Ocean', 1100.00),
    
    -- Air Freight Lanes
    ('LANE-004', 'Mumbai Airport (BOM)', 'Frankfurt Airport (FRA)', 'Air', 6500.00),
    ('LANE-005', 'Delhi Airport (DEL)', 'Dubai Airport (DXB)', 'Air', 4800.00),
    
    -- Road / FTL Trucking Lanes
    ('LANE-006', 'Nhava Sheva Hub', 'Pune Distribution Center', 'Road', 850.00),
    ('LANE-007', 'Chennai Logistics Park', 'Bangalore Warehouse', 'Road', 950.00)
ON CONFLICT (lane_id) DO UPDATE SET
    origin_hub = EXCLUDED.origin_hub,
    destination_hub = EXCLUDED.destination_hub,
    mode_of_transport = EXCLUDED.mode_of_transport,
    contracted_base_rate_usd = EXCLUDED.contracted_base_rate_usd;