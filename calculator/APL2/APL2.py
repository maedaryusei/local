import flet as ft
import requests

# 地域リスト取得関数
def fetch_region_codes():
    url = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data)  # デバッグ用にレスポンス内容を出力
            return {
                region["name"]: code
                for code, region in data["class10s"].items()
            }
        else:
            print(f"地域リストの取得に失敗しました。ステータスコード: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"リクエスト中にエラーが発生しました: {e}")
        return None
    except ValueError as e:
        print(f"レスポンスの解析中にエラーが発生しました: {e}")
        return None


# 天気データ取得関数
def fetch_weather(region_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/"
    print(f"リクエストURL: {url}")  # デバッグ用
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"天気データの取得に失敗しました。ステータスコード: {response.status_code}")
            print(response.text)  # エラー内容を出力
            return None
    except requests.exceptions.RequestException as e:
        print(f"リクエスト中にエラーが発生しました: {e}")
        return None
    except ValueError as e:
        print(f"レスポンスの解析中にエラーが発生しました: {e}")
        return None


# アプリのメイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "adaptive"

    # 地域データ取得
    region_codes = fetch_region_codes()

    if region_codes is None:
        # エラーメッセージを表示
        page.add(ft.Text("地域リストの取得に失敗しました。後でもう一度試してください。", color="red"))
        return

    # UIの要素を管理
    selected_region = ft.Ref[ft.Dropdown]()
    weather_data = ft.Ref[ft.Column]()
    error_message = ft.Ref[ft.Text]()

    # 地域が変更されたときに天気を更新する関数
    def update_weather(e):
        region_name = selected_region.current.value
        if region_name:
            region_code = region_codes.get(region_name)
            if region_code:
                data = fetch_weather(region_code)
                if data:
                    error_message.current.text = ""
                    weather_data.current.controls.clear()
                    forecasts = data[0].get("timeSeries", [])
                    if forecasts:
                        area_forecasts = forecasts[0].get("areas", [])
                        for forecast in area_forecasts:
                            if forecast["area"]["code"] == region_code:
                                for i, weather in enumerate(forecast["weathers"]):
                                    weather_data.current.controls.append(
                                        ft.Container(
                                            content=ft.Column([
                                                ft.Text(f"日付: {forecasts[0]['timeDefines'][i]}"),
                                                ft.Text(f"天気: {weather}"),
                                                ft.Text(f"最高気温: {data[1]['tempAverage']['areas'][0]['max']}°C"),
                                                ft.Text(f"最低気温: {data[1]['tempAverage']['areas'][0]['min']}°C"),
                                            ]),
                                            padding=10,
                                            border=ft.border.all(1, "black"),
                                            margin=5,
                                        )
                                    )
                                break
                    page.update()
                else:
                    error_message.current.text = "天気データは利用できませんでした。"
                    page.update()
            else:
                error_message.current.text = "地域コードが見つかりませんでした。"
                page.update()

    # UIを作成
    page.add(
        ft.Column([
            ft.Dropdown(
                ref=selected_region,
                label="地域を選択",
                options=[
                    ft.dropdown.Option(name, name)
                    for name in region_codes.keys()
                ],
                on_change=update_weather,
            ),
            ft.Text(ref=error_message, color="red"),
            ft.Column(ref=weather_data),
        ])
    )

# アプリの実行
if __name__ == "__main__":
    ft.app(target=main)