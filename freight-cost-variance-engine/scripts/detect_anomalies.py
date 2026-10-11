import os
import pandas as pd
from sqlalchemy import create_engine

# Database Connection Parameters
DB_USER = "tejdeepreddygudise"  
DB_PASSWORD = ""      
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "freight_db"

# Create SQLAlchemy connection engine
db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def run_anomaly_audit_and_exports():
    print("=" * 70)
    print(" 🚨 FREIGHT COST LEAKAGE & SPEND ANOMALY AUDIT ENGINE")
    print("=" * 70)
    
    # Ensure docs folder exists
    os.makedirs("docs", exist_ok=True)
    
    # 1. Fetch the complete dataset from the view (Great for Power BI web service)
    print("📥 Fetching full analytical dataset from PostgreSQL...")
    full_query = "SELECT * FROM vw_freight_cost_variance;"
    df_full = pd.read_sql(full_query, con=engine)
    
    pbi_export_path = "docs/freight_variance_export.csv"
    df_full.to_csv(pbi_export_path, index=False)
    print(f"✅ Power BI Master CSV successfully exported to `{pbi_export_path}` ({len(df_full):,} rows)")
    
    # 2. Filter in-memory for transactions exceeding the \$500 cost leakage threshold
    df_anomalies = df_full[df_full['variance_vs_contract_usd'] > 500.00].sort_values(
        by='variance_vs_contract_usd', ascending=False
    )
    
    if df_anomalies.empty:
        print("✅ No critical cost leakage anomalies found above the \$500 threshold.")
    else:
        print(f"\n⚠️ ALERT: Detected {len(df_anomalies):,} high-variance transactions exceeding \$500 leakage!\n")
        
        # Select key columns for clean terminal display
        display_cols = [
            'transaction_id', 'transaction_date', 'origin_hub', 
            'destination_hub', 'carrier_name', 'variance_vs_contract_usd', 'cost_performance_status'
        ]
        print(df_anomalies[display_cols].to_string(index=False))
        
        # Export stakeholder anomaly audit log
        audit_output_path = "docs/cost_leakage_audit_report.csv"
        df_anomalies.to_csv(audit_output_path, index=False)
        print("\n" + "-" * 70)
        print(f"📄 Stakeholder Audit Report successfully exported to `{audit_output_path}`")
    
    print("=" * 70)

if __name__ == "__main__":
    run_anomaly_audit_and_exports()