from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
from difflib import get_close_matches

app = Flask(__name__)

API_KEY = "1a45e0667b1074687306201df0cf198f"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
ONECALL_URL = "https://api.openweathermap.org/data/2.5/onecall/timemachine"

@app.route('/')
def home():
    return render_template('index.html')


def fetch_weather(city):
    """Fetch current weather details for a city."""
    try:
        params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        weather_info = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'description': data['weather'][0]['description'].title(),
            'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
            'pressure': data['main']['pressure'],
            'visibility': data.get('visibility', 'N/A'),
            'icon': data['weather'][0]['icon'],
            'lat': data['coord']['lat'],
            'lon': data['coord']['lon']
        }
        return weather_info
    except:
        return None


def fetch_historical_weather(lat, lon, days_ago):
    """Fetch past weather using One Call Timemachine API."""
    dt = int((datetime.utcnow() - timedelta(days=days_ago)).timestamp())
    params = {'lat': lat, 'lon': lon, 'dt': dt, 'appid': API_KEY, 'units': 'metric'}
    res = requests.get(ONECALL_URL, params=params)
    if res.status_code == 200:
        data = res.json()
        weather = data['current']
        return {
            'temp': weather['temp'],
            'desc': weather['weather'][0]['description'].title(),
            'icon': weather['weather'][0]['icon']
        }
    return None


@app.route('/get_weather', methods=['POST'])
def get_weather():
    user_input = request.json.get('city')
    if not user_input:
        return jsonify({"error": "Please enter a city name"}), 400

    weather = fetch_weather(user_input)

    if not weather:
        # suggest similar names
        possible_cities = ["London", "Paris", "Berlin", "New York", "Tokyo", "Sydney", "Mumbai", "Chennai", "Delhi", "Toronto", "Bangalore", "Hyderabad"]
        suggestion = get_close_matches(user_input.title(), possible_cities, n=1, cutoff=0.6)
        if suggestion:
            return jsonify({"suggestion": suggestion[0]})
        else:
            return jsonify({"error": f"'{user_input}' seems out of my reach. Please enter another valid city."})

    lat, lon = weather['lat'], weather['lon']
    yesterday = fetch_historical_weather(lat, lon, 1)
    tomorrow = {"temp": round(weather['temperature'] + 1.5, 1), "desc": "Likely similar weather tomorrow 🌤", "icon": weather['icon']}

    return jsonify({
        "current": weather,
        "yesterday": yesterday,
        "tomorrow": tomorrow
    })


if __name__ == '__main__':
    app.run(debug=True)
