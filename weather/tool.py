# name: Погода
# icon: fa-cloud-sun
# description: Прогноз погоды по названию города
# requirements: requests

import os
import json
import html
import datetime
import requests

WMO = {
    0: ('☀️', 'Ясно'), 1: ('🌤', 'Преим. ясно'), 2: ('⛅', 'Переменная облачность'),
    3: ('☁️', 'Пасмурно'), 45: ('🌫', 'Туман'), 48: ('🌫', 'Изморозь'),
    51: ('🌦', 'Морось слабая'), 53: ('🌦', 'Морось'), 55: ('🌦', 'Морось сильная'),
    61: ('🌧', 'Дождь слабый'), 63: ('🌧', 'Дождь'), 65: ('🌧', 'Дождь сильный'),
    71: ('🌨', 'Снег слабый'), 73: ('🌨', 'Снег'), 75: ('❄️', 'Снег сильный'),
    80: ('🌦', 'Ливень слабый'), 81: ('🌧', 'Ливень'), 82: ('⛈', 'Ливень сильный'),
    95: ('⛈', 'Гроза'), 96: ('⛈', 'Гроза с градом'), 99: ('⛈', 'Гроза с градом'),
}
DAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


def read_last_city():
    """Тот же файл, что использует window.toolStorage на клиенте, — можно
    читать его и напрямую из Python при генерации страницы."""
    storage_path = os.environ.get('TOOL_STORAGE_PATH')
    if storage_path and os.path.exists(storage_path):
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            city = data.get('last_city')
            if city:
                return city
        except Exception:
            pass
    return 'Москва'


def fetch_weather(city):
    geo = requests.get(
        'https://geocoding-api.open-meteo.com/v1/search',
        params={'name': city, 'count': 1, 'language': 'ru', 'format': 'json'},
        timeout=10
    ).json()
    if not geo.get('results'):
        return None, None
    place = geo['results'][0]
    forecast = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params={
            'latitude': place['latitude'], 'longitude': place['longitude'],
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min,weather_code',
            'timezone': 'auto'
        },
        timeout=10
    ).json()
    return place, forecast


def render_current(place, w):
    icon, desc = WMO.get(w['current']['weather_code'], ('🌡', ''))
    city_label = html.escape(place['name'] + (f", {place['country']}" if place.get('country') else ''))
    return f'''
    <div class="current-card">
        <div class="city">{city_label}</div>
        <div class="temp">{icon} {round(w['current']['temperature_2m'])}°</div>
        <div class="desc">{html.escape(desc)}</div>
        <div class="meta">
            <span>💧 {w['current']['relative_humidity_2m']}%</span>
            <span>💨 {round(w['current']['wind_speed_10m'])} км/ч</span>
        </div>
    </div>'''


def render_forecast(w):
    cards = []
    for i, date in enumerate(w['daily']['time'][:6]):
        d_icon, _ = WMO.get(w['daily']['weather_code'][i], ('🌡', ''))
        weekday = datetime.date.fromisoformat(date).weekday()
        day_name = 'Сегодня' if i == 0 else DAY_NAMES[weekday]
        cards.append(f'''
        <div class="day-card">
            <div class="day-name">{day_name}</div>
            <div class="day-icon">{d_icon}</div>
            <div class="day-temps">{round(w['daily']['temperature_2m_max'][i])}° <span class="min">{round(w['daily']['temperature_2m_min'][i])}°</span></div>
        </div>''')
    return ''.join(cards)


last_city = read_last_city()
error_message = ''
current_html = ''
forecast_html = ''

try:
    place, w = fetch_weather(last_city)
    if place is None:
        error_message = f'Город «{html.escape(last_city)}» не найден'
    else:
        current_html = render_current(place, w)
        forecast_html = render_forecast(w)
except Exception as e:
    error_message = f'Не удалось загрузить погоду: {html.escape(str(e))}'

print(f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Погода</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 16px; min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(160deg, #4f8ef7, #7db8f9);
    color: #fff;
  }}
  h1 {{ font-size: 1.2rem; margin: 0 0 14px; text-align: center; }}
  .search-row {{ display: flex; gap: 8px; margin-bottom: 18px; }}
  .search-row input {{
    flex: 1; border: none; border-radius: 12px; padding: 12px 14px;
    font-size: 0.95rem; outline: none;
  }}
  .search-row button {{
    border: none; border-radius: 12px; padding: 0 16px;
    background: rgba(255,255,255,0.25); color: #fff; font-size: 1.1rem; cursor: pointer;
  }}
  .search-row button:active {{ background: rgba(255,255,255,0.4); }}
  #status {{ text-align: center; opacity: 0.85; font-size: 0.85rem; min-height: 20px; }}
  .current-card {{
    background: rgba(255,255,255,0.15); border-radius: 20px; padding: 22px;
    text-align: center; margin-bottom: 16px;
  }}
  .current-card .city {{ font-size: 1rem; opacity: 0.9; margin-bottom: 4px; }}
  .current-card .temp {{ font-size: 3rem; font-weight: 700; line-height: 1; }}
  .current-card .desc {{ font-size: 0.95rem; margin-top: 6px; opacity: 0.95; }}
  .current-card .meta {{ display: flex; justify-content: center; gap: 18px; margin-top: 14px; font-size: 0.8rem; opacity: 0.9; }}
  .forecast {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }}
  .day-card {{
    flex: 0 0 auto; width: 74px; background: rgba(255,255,255,0.15);
    border-radius: 14px; padding: 10px 6px; text-align: center; font-size: 0.75rem;
  }}
  .day-card .day-name {{ opacity: 0.85; margin-bottom: 6px; }}
  .day-card .day-icon {{ font-size: 1.4rem; margin-bottom: 6px; }}
  .day-card .day-temps {{ font-weight: 600; }}
  .day-card .day-temps .min {{ opacity: 0.7; font-weight: 400; }}
