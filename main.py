import requests
import sys

# 1. Define the function to get weather
def get_weather(city_name):
    # Hardcoded coordinates for demo simplicity (London). 
    # To make this advanced, you can add a geocoding step later.
    # For now, let's use London as default or allow manual lat/long input.
    
    # Let's use Open-Meteo's Geocoding API to find the city first
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
    
    try:
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            print(f"Error: City '{city_name}' not found.")
            return

        # Extract lat/long
        location = geo_data['results'][0]
        lat = location['latitude']
        lon = location['longitude']
        country = location['country']
        
        # 2. Get Weather Data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        
        current = weather_data['current_weather']
        temp = current['temperature']
        wind = current['windspeed']
        
        # 3. Display Output
        print(f"\n--- Weather Report for {location['name']}, {country} ---")
        print(f"🌡️  Temperature: {temp}°C")
        print(f"💨 Wind Speed:  {wind} km/h")
        print("------------------------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")

# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [city_name]")
    else:
        city = " ".join(sys.argv[1:])
        get_weather(city)
