import datetime
import random
import re
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# 1. Database Connection Parameters
DB_USER = "tejdeepreddygudise"  
DB_PASSWORD = ""      
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "freight_db"

# Create Database Connection Engine
db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)

def clean_freight_data(df: pd.DataFrame) -> pd.DataFrame:
    print("=" * 60)
    print(" 🧹 RUNNING PRODUCTION DATA CLEANING & VALIDATION PIPELINE")
    print("=" * 60)
    
    initial_row_count = len(df)
    
    # 1. STEP 1: Standardize and Clean `lane_id` first using Regex & Pattern Extraction
    # Handles messy variations like 'lane001', 'lane\$001', 'lane@01', 'Lane 001', 'lANe001', 'laNE-001'
    def standardize_lane_id(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        digits = re.findall(r'\d+', val_str)
        if digits:
            return f"LANE-{digits[0].zfill(3)}"
        return val_str.upper()
        
    if 'lane_id' in df.columns:
        df['lane_id'] = df['lane_id'].apply(standardize_lane_id)
    
    # 2. Clean Text Columns
    text_cols = ['mode_of_transport', 'carrier_name']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            
    # 3. Standardize Transport Mode Categories & Fix Typos
    mode_mapping = {
        "Oean": "Ocean", 
        "Ocann": "Ocean", 
        "Maritime": "Ocean",
        "Aviation": "Air", 
        "Truck": "Road", 
        "Ftl": "Road", 
        "Ltl": "Road"
    }
    df['mode_of_transport'] = df['mode_of_transport'].replace(mode_mapping)
    valid_modes = ['Ocean', 'Air', 'Road']
    df = df[df['mode_of_transport'].isin(valid_modes)]
    
    # 4. Standardize Carrier Name Aliases
    carrier_mapping = {
        "Maersk Line": "Maersk",
        "Msc S.A.": "MSC",
        "Cma-Cgm": "CMA CGM",
        "Fedex": "FedEx Express"
    }
    df['carrier_name'] = df['carrier_name'].replace(carrier_mapping)
    
    # 5. Clean Numeric Rate Fields (Strip symbols like '\$' or commas, coerce errors)
    rate_cols = ['actual_rate_paid_usd', 'market_spot_rate_usd']
    for col in rate_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\$,]', '', regex=True).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 6. Parse and Standardize Dates Safely
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df = df.dropna(subset=['transaction_date'])
    df['transaction_date'] = df['transaction_date'].dt.date
    
    # 7. Clean Transit Days & Apply Boundary Checks
    df['transit_days'] = pd.to_numeric(df['transit_days'], errors='coerce')
    df = df.dropna(subset=['transit_days'])
    
    df = df[
        (df['actual_rate_paid_usd'] > 0) & 
        (df['market_spot_rate_usd'] > 0) & 
        (df['transit_days'] >= 0) & 
        (df['transit_days'] <= 120)
    ]
    
    # 8. Drop NaNs in critical fields
    critical_cols = ['lane_id', 'transaction_date', 'actual_rate_paid_usd', 'market_spot_rate_usd']
    df = df.dropna(subset=critical_cols)
    
    dropped_count = initial_row_count - len(df)
    print(f"📊 Data Pipeline Summary:")
    print(f"   - Initial Raw Records Generated: {initial_row_count:,}")
    print(f"   - Successfully Validated & Cleaned: {len(df):,}")
    print(f"   - Filtered Invalid/Outlier Records: {dropped_count:,}")
    print("=" * 60)
    
    return df

def generate_and_ingest_data():
    # Define multi-modal trade lanes synchronized with dim_shipping_lanes
    lanes = [
        # Ocean Lanes
        {"lane_id": "LANE-001", "mode": "Ocean", "base": 2800.00, "carriers": ["Maersk", "MSC", "CMA CGM"]},
        {"lane_id": "LANE-002", "mode": "Ocean", "base": 2600.00, "carriers": ["Ocean Network Express", "Hapag-Lloyd", "Evergreen"]},
        {"lane_id": "LANE-003", "mode": "Ocean", "base": 1100.00, "carriers": ["Maersk", "COSCO", "Evergreen"]},
        
        # Air Freight Lanes
        {"lane_id": "LANE-004", "mode": "Air", "base": 6500.00, "carriers": ["FedEx Express", "DHL Aviation", "Emirates SkyCargo"]},
        {"lane_id": "LANE-005", "mode": "Air", "base": 4800.00, "carriers": ["Qatar Airways Cargo", "Lufthansa Cargo", "Atlas Air"]},
        
        # Road / FTL Trucking Lanes
        {"lane_id": "LANE-006", "mode": "Road", "base": 850.00,  "carriers": ["Swift Transportation", "JB Hunt", "Schneider"]},
        {"lane_id": "LANE-007", "mode": "Road", "base": 950.00,  "carriers": ["Old Dominion", "XPO Logistics", "Knight Transportation"]}
    ]

    start_date = datetime.date(2026, 1, 1)
    records = []

    # Generate 180 days of transaction data across all modes
    for i in range(180):
        current_date = start_date + datetime.timedelta(days=i)
        for lane in lanes:
            spot_multiplier = random.uniform(0.85, 1.25)
            market_spot_rate = round(lane["base"] * spot_multiplier, 2)
            actual_paid = round(market_spot_rate * random.uniform(0.95, 1.12), 2)
            
            if lane["mode"] == "Air":
                transit_days = random.randint(1, 3)
            elif lane["mode"] == "Road":
                transit_days = random.randint(2, 6)
            else:
                transit_days = random.randint(14, 32)
            
            records.append({
                "lane_id": lane["lane_id"],
                "mode_of_transport": lane["mode"], # Used during cleaning validation
                "transaction_date": current_date,
                "actual_rate_paid_usd": actual_paid,
                "market_spot_rate_usd": market_spot_rate,
                "carrier_name": random.choice(lane["carriers"]),
                "transit_days": transit_days
            })

    df_raw = pd.DataFrame(records)
    
    # Process through cleaning and validation pipeline
    df_cleaned = clean_freight_data(df_raw)

    # Star Schema Rule: `mode_of_transport` belongs in dim_shipping_lanes, 
    # so we drop it from the dataframe before inserting into `fact_freight_transactions`.
    df_fact = df_cleaned.drop(columns=['mode_of_transport'], errors='ignore')

    # Append validated clean data into PostgreSQL fact table
    try:
        df_fact.to_sql('fact_freight_transactions', con=engine, if_exists='append', index=False)
        print(f"✅ Successfully ingested {len(df_fact):,} multi-modal freight records into 'fact_freight_transactions'!")
    except Exception as e:
        print(f"❌ Error during data ingestion: {e}")

if __name__ == "__main__":
    generate_and_ingest_data()