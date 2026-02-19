import requests
import sys
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.prompt import Prompt

console = Console()

# --- Helpers ---
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

def get_aqi_description(aqi):
    if aqi <= 20: return "[bold green]Good[/bold green]"
    if aqi <= 40: return "[bold green]Fair[/bold green]"
    if aqi <= 60: return "[bold yellow]Moderate[/bold yellow]"
    if aqi <= 80: return "[bold orange1]Poor[/bold orange1]"
    if aqi <= 100: return "[bold red]Very Poor[/bold red]"
    return "[bold purple]Extremely Poor[/bold purple]"

def get_coordinates(city_name):
    # Geocoding helper
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
    try:
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            console.print(f"[bold red]Error:[/bold red] City '{city_name}' not found.")
            return None, None, None, None

        location = geo_data['results'][0]
        return location['latitude'], location['longitude'], location['name'], location['country']
    except Exception as e:
        console.print(f"[bold red]Geocoding Error:[/bold red] {e}")
        return None, None, None, None

# --- Features ---

def show_weather(city_name):
    lat, lon, name, country = get_coordinates(city_name)
    if not lat: return

    with console.status(f"[bold green]Fetching weather for {name}...") as status:
        try:
            weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                           f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,cloud_cover,wind_speed_10m"
                           f"&hourly=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code,sunrise,sunset,uv_index_max"
                           f"&timezone=auto")
            
            response = requests.get(weather_url)
            data = response.json()
            
            current = data['current']
            daily = data['daily']
            hourly = data['hourly']
            
            # Header
            header_text = Text(f"{get_weather_icon(current['weather_code'])}  Weather Report for {name}, {country}", style="bold cyan")
            console.print(Panel(header_text, expand=False))
            
            # Current Grid
            grid = Table.grid(expand=True)
            grid.add_column(justify="center", ratio=1)
            grid.add_column(justify="center", ratio=1)
            
            main_stats = f"""
[bold]Temperature:[/bold] [yellow]{current['temperature_2m']}°C[/yellow]
[dim]Feels like {current['apparent_temperature']}°C[/dim]

[bold]Wind:[/bold] [blue]{current['wind_speed_10m']} km/h[/blue]
[bold]Humidity:[/bold] [blue]{current['relative_humidity_2m']}%[/blue]
            """
            
            extra_stats = f"""
[bold]UV Index:[/bold] [magenta]{daily['uv_index_max'][0]}[/magenta]
[bold]Sunrise:[/bold] 🌅 {daily['sunrise'][0].split('T')[1]}
[bold]Sunset:[/bold]  🌇 {daily['sunset'][0].split('T')[1]}
            """
            
            grid.add_row(Panel(main_stats, title="Current", style="green"), Panel(extra_stats, title="Details", style="blue"))
            console.print(grid)

            # Hourly Forecast
            console.print(f"\n[bold]🕐 Next 12 Hours:[/bold]")
            hourly_grid = Table.grid(expand=True, padding=(0, 2))
            
            # Find start index
            current_hour_iso = current['time']
            start_index = 0
            for i, time in enumerate(hourly['time']):
                if time >= current_hour_iso:
                    start_index = i
                    break
            
            times_row, temps_row, icons_row = [], [], []
            for i in range(start_index, start_index + 12, 3):
                if i >= len(hourly['time']): break
                time_str = hourly['time'][i].split('T')[1]
                times_row.append(f"[dim]{time_str}[/dim]")
                temps_row.append(f"[bold]{hourly['temperature_2m'][i]}°C[/bold]")
                icons_row.append(get_weather_icon(hourly['weather_code'][i]))

            for _ in range(len(times_row)): hourly_grid.add_column(justify="center")
            hourly_grid.add_row(*times_row)
            hourly_grid.add_row(*icons_row)
            hourly_grid.add_row(*temps_row)
            
            console.print(Panel(hourly_grid, title="Hourly Trend", border_style="dim"))
            
            # Daily Forecast
            table = Table(title="📅 5-Day Forecast", show_header=True, header_style="bold magenta", expand=True)
            table.add_column("Date", style="dim")
            table.add_column("Condition", justify="center")
            table.add_column("Max/Min Temp", justify="center")
            table.add_column("UV", justify="right")

            for i in range(1, 6):
                table.add_row(
                    daily['time'][i],
                    get_weather_icon(daily['weather_code'][i]),
                    f"[red]{daily['temperature_2m_max'][i]}°[/red] / [blue]{daily['temperature_2m_min'][i]}°[/blue]",
                    str(daily['uv_index_max'][i])
                )
            
            console.print(table)
            console.print("\n[dim]Data provided by Open-Meteo[/dim]\n")

        except Exception as e:
            console.print(f"[bold red]Error fetching weather:[/bold red] {e}")

