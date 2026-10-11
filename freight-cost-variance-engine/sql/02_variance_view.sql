-- Create an Analytics View for Freight Cost Leakage & Variance
CREATE OR REPLACE VIEW vw_freight_cost_variance AS
SELECT 
    f.transaction_id,
    f.transaction_date,
    l.lane_id,
    l.origin_hub,
    l.destination_hub,
    l.mode_of_transport,
    f.carrier_name,
    l.contracted_base_rate_usd,
    f.market_spot_rate_usd,
    f.actual_rate_paid_usd,
    f.transit_days,
    
    -- Variance vs Contracted Base Rate (Positive = Overspend / Cost Leakage)
    (f.actual_rate_paid_usd - l.contracted_base_rate_usd) AS variance_vs_contract_usd,
    
    -- Variance vs Market Spot Benchmark (Positive = Paid above spot market)
    (f.actual_rate_paid_usd - f.market_spot_rate_usd) AS variance_vs_spot_usd,
    
    -- Performance Flag
    CASE 
        WHEN f.actual_rate_paid_usd > (l.contracted_base_rate_usd * 1.05) THEN 'High Overspend'
        WHEN f.actual_rate_paid_usd < l.contracted_base_rate_usd THEN 'Under Contract'
        ELSE 'Within Tolerance'
    END AS cost_performance_status

FROM fact_freight_transactions f
JOIN dim_shipping_lanes l ON f.lane_id = l.lane_id;

-- Aggregate Trade Lane Summary Query
SELECT 
    origin_hub || ' ➔ ' || destination_hub AS trade_lane, 
    COUNT(transaction_id) AS total_shipments,
    ROUND(AVG(actual_rate_paid_usd), 2) AS avg_actual_rate,
    ROUND(AVG(contracted_base_rate_usd), 2) AS avg_contract_rate,
    ROUND(SUM(variance_vs_contract_usd), 2) AS total_cost_leakage_usd,
    ROUND(AVG(transit_days), 1) AS avg_transit_days
FROM vw_freight_cost_variance
GROUP BY lane_id, origin_hub, destination_hub
ORDER BY total_cost_leakage_usd DESC;