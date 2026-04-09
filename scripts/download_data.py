import requests
import pandas as pd
import time
import os
import json


def get_fund_list():
    """Get list of all mutual funds from AMFI (official source, reliable)"""
    print("Fetching list of all mutual funds from AMFI...")
    url = "https://www.amfiindia.com/spages/NAVAll.txt"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    lines = response.text.strip().split("\n")
    funds = []
    for line in lines:
        parts = line.strip().split(";")
        if len(parts) == 6:
            try:
                scheme_code = int(parts[0].strip())
                scheme_name = parts[3].strip()
                if scheme_code and scheme_name:
                    funds.append({
                        "schemeCode": scheme_code,
                        "schemeName": scheme_name
                    })
            except ValueError:
                continue

    print(f"Found {len(funds)} total funds")
    return funds


def download_fund_data(scheme_code, scheme_name):
    """Download historical NAV data for one fund from mfapi.in"""
    url = f"https://api.mfapi.in/mf/{scheme_code}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if 'data' in data and len(data['data']) > 0:
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df['nav'] = pd.to_numeric(df['nav'])
            df['scheme_code'] = scheme_code
            df['scheme_name'] = scheme_name
            return df
        else:
            return None

    except Exception as e:
        print(f"  Error downloading: {e}")
        return None


def main():
    # Create data folder if it doesn't exist
    data_folder = '../data'
    os.makedirs(data_folder, exist_ok=True)

    # Get list of already downloaded funds
    existing_files = os.listdir(data_folder)
    existing_codes = set()
    for filename in existing_files:
        if filename.startswith('fund_') and filename.endswith('.csv'):
            code = filename.replace('fund_', '').replace('.csv', '')
            existing_codes.add(code)

    print(f"✓ Already have data for {len(existing_codes)} funds")

    # Get all funds from AMFI
    all_funds = get_fund_list()

    # Filter: Get only Equity funds
    equity_funds = [f for f in all_funds if 'equity' in f['schemeName'].lower()]
    print(f"✓ Filtered to {len(equity_funds)} equity funds")

    TARGET_FUNDS = 200
    selected_funds = equity_funds[:TARGET_FUNDS]
    print(f"\n🎯 Target: {TARGET_FUNDS} funds")

    # Filter out already downloaded funds
    new_funds = [f for f in selected_funds if str(f['schemeCode']) not in existing_codes]

    print(f"✓ Need to download: {len(new_funds)} new funds")
    print(f"✓ Already downloaded: {len(selected_funds) - len(new_funds)} funds")

    if len(new_funds) == 0:
        print("\n✓ All funds already downloaded!")
        return

    print(f"\nStarting download of {len(new_funds)} new funds...")
    print("This will take about {:.0f} minutes...\n".format(len(new_funds) * 1.5 / 60))

    successful = 0
    failed = 0
    skipped = 0
    all_fund_info = []

    for i, fund in enumerate(new_funds, 1):
        scheme_code = fund['schemeCode']
        scheme_name = fund['schemeName']

        print(f"[{i}/{len(new_funds)}] {scheme_name[:60]}...")

        df = download_fund_data(scheme_code, scheme_name)

        if df is not None:
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=2)

            if len(df) < 365:
                skipped += 1
                print(f"  ⚠ Skipped (only {len(df)} days, need 365+)")
            elif df['date'].max() < cutoff_date:
                skipped += 1
                print(f"  ⚠ Skipped (inactive fund, last date: {df['date'].max().date()})")
            else:
                filename = f"{data_folder}/fund_{scheme_code}.csv"
                df.to_csv(filename, index=False)

                all_fund_info.append({
                    'scheme_code': scheme_code,
                    'scheme_name': scheme_name,
                    'data_points': len(df),
                    'oldest_date': df['date'].min(),
                    'latest_date': df['date'].max()
                })

                successful += 1
                print(f"  ✓ Saved! ({len(df)} days of data)")
        else:
            failed += 1
            print(f"  ✗ Failed (no data available)")

        time.sleep(1)

    print(f"\n{'=' * 70}")
    print(f"DOWNLOAD COMPLETE!")
    print(f"{'=' * 70}")
    print(f"✓ Successfully downloaded: {successful} new funds")
    print(f"⚠ Skipped due to insufficient data: {skipped} funds")
    print(f"✗ Failed: {failed} funds")
    print(f"Total funds available: {len(existing_codes) + successful}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()