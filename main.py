import requests
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def get_weather_icon(code):
    # WMO Weather interpretation codes (WW)
    if code == 0: return "☀️"
    if code in [1, 2, 3]: return "⛅"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55]: return "🌧️"
    if code in [61, 63, 65]: return "🌧️"
    if code in [80, 81, 82]: return "🌦️"
    if code >= 95: return "⛈️"
    return "🌡️"

def get_weather(city_name):
    with console.status(f"[bold green]Fetching weather for {city_name}...") as status:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        
        try:
            geo_response = requests.get(geo_url)
            geo_data = geo_response.json()
            
            if not geo_data.get('results'):
                console.print(f"[bold red]Error:[/bold red] City '{city_name}' not found.")
                return

            location = geo_data['results'][0]
            lat = location['latitude']
            lon = location['longitude']
            country = location['country']
            name = location['name']
            
            # 2. Get Weather Data (Current + Daily Forecast)
            weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                           f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode"
                           f"&timezone=auto")
            
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            
            # Current Weather
            current = weather_data['current_weather']
            temp = current['temperature']
            wind = current['windspeed']
            w_code = current['weathercode']
            
            # 3. Display Output using Rich
            
            # Header Panel
            header_text = Text(f"{get_weather_icon(w_code)}  Weather Report for {name}, {country}", style="bold cyan")
            console.print(Panel(header_text, expand=False))
            
            # Current Details
            console.print(f"\n[bold]Current Conditions:[/bold]")
            console.print(f"🌡️  Temperature: [bold yellow]{temp}°C[/bold yellow]")
            console.print(f"💨 Wind Speed:  [bold blue]{wind} km/h[/bold blue]")
            console.print("")

            # Forecast Table
            table = Table(title="📅 5-Day Forecast", show_header=True, header_style="bold magenta")
            table.add_column("Date", style="dim")
            table.add_column("Condition", justify="center")
            table.add_column("Max Temp", justify="right")
            table.add_column("Min Temp", justify="right")

            daily = weather_data['daily']
            for i in range(5):
                date = daily['time'][i]
                max_t = daily['temperature_2m_max'][i]
                min_t = daily['temperature_2m_min'][i]
                code = daily['weathercode'][i]
                icon = get_weather_icon(code)
                
                table.add_row(
                    date,
                    icon,
                    f"[red]{max_t}°C[/red]",
                    f"[blue]{min_t}°C[/blue]"
                )
            
            console.print(table)
            console.print("\n[dim]Data provided by Open-Meteo[/dim]\n")

        except Exception as e:
            console.print(f"[bold red]An error occurred:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[bold yellow]Usage:[/bold yellow] python main.py [city_name]")
    else:
        city = " ".join(sys.argv[1:])
        get_weather(city)
