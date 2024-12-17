import sqlite3
import requests

# SQLiteに接続
conn = sqlite3.connect("weather.db")
cursor = conn.cursor()

# 地域情報を追加する関数
def insert_region(region_code, region_name):
    cursor.execute("INSERT OR IGNORE INTO regions (region_code, region_name) VALUES (?, ?)", 
                   (region_code, region_name))
    conn.commit()
    return cursor.lastrowid

# 天気情報を追加する関数
def insert_weather(region_id, date, weather, max_temp, min_temp):
    cursor.execute("""
    INSERT INTO weather (region_id, date, weather, max_temp, min_temp) 
    VALUES (?, ?, ?, ?, ?)
    """, (region_id, date, weather, max_temp, min_temp))
    conn.commit()

# 日本気象庁のAPIから天気情報を取得
def fetch_weather(region_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"エラー: {response.status_code}")
        return None

# 天気情報を取得してDBに保存する
def save_weather(region_code, region_name):
    # 地域情報をDBに格納
    region_id = insert_region(region_code, region_name)
    
    # 天気情報を取得
    weather_data = fetch_weather(region_code)
    if weather_data:
        time_series = weather_data[0]["timeSeries"][0]
        for i, weather in enumerate(time_series["areas"][0]["weathers"]):
            date = time_series["timeDefines"][i]
            max_temp = weather_data[1]["tempAverage"]["areas"][0]["max"]
            min_temp = weather_data[1]["tempAverage"]["areas"][0]["min"]
            insert_weather(region_id, date, weather, max_temp, min_temp)

# 終了
conn.close()
