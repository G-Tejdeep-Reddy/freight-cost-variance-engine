-- Create an Advanced Carrier Transit & Cost Trade-off View
CREATE OR REPLACE VIEW vw_carrier_tradeoffs AS
SELECT 
    carrier_name,
    mode_of_transport,
    COUNT(transaction_id) AS total_shipments,
    ROUND(AVG(actual_rate_paid_usd), 2) AS avg_rate_paid,
    ROUND(AVG(contracted_base_rate_usd), 2) AS avg_contract_rate,
    ROUND(AVG(transit_days), 1) AS avg_transit_days,
    ROUND(SUM(variance_vs_contract_usd), 2) AS total_leakage_usd,
    
    -- Mode-Aware Performance Classification
    CASE 
        -- High Efficiency (Fast & Lean relative to their transport mode)
        WHEN mode_of_transport IN ('Road', 'Air') AND AVG(transit_days) <= 4 AND AVG(actual_rate_paid_usd) <= AVG(contracted_base_rate_usd) THEN 'High Efficiency (Fast & Lean)'
        WHEN mode_of_transport = 'Ocean' AND AVG(transit_days) <= 22 AND AVG(actual_rate_paid_usd) <= AVG(contracted_base_rate_usd) THEN 'High Efficiency (Fast & Lean)'
        
        -- Premium Speed (Fast transit, but paid above contract)
        WHEN AVG(actual_rate_paid_usd) > AVG(contracted_base_rate_usd) AND (
            (mode_of_transport IN ('Road', 'Air') AND AVG(transit_days) <= 4) OR
            (mode_of_transport = 'Ocean' AND AVG(transit_days) <= 22)
        ) THEN 'Premium Speed (High Cost)'
        
        -- Severe Bottleneck (Slow transit and over budget)
        WHEN AVG(actual_rate_paid_usd) > AVG(contracted_base_rate_usd) AND (
            (mode_of_transport IN ('Road', 'Air') AND AVG(transit_days) > 6) OR
            (mode_of_transport = 'Ocean' AND AVG(transit_days) > 28)
        ) THEN 'Severe Bottleneck (Delayed & Overpriced)'
        
        ELSE 'Standard Performance'
    END AS operational_tier

FROM vw_freight_cost_variance
GROUP BY carrier_name, mode_of_transport
ORDER BY total_leakage_usd DESC;

-- Query the View
SELECT * FROM vw_carrier_tradeoffs;