</style>
</head>
<body>
  <h1>🌤 Погода</h1>
  <div class="search-row">
    <input type="text" id="cityInput" placeholder="Введите город..." value="{html.escape(last_city)}" autocomplete="off">
    <button id="searchBtn">🔍</button>
  </div>
  <div id="status">{html.escape(error_message)}</div>
  <div id="currentCard">{current_html}</div>
  <div class="forecast" id="forecast">{forecast_html}</div>

<script>
// WMO weather codes -> [emoji, russian description] — тот же справочник,
// что и на сервере, но здесь нужен для дозагрузки без перезапуска Python.
const WMO = {{
  0: ['☀️', 'Ясно'], 1: ['🌤', 'Преим. ясно'], 2: ['⛅', 'Переменная облачность'],
  3: ['☁️', 'Пасмурно'], 45: ['🌫', 'Туман'], 48: ['🌫', 'Изморозь'],
  51: ['🌦', 'Морось слабая'], 53: ['🌦', 'Морось'], 55: ['🌦', 'Морось сильная'],
  61: ['🌧', 'Дождь слабый'], 63: ['🌧', 'Дождь'], 65: ['🌧', 'Дождь сильный'],
  71: ['🌨', 'Снег слабый'], 73: ['🌨', 'Снег'], 75: ['❄️', 'Снег сильный'],
  80: ['🌦', 'Ливень слабый'], 81: ['🌧', 'Ливень'], 82: ['⛈', 'Ливень сильный'],
  95: ['⛈', 'Гроза'], 96: ['⛈', 'Гроза с градом'], 99: ['⛈', 'Гроза с градом']
}};
const DAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

const cityInput = document.getElementById('cityInput');
const searchBtn = document.getElementById('searchBtn');
const statusEl = document.getElementById('status');
const currentCard = document.getElementById('currentCard');
const forecastEl = document.getElementById('forecast');

async function search() {{
  const city = cityInput.value.trim();
  if (!city) return;
  statusEl.textContent = 'Ищу город...';
  currentCard.innerHTML = '';
  forecastEl.innerHTML = '';
  try {{
    const geoResp = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${{encodeURIComponent(city)}}&count=1&language=ru&format=json`);
    const geo = await geoResp.json();
    if (!geo.results || !geo.results.length) {{
      statusEl.textContent = 'Город не найден';
      return;
    }}
    const {{ latitude, longitude, name, country }} = geo.results[0];

    const wResp = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${{latitude}}&longitude=${{longitude}}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto`);
    const w = await wResp.json();

    statusEl.textContent = '';
    const [icon, desc] = WMO[w.current.weather_code] || ['🌡', ''];
    currentCard.innerHTML = `
      <div class="current-card">
        <div class="city">${{name}}${{country ? ', ' + country : ''}}</div>
        <div class="temp">${{icon}} ${{Math.round(w.current.temperature_2m)}}°</div>
        <div class="desc">${{desc}}</div>
        <div class="meta">
          <span>💧 ${{w.current.relative_humidity_2m}}%</span>
          <span>💨 ${{Math.round(w.current.wind_speed_10m)}} км/ч</span>
        </div>
      </div>`;

    forecastEl.innerHTML = w.daily.time.slice(0, 6).map((date, i) => {{
      const [dIcon] = WMO[w.daily.weather_code[i]] || ['🌡'];
      const dayName = i === 0 ? 'Сегодня' : DAYS[new Date(date).getDay()];
      return `<div class="day-card">
        <div class="day-name">${{dayName}}</div>
        <div class="day-icon">${{dIcon}}</div>
        <div class="day-temps">${{Math.round(w.daily.temperature_2m_max[i])}}° <span class="min">${{Math.round(w.daily.temperature_2m_min[i])}}°</span></div>
      </div>`;
    }}).join('');

    // Запоминаем город на сервере (через toolStorage) — при следующем
    // открытии инструмента Python сразу подставит именно его.
    if (window.toolStorage) {{
      window.toolStorage.set('last_city', city).catch(() => {{}});
    }}
  }} catch (e) {{
    statusEl.textContent = 'Ошибка загрузки. Проверьте подключение к интернету.';
  }}
}}

searchBtn.addEventListener('click', search);
cityInput.addEventListener('keypress', (e) => {{ if (e.key === 'Enter') search(); }});
</script>
</body>
</html>''')
