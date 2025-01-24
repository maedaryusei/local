import requests
from bs4 import BeautifulSoup
import sqlite3
import time

# データベースの設定
conn = sqlite3.connect('suumo_properties.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        price TEXT,
        area REAL,
        year_built TEXT,
        station_distance TEXT
    )
''')
conn.commit()

# スクレイピング処理
def scrape_suumo(page_limit=5):
    base_url = 'https://suumo.jp/chintai/tokyo/sc_shinjuku/'
    page = 1

    while page <= page_limit:
        url = f"{base_url}?page={page}"
        print(f"Scraping page {page}...")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code != 200:
            print(f"Failed to retrieve page {page}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')

        # 物件リストを取得
        listings = soup.find_all('div', class_='cassetteitem')

        for listing in listings:
            # 価格の取得
            price_tag = listing.find('span', class_='cassetteitem_price')
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            # 面積の取得
            area_tag = listing.find('span', class_='cassetteitem_menseki')
            area = area_tag.get_text(strip=True).replace("m²", "") if area_tag else "N/A"

            # **築年数の取得（クラス名を調査して修正）**
            year_built_tag = listing.find('div', class_='cassetteitem_detail')
            year_built = "N/A"
            if year_built_tag:
                year_info = year_built_tag.get_text(strip=True)
                if "築" in year_info:
                    year_built = year_info.replace("築", "").strip()

            # **最寄駅からの距離の取得**
            station_distance_tag = listing.find('div', class_='cassetteitem_detail-text')
            station_distance = station_distance_tag.get_text(strip=True) if station_distance_tag else "N/A"
            station_distance = station_distance.replace("徒歩", "").replace("分", "").strip()

            # データベースに保存
            c.execute('''
                INSERT INTO properties (price, area, year_built, station_distance)
                VALUES (?, ?, ?, ?)
            ''', (price, area, year_built, station_distance))
            conn.commit()

            print(f"Price: {price}, Area: {area}m², Year Built: {year_built}, Station Distance: {station_distance} min")

        page += 1
        time.sleep(1)

    conn.close()
    print("Scraping completed!")

if __name__ == "__main__":
    scrape_suumo(page_limit=5)

import pandas as pd
import sqlite3
import re

# Load the data from SQLite
conn = sqlite3.connect('suumo_properties.db')
df = pd.read_sql_query("SELECT id, price, area, year_built, station_distance FROM properties;", conn)
conn.close()

# Clean price (remove '万円' and convert to integer)
df['price'] = df['price'].str.replace('万円', '').astype(float) * 10000

# Clean area (remove unit inconsistencies like "m2" or "m²")
df['area'] = df['area'].str.replace(r'[m²m2]', '', regex=True).astype(float)

# Extract numerical values from station distance (convert "歩10min" → 10)
df['station_distance'] = df['station_distance'].apply(lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else None)

# Calculate price per square meter
df['price_per_sqm'] = df['price'] / df['area']

# Display the cleaned data
print(df.head())

import matplotlib.pyplot as plt
import seaborn as sns

# 散布図を描画
plt.figure(figsize=(10, 6))
sns.scatterplot(x=df['station_distance'], y=df['price_per_sqm'])

# グラフのタイトルとラベル
plt.title('Scatter Plot of Price per Sqm vs Station Distance')
plt.xlabel('Distance to Station (min)')
plt.ylabel('Price per sqm (yen)')
plt.grid(True)

# グラフを表示
plt.show()
