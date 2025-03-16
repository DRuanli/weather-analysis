# Advanced Weather Forecast Application

A professional weather application built with Python and Tkinter that provides current weather conditions, 5-day forecasts, and data visualization.

## Features

- **Current Weather Data**: Temperature, humidity, wind speed, pressure, and more
- **5-Day Forecast**: Daily weather predictions with icons and details
- **Data Visualization**: Interactive charts for temperature, humidity, pressure, and wind speed trends
- **Multiple Units**: Support for both metric (°C) and imperial (°F) units
- **Favorites System**: Save and manage your favorite cities
- **Search History**: Quick access to previously searched locations
- **Current Location**: Detect your location automatically
- **Dark/Light Theme**: Choose your preferred visual style
- **Customizable Colors**: Personalize your application appearance
- **Data Export**: Export weather data in JSON or CSV format
- **Auto-Refresh**: Keep weather data up-to-date automatically

## Screenshots

*Weather information display with current conditions and forecast*

*Interactive weather trend charts*

*Settings panel for customization*

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Required Libraries

```bash
pip install requests pillow matplotlib
```

### Setup

1. Clone the repository or download the source code:

```bash
git clone https://github.com/yourusername/weather-forecast.git
cd weather-forecast
```

2. Run the application:

```bash
python main.py
```

## API Key Setup

This application requires an API key from OpenWeatherMap to fetch weather data:

1. Go to [OpenWeatherMap](https://openweathermap.org/) and create a free account
2. Navigate to the API Keys section in your account
3. Copy your API key
4. Enter the API key in the application's Settings tab
5. Click "Save Key" to store it for future use

**Note**: The free tier of OpenWeatherMap allows up to 1,000 API calls per day, which is more than enough for personal use.

## Usage Guide

### Searching for Weather

1. Enter a city name in the search field
2. Click the "Search" button or press Enter
3. View current weather conditions in the "Current Weather" tab
4. Check the 5-day forecast in the "Forecast" tab
5. Explore weather trends in the "Charts & Trends" tab

### Managing Favorites

1. Search for a city
2. Click "Add to Favorites" to save it
3. Access your favorites through the Favorites dropdown
4. Manage your favorites list in Edit → Manage Favorites

### Customizing the Application

1. Change temperature units in the Settings tab
2. Switch between Light and Dark themes in View → Theme
3. Customize colors in View → Customize Colors
4. Set up auto-refresh in the Settings tab

### Exporting Data

1. Search for a city to load its weather data
2. Go to File → Export Weather Data
3. Choose between JSON or CSV format
4. Select a location to save the file

## Configuration

The application stores its configuration in a `weather_config.json` file in the application directory. This includes:

- API key
- Temperature units
- Theme preference
- Favorite cities
- Search history
- Auto-refresh settings
- Custom colors

## File Structure

```
weather-forecast/
├── main.py              # Main application file
├── weather_config.json  # Configuration storage
├── weather_app.log      # Application logs
└── README.md            # This file
```

## Troubleshooting

### Common Issues

1. **"API Key Required" Error**
   - Make sure you've entered a valid OpenWeatherMap API key in the Settings tab
   - Test your API key with the "Test API Key" button

2. **City Not Found**
   - Check for spelling errors in the city name
   - Try adding the country code (e.g., "London,UK")

3. **Connection Error**
   - Check your internet connection
   - Verify that OpenWeatherMap services are online

4. **Display Issues**
   - Try switching between themes
   - Restart the application

### Viewing Logs

For more detailed error information, you can view the application logs:

1. Go to Help → View Logs
2. Check the log entries for error messages

## Development Notes

The application is built using:

- **Tkinter**: For the graphical user interface
- **Requests**: For API communication
- **Matplotlib**: For data visualization
- **PIL/Pillow**: For image processing
- **Threading**: For non-blocking API calls

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Weather data provided by [OpenWeatherMap](https://openweathermap.org/)
- Weather icons by OpenWeatherMap
- Geolocation services by [ipapi](https://ipapi.co/)