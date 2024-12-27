import requests
import click
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

API_BASE_URL = "https://www.alphavantage.co/query"
API_KEY = "your_api_key_here"  # Replace with your actual API key

def create_border(width, title=""):
    """Create a decorative border with title."""
    top_border = f"╭{'─' * (width-2)}╮"
    if title:
        padding = (width - len(title) - 4) // 2
        title_line = f"│{' ' * padding}✧ {title} ✧{' ' * (width - padding - len(title) - 5)}│"
    else:
        title_line = None
    bottom_border = f"╰{'─' * (width-2)}╯"
    return (top_border, title_line, bottom_border)

def normalize_prices(prices, min_price, max_price, height):
    """Normalize prices to fit the desired height."""
    if max_price == min_price:
        return [0] * len(prices)
    return [int((p - min_price) / (max_price - min_price) * (height - 1)) for p in prices]

def format_price(price):
    """Format price with color based on value change."""
    return f"{price:,.2f}"

def generate_multi_series_ascii_graph(data_points_dict, timestamps):
    """Generate a vertically-scaled ASCII graph."""
    # Get dimensions for the graph (excluding borders)
    HEIGHT = 20  # Increased height for better resolution
    WIDTH = len(timestamps) * 3  # Increased spacing between points
    
    # Find overall min and max for proper scaling
    all_points = []
    for series in data_points_dict.values():
        all_points.extend(series)
    max_price = max(all_points)
    min_price = min(all_points)
    
    # Add padding to min/max for better visualization
    price_range = max_price - min_price
    padding = price_range * 0.1
    max_price += padding
    min_price -= padding
    
    # Normalize all series to fit the graph height
    normalized_data = {}
    for series_name, data_points in data_points_dict.items():
        normalized_data[series_name] = normalize_prices(data_points, min_price, max_price, HEIGHT)
    
    # Beautiful symbols for different series
    symbols = {
        'close': '⬤',
        'open': '◯',
        'high': '△',
        'low': '▽'
    }
    
    # Initialize the canvas with spaces
    canvas = [[' ' for _ in range(WIDTH + 2)] for _ in range(HEIGHT + 2)]
    
    # Draw vertical grid lines
    for x in range(0, WIDTH + 2, 3):
        for y in range(HEIGHT + 1):
            if canvas[y][x] == ' ':
                canvas[y][x] = '⋮'
    
    # Draw horizontal grid lines
    for y in range(HEIGHT + 1):
        if y % 4 == 0:  # Draw lines every 4 rows
            for x in range(WIDTH + 2):
                if canvas[y][x] == ' ':
                    canvas[y][x] = '⋅'
    
    # Plot each series
    for series_name, norm_points in normalized_data.items():
        symbol = symbols[series_name]
        for i, value in enumerate(norm_points):
            x = i * 3 + 1  # Space points further apart
            y = HEIGHT - value - 1  # Flip Y-axis
            canvas[y][x] = symbol
    
    # Generate the graph with beautiful borders
    graph_lines = []
    
    # Add title
    title = "✧ Price Chart ✧"
    total_width = WIDTH + 30  # Add space for y-axis labels
    graph_lines.append(f"{Fore.CYAN}╭{'─' * (total_width-2)}╮{Style.RESET_ALL}")
    padding = (total_width - len(title) - 2) // 2
    graph_lines.append(f"{Fore.CYAN}│{' ' * padding}{title}{' ' * (total_width - padding - len(title) - 2)}│{Style.RESET_ALL}")
    
    # Add legend
    legend = " ".join([f"{Fore.YELLOW}{symbols[name]}{Style.RESET_ALL} {name.capitalize()}" 
                      for name in data_points_dict.keys()])
    graph_lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} Legend: {legend}{' ' * (total_width - len(' Legend: ') - len(legend) - 2)}{Fore.CYAN}│{Style.RESET_ALL}")
    graph_lines.append(f"{Fore.CYAN}│{' ' * (total_width-2)}│{Style.RESET_ALL}")
    
    # Draw the price axis and main graph
    price_step = (max_price - min_price) / (HEIGHT - 1)
    for i, row in enumerate(canvas):
        if i == HEIGHT + 1:  # Skip the last row (will be used for timestamps)
            continue
        current_price = max_price - (i * price_step)
        price_str = f"{current_price:8.2f} "
        line = ''.join(row)
        graph_lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} {price_str}{Fore.YELLOW}{line}{Style.RESET_ALL}{' ' * (total_width - len(price_str) - len(line) - 3)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Add bottom border for X-axis
    graph_lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} {'─' * 8}╮{'─' * WIDTH}{' ' * (total_width - WIDTH - 11)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Add timestamps
    time_markers = []
    for ts in timestamps:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        time_markers.append(f"{dt.strftime('%H:%M')}")
    
    time_str = (" " * 10) + "  ".join(time_markers)
    graph_lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} {time_str}{' ' * (total_width - len(time_str) - 3)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Add final border
    graph_lines.append(f"{Fore.CYAN}╰{'─' * (total_width-2)}╯{Style.RESET_ALL}")
    
    return "\n".join(graph_lines)

def format_summary_box(symbol, latest, price_data, price_change, price_change_pct):
    """Create a decorative summary box."""
    lines = []
    width = 50
    
    # Create decorative border
    top, title, bottom = create_border(width, f"✦ {symbol.upper()} ✦")
    
    lines.append(f"{Fore.CYAN}{top}{Style.RESET_ALL}")
    lines.append(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
    
    # Add timestamp with cute decoration
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} ⌚ Latest Update: {latest}{' ' * (width - len(' ⌚ Latest Update: ' + latest) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Add prices with symbols
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} ▲ Open:  {Fore.GREEN}{format_price(price_data['open'][0])}{Style.RESET_ALL}{' ' * (width - len(' ▲ Open:  ') - len(format_price(price_data['open'][0])) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} ⬆ High:  {Fore.GREEN}{format_price(price_data['high'][0])}{Style.RESET_ALL}{' ' * (width - len(' ⬆ High:  ') - len(format_price(price_data['high'][0])) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} ⬇ Low:   {Fore.RED}{format_price(price_data['low'][0])}{Style.RESET_ALL}{' ' * (width - len(' ⬇ Low:   ') - len(format_price(price_data['low'][0])) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL} ◆ Close: {Fore.YELLOW}{format_price(price_data['close'][0])}{Style.RESET_ALL}{' ' * (width - len(' ◆ Close: ') - len(format_price(price_data['close'][0])) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Add change information with arrows
    change_color = Fore.GREEN if price_change >= 0 else Fore.RED
    change_symbol = "🡅" if price_change >= 0 else "🡇"
    change_line = f" {change_symbol} Change: {change_color}{abs(price_change):.2f} ({price_change_pct:.2f}%){Style.RESET_ALL}"
    lines.append(f"{Fore.CYAN}│{Style.RESET_ALL}{change_line}{' ' * (width - len(change_line) - 1)}{Fore.CYAN}│{Style.RESET_ALL}")
    
    lines.append(f"{Fore.CYAN}{bottom}{Style.RESET_ALL}")
    
    return "\n".join(lines)

def fetch_and_display_stock_data(symbol):
    """Fetch and display stock data for a given symbol."""
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": API_KEY,
        "datatype": "json"
    }

    try:
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        click.echo(f"{Fore.RED}⚠ Error fetching data: {e}{Style.RESET_ALL}")
        return
    except ValueError:
        click.echo(f"{Fore.RED}⚠ Error parsing response data{Style.RESET_ALL}")
        return

    time_series_key = "Time Series (5min)"
    if time_series_key not in data:
        click.echo(f"{Fore.RED}⚠ Error: {data.get('Note', 'Unknown error')}{Style.RESET_ALL}")
        return

    # Extract multiple price points
    time_series = data[time_series_key]
    timestamps = list(time_series.keys())[:15]  # Use the last 15 intervals
    
    price_data = {
        'open': [float(time_series[ts]["1. open"]) for ts in timestamps],
        'high': [float(time_series[ts]["2. high"]) for ts in timestamps],
        'low': [float(time_series[ts]["3. low"]) for ts in timestamps],
        'close': [float(time_series[ts]["4. close"]) for ts in timestamps]
    }

    # Clear screen (cross-platform)
    click.clear()

    # Calculate price changes
    price_change = price_data['close'][0] - price_data['open'][0]
    price_change_pct = (price_change / price_data['open'][0]) * 100

    # Display decorated summary box
    click.echo("\n" + format_summary_box(symbol, timestamps[0], price_data, price_change, price_change_pct))
    
    # Generate and display enhanced graph
    click.echo("\n" + generate_multi_series_ascii_graph(price_data, timestamps))
    
    # Display help text with decorative elements
    click.echo(f"\n{Fore.CYAN}╭─ Commands ─╮{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}│{Style.RESET_ALL} ⌨  Enter a new stock symbol to view different stock")
    click.echo(f"{Fore.CYAN}│{Style.RESET_ALL} ⌃D Press Ctrl+D to exit")
    click.echo(f"{Fore.CYAN}╰──────────╯{Style.RESET_ALL}")

def main():
    """Main loop for the stock monitoring CLI."""
    title = "✧ Stock Market Monitor CLI ✧"
    border_width = len(title) + 4
    top, _, bottom = create_border(border_width)
    
    click.echo(f"\n{Fore.CYAN}{top}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}│{Style.RESET_ALL} {title} {Fore.CYAN}│{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{bottom}{Style.RESET_ALL}")
    click.echo("\n⌨  Enter a stock symbol to begin (Ctrl+D to exit)")
    
    while True:
        try:
            symbol = click.prompt('⮞ Stock Symbol', type=str).strip().upper()
            if symbol:
                fetch_and_display_stock_data(symbol)
        except click.exceptions.Abort:
            click.echo("\n👋 Goodbye!")
            break
        except Exception as e:
            click.echo(f"{Fore.RED}⚠ An error occurred: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