def show_air_quality(city_name):
    lat, lon, name, country = get_coordinates(city_name)
    if not lat: return

    with console.status(f"[bold green]Fetching air quality for {name}...") as status:
        try:
            aq_url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
                      f"&current=european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,uv_index"
                      f"&timezone=auto")
            
            response = requests.get(aq_url)
            data = response.json()
            current = data['current']

            # Header
            header_text = Text(f"🍃 Air Quality Report for {name}, {country}", style="bold green")
            console.print(Panel(header_text, expand=False))

            # Main AQI
            aqi = current['european_aqi']
            desc = get_aqi_description(aqi)
            
            console.print(Align.center(f"\n[bold]European AQI:[/bold] [bold size=30]{aqi}[/bold size]"))
            console.print(Align.center(f"{desc}\n"))

            # Details Table
            table = Table(show_header=True, header_style="bold green", expand=True)
            table.add_column("Pollutant", style="cyan")
            table.add_column("Concentration", justify="right")
            table.add_column("Unit", style="dim")

            pollutants = {
                "PM2.5 (Fine Particles)": ("pm2_5", "µg/m³"),
                "PM10 (Coarse Particles)": ("pm10", "µg/m³"),
                "Nitrogen Dioxide (NO₂)": ("nitrogen_dioxide", "µg/m³"),
                "Ozone (O₃)": ("ozone", "µg/m³"),
                "Sulphur Dioxide (SO₂)": ("sulphur_dioxide", "µg/m³"),
                "Carbon Monoxide (CO)": ("carbon_monoxide", "µg/m³"),
                "Dust": ("dust", "µg/m³"),
                "UV Index": ("uv_index", "")
            }

            for label, (key, unit) in pollutants.items():
                val = current.get(key)
                if val is not None:
                    table.add_row(label, str(val), unit)

            console.print(Panel(table, title="Pollutant Details"))
            console.print("\n[dim]Data provided by Open-Meteo Air Quality API[/dim]\n")

        except Exception as e:
            console.print(f"[bold red]Error fetching air quality:[/bold red] {e}")

def main():
    console.print("\n[bold magenta]🌦️  Weather CLI Tool v2.0  🍃[/bold magenta]")

    # Check for interactive mode (no arguments)
    if len(sys.argv) == 1:
        console.print("[yellow]No command specified. Entering interactive mode...[/yellow]")
        city = Prompt.ask("[bold cyan]Enter city name[/bold cyan]")
        mode = Prompt.ask("[bold cyan]Choose mode[/bold cyan]", choices=["weather", "air"], default="weather")
        # Direct call
        if mode == "weather":
            show_weather(city)
        else:
            show_air_quality(city)
        return

    # Check for "backward compatibility" mode (no subcommand)
    # If the first argument isn't a known command, assume it's a city for 'weather'
    if len(sys.argv) > 1 and sys.argv[1] not in ["weather", "air", "-h", "--help"]:
        city_name = " ".join(sys.argv[1:])
        show_weather(city_name)
        return

    # Standard Argument Parsing
    parser = argparse.ArgumentParser(description="Multi-functional Weather CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Weather Command
    weather_parser = subparsers.add_parser("weather", help="Get weather forecast")
    weather_parser.add_argument("city", nargs="+", help="Name of the city")

    # Air Quality Command
    air_parser = subparsers.add_parser("air", help="Get air quality data")
    air_parser.add_argument("city", nargs="+", help="Name of the city")

    args = parser.parse_args()

    if args.command == "weather":
        show_weather(" ".join(args.city))
    elif args.command == "air":
        show_air_quality(" ".join(args.city))

if __name__ == "__main__":
    main()
