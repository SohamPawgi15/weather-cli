import requests
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from datetime import datetime

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
    with console.status(f"[bold green]Fetching detailed weather for {city_name}...") as status:
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
            timezone = location.get("timezone", "auto")
            
            # 2. Get Weather Data (Current + Daily + Hourly)
            # Added: apparent_temperature, relativehumidity_2m, precipitation, uv_index
            weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                           f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m"
                           f"&hourly=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code,sunrise,sunset,uv_index_max"
                           f"&timezone=auto")
            
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            
            # Extract Data
            current = weather_data['current']
            daily = weather_data['daily']
            hourly = weather_data['hourly']
            
            # Current Variables
            temp = current['temperature_2m']
            feels_like = current['apparent_temperature']
            humidity = current['relative_humidity_2m']
            wind_speed = current['wind_speed_10m']
            w_code = current['weather_code']
            uv_max = daily['uv_index_max'][0]
            sunrise = daily['sunrise'][0].split('T')[1]
            sunset = daily['sunset'][0].split('T')[1]

            # 3. Display Output using Rich Layout
            
            # Header
            header_text = Text(f"{get_weather_icon(w_code)}  Weather Report for {name}, {country}", style="bold cyan")
            console.print(Panel(header_text, expand=False))
            
            # Grid for Current Details
            grid = Table.grid(expand=True)
            grid.add_column(justify="center", ratio=1)
            grid.add_column(justify="center", ratio=1)
            
            # Left Side: Main Stats
            main_stats = f"""
[bold]Temperature:[/bold] [yellow]{temp}°C[/yellow]
[dim]Feels like {feels_like}°C[/dim]

[bold]Wind:[/bold] [blue]{wind_speed} km/h[/blue]
[bold]Humidity:[/bold] [blue]{humidity}%[/blue]
            """
            
            # Right Side: Extra Stats
            extra_stats = f"""
[bold]UV Index:[/bold] [magenta]{uv_max}[/magenta]
[bold]Sunrise:[/bold] 🌅 {sunrise}
[bold]Sunset:[/bold]  🌇 {sunset}
            """
            
            grid.add_row(Panel(main_stats, title="Current", style="green"), Panel(extra_stats, title="Details", style="blue"))
            console.print(grid)

            # Hourly Forecast (Next 12 hours)
            console.print(f"\n[bold]🕐 Next 12 Hours:[/bold]")
            hourly_table = Table(box=None, show_header=False)
            
            # Get current hour index
            current_hour_iso = current['time']
            # Find closest hour index (simple approach) in the hourly list
            start_index = 0
            for i, time in enumerate(hourly['time']):
                if time >= current_hour_iso:
                    start_index = i
                    break
            
            # Create row for times and row for temps
            times_row = []
            temps_row = []
            icons_row = []
            
            for i in range(start_index, start_index + 12, 3): # Every 3 hours
                if i >= len(hourly['time']): break
                time_str = hourly['time'][i].split('T')[1]
                t = hourly['temperature_2m'][i]
                c = hourly['weather_code'][i]
                
                times_row.append(f"[dim]{time_str}[/dim]")
                temps_row.append(f"[bold]{t}°C[/bold]")
                icons_row.append(get_weather_icon(c))

            hourly_grid = Table.grid(expand=True, padding=(0, 2))
            for _ in range(len(times_row)): hourly_grid.add_column(justify="center")
            
            hourly_grid.add_row(*times_row)
            hourly_grid.add_row(*icons_row)
            hourly_grid.add_row(*temps_row)
            
            console.print(Panel(hourly_grid, title="Hourly Trend", border_style="dim"))
            
            
            # 5-Day Forecast Table
            table = Table(title="📅 5-Day Forecast", show_header=True, header_style="bold magenta", expand=True)
            table.add_column("Date", style="dim")
            table.add_column("Condition", justify="center")
            table.add_column("Max/Min Temp", justify="center")
            table.add_column("UV", justify="right")

            for i in range(1, 6): # Start from tomorrow
                date = daily['time'][i]
                max_t = daily['temperature_2m_max'][i]
                min_t = daily['temperature_2m_min'][i]
                code = daily['weather_code'][i]
                uv = daily['uv_index_max'][i]
                icon = get_weather_icon(code)
                
                table.add_row(
                    date,
                    icon,
                    f"[red]{max_t}°[/red] / [blue]{min_t}°[/blue]",
                    str(uv)
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
