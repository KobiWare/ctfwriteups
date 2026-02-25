import pyogrio
import pandas as pd
from pathlib import Path

mmsi = 311714000
data_dir = Path(".")

print(f"🚢 FINAL FIXED ANALYSIS for MMSI {mmsi} — January 2009\n")

gdb_folders = sorted(data_dir.glob("Zone*_2009_01.gdb"))
if not gdb_folders:
    print("❌ No .gdb folders found!")
    exit()

all_data = []
for gdb in gdb_folders:
    print(f"📂 Loading {gdb.name} ...")
    try:
        # use_arrow=False is the key fix for the categorical error
        gdf = pyogrio.read_dataframe(
            str(gdb),
            layer="Broadcast",
            where=f"MMSI = {mmsi}",
            use_arrow=False
        )

        if not gdf.empty:
            gdf = gdf.copy()

            # Extract LAT/LON from geometry column (NOAA 2009 style)
            if "geometry" in gdf.columns:
                gdf["LON"] = gdf.geometry.x
                gdf["LAT"] = gdf.geometry.y
                gdf = gdf.drop(columns=["geometry"])

            # Standardize column names just in case
            gdf.rename(columns={
                "Latitude": "LAT", "Longitude": "LON",
                "baseDateTime": "BaseDateTime", "Sog": "SOG", "Cog": "COG"
            }, inplace=True)

            print(f"   → {len(gdf):,} positions loaded")
            all_data.append(gdf[['BaseDateTime', 'LAT', 'LON', 'SOG', 'COG']])

    except Exception as e:
        print(f"   ⚠️ {e}")

if not all_data:
    print("❌ Still no data — try re-downloading Zone16 and Zone17.")
    exit()

df = pd.concat(all_data, ignore_index=True)
df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"])
df = df.sort_values("BaseDateTime").reset_index(drop=True)

# Daily counts (confirms the gap on Jan 20)
daily = df["BaseDateTime"].dt.strftime("%Y-%m-%d").value_counts().sort_index()
print("\n📅 Daily AIS transmissions in January 2009:")
print(daily)

# Show positions on Jan 19 and Jan 21 (the closest days)
for day in [19, 21]:
    day_df = df[df["BaseDateTime"].dt.day == day]
    if not day_df.empty:
        print(f"\n{'='*80}")
        print(f"📍 POSITIONS ON 2009-01-{day:02d}  ({len(day_df)} records)")
        print("="*80)
        print(day_df[["BaseDateTime", "LAT", "LON", "SOG"]].head(6).to_string(index=False))
        print("   ...")
        print(day_df[["BaseDateTime", "LAT", "LON", "SOG"]].tail(6).to_string(index=False))

df.to_csv(f"MMSI_{mmsi}_Jan2009_FINAL.csv", index=False)
print(f"\n💾 All data saved to MMSI_{mmsi}_Jan2009_FINAL.csv")
print("\n✅ Run complete!")
print("Now copy-paste the LAT/LON pairs from 2009-01-19 or 2009-01-21 here.")
print("I'll reverse-geocode them and tell you the exact nearest city/port/anchorage.")