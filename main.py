import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime
import threading
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import csv
matplotlib.use("TkAgg")

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Weather Forecast")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Setup logging
        logging.basicConfig(filename='weather_app.log', level=logging.INFO,
                           format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Config
        self.config_file = "weather_config.json"
        self.config = self.load_config()
        self.api_key = self.config.get('api_key', '')
        self.units = tk.StringVar(value=self.config.get('units', 'metric'))
        self.theme = tk.StringVar(value=self.config.get('theme', 'light'))
        self.current_city = tk.StringVar()
        self.favorite_cities = self.config.get('favorite_cities', [])
        self.search_history = self.config.get('search_history', [])
        
        # API selection
        self.available_apis = {
            'openweathermap': {
                'name': 'OpenWeatherMap',
                'current_url': 'http://api.openweathermap.org/data/2.5/weather',
                'forecast_url': 'http://api.openweathermap.org/data/2.5/forecast',
                'icon_url': 'http://openweathermap.org/img/wn/{icon}@2x.png'
            }
        }
        self.active_api = tk.StringVar(value=self.config.get('active_api', 'openweathermap'))
        
        # Data containers
        self.current_weather = None
        self.forecast_data = None
        self.weather_icons = {}
        
        # Apply theme before creating widgets
        self.apply_theme()
        
        # Create main UI
        self.create_widgets()
        
        # Show API key prompt if no API key is set
        if not self.api_key:
            self.show_api_key_prompt()
        else:
            # Check for saved city to load on startup
            last_city = self.config.get('last_city', '')
            if last_city:
                self.city_entry.insert(0, last_city)
                self.current_city.set(last_city)
                self.get_weather()
    
    # MISSING METHOD: Export Weather Data
    def export_weather_data(self):
        """Export current weather data to file"""
        if not self.current_weather:
            messagebox.showinfo("Export", "No weather data to export")
            return
        
        city = self.current_city.get()
        default_filename = f"weather_data_{city}_{datetime.now().strftime('%Y%m%d')}"
        
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.json'):
                with open(filename, 'w') as f:
                    json.dump({
                        'current': self.current_weather,
                        'forecast': self.forecast_data
                    }, f, indent=2)
            elif filename.endswith('.csv'):
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write current weather data
                    writer.writerow(['City', 'Date', 'Temperature', 'Feels Like', 
                                     'Description', 'Humidity', 'Pressure', 'Wind Speed'])
                    
                    if self.active_api.get() == 'openweathermap':
                        dt = datetime.fromtimestamp(self.current_weather['dt'])
                        writer.writerow([
                            f"{self.current_weather['name']}, {self.current_weather['sys']['country']}",
                            dt.strftime('%Y-%m-%d %H:%M'),
                            self.current_weather['main']['temp'],
                            self.current_weather['main']['feels_like'],
                            self.current_weather['weather'][0]['description'],
                            self.current_weather['main']['humidity'],
                            self.current_weather['main']['pressure'],
                            self.current_weather['wind']['speed']
                        ])
                        
                        # Write forecast data
                        writer.writerow([])
                        writer.writerow(['Forecast'])
                        writer.writerow(['Date', 'Temperature', 'Min Temp', 'Max Temp', 
                                        'Description', 'Humidity', 'Wind Speed'])
                        
                        for item in self.forecast_data['list']:
                            dt = datetime.fromtimestamp(item['dt'])
                            writer.writerow([
                                dt.strftime('%Y-%m-%d %H:%M'),
                                item['main']['temp'],
                                item['main']['temp_min'],
                                item['main']['temp_max'],
                                item['weather'][0]['description'],
                                item['main']['humidity'],
                                item['wind']['speed']
                            ])
            
            messagebox.showinfo("Export", f"Weather data exported to {filename}")
            
        except Exception as e:
            logging.error(f"Error exporting data: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    # MISSING METHOD: Clear History
    def clear_history(self):
        """Clear search history"""
        confirm = messagebox.askyesno("Confirm", "Clear search history?")
        if confirm:
            self.search_history = []
            self.city_entry['values'] = []
            self.save_config()
            messagebox.showinfo("History", "Search history cleared")
    
    # MISSING METHOD: Manage Favorites
    def manage_favorites(self):
        """Open dialog to manage favorite cities"""
        fav_window = tk.Toplevel(self.root)
        fav_window.title("Manage Favorites")
        fav_window.geometry("300x400")
        fav_window.transient(self.root)
        fav_window.grab_set()
        
        ttk.Label(fav_window, text="Your Favorite Cities").pack(pady=10)
        
        # Listbox with scrollbar
        frame = ttk.Frame(fav_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        fav_listbox = tk.Listbox(frame)
        fav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        fav_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=fav_listbox.yview)
        
        # Populate listbox
        for city in self.favorite_cities:
            fav_listbox.insert(tk.END, city)
        
        # Buttons frame
        button_frame = ttk.Frame(fav_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def remove_selected():
            selected = fav_listbox.curselection()
            if not selected:
                messagebox.showinfo("Selection", "Please select a city to remove")
                return
                
            city = fav_listbox.get(selected)
            confirm = messagebox.askyesno("Confirm", f"Remove {city} from favorites?")
            if confirm:
                self.favorite_cities.remove(city)
                fav_listbox.delete(selected)
                self.save_config()
                self.update_favorite_button()
        
        def use_selected():
            selected = fav_listbox.curselection()
            if not selected:
                messagebox.showinfo("Selection", "Please select a city")
                return
                
            city = fav_listbox.get(selected)
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, city)
            self.current_city.set(city)
            fav_window.destroy()
            self.get_weather()
        
        ttk.Button(button_frame, text="Remove Selected", 
                  command=remove_selected).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Use Selected", 
                  command=use_selected).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Close", 
                  command=fav_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    # MISSING METHOD: Customize Colors
    def customize_colors(self):
        """Open dialog to customize theme colors"""
        color_window = tk.Toplevel(self.root)
        color_window.title("Customize Colors")
        color_window.geometry("400x300")
        color_window.transient(self.root)
        color_window.grab_set()
        
        ttk.Label(color_window, text="Select theme to customize:").pack(padx=10, pady=5)
        
        theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(color_window, text="Light Theme", 
                       variable=theme_var, value="light").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(color_window, text="Dark Theme", 
                       variable=theme_var, value="dark").pack(anchor=tk.W, padx=20)
        
        ttk.Label(color_window, text="Select element to change:").pack(padx=10, pady=5)
        
        elements = [
            ("Background", "bg_color"),
            ("Text", "fg_color"),
            ("Accent", "accent_color"),
            ("Highlight", "highlight_color")
        ]
        
        element_var = tk.StringVar(value="bg_color")
        for text, value in elements:
            ttk.Radiobutton(color_window, text=text, 
                           variable=element_var, value=value).pack(anchor=tk.W, padx=20)
        
        def pick_color():
            initial_color = getattr(self, element_var.get())
            color = tk.colorchooser.askcolor(initial_color)[1]
            if color:
                # Store in custom colors config
                theme_key = theme_var.get()
                element_key = element_var.get()
                
                if 'custom_colors' not in self.config:
                    self.config['custom_colors'] = {}
                if theme_key not in self.config['custom_colors']:
                    self.config['custom_colors'][theme_key] = {}
                
                self.config['custom_colors'][theme_key][element_key] = color
                
                # Apply immediately if current theme
                if theme_key == self.theme.get():
                    setattr(self, element_key, color)
                    self.apply_theme()
                
                # Save config
                self.save_config()
        
        ttk.Button(color_window, text="Choose Color", 
                  command=pick_color).pack(pady=10)
        
        ttk.Button(color_window, text="Reset to Default", 
                  command=self.reset_colors).pack(pady=5)
        
        ttk.Button(color_window, text="Close", 
                  command=color_window.destroy).pack(pady=10)
    
    # MISSING METHOD: Reset Colors
    def reset_colors(self):
        """Reset colors to default"""
        if 'custom_colors' in self.config:
            del self.config['custom_colors']
            self.save_config()
            self.apply_theme()
            messagebox.showinfo("Colors", "Colors reset to default")
    
    # MISSING METHOD: Change Theme
    def change_theme(self):
        """Change application theme"""
        self.apply_theme()
        
        # Force redraw of all tabs
        self.notebook.update_idletasks()
        
        # Update chart if it exists
        if hasattr(self, 'chart_type'):
            self.update_chart()
        
        # Update config
        self.config['theme'] = self.theme.get()
        self.save_config()
    
    # MISSING METHOD: On API Change
    def on_api_change(self, event):
        """Handle API provider change"""
        # Map combobox displayed text back to actual API key
        selected_name = event.widget.get()
        for key, api in self.available_apis.items():
            if api['name'] == selected_name:
                self.active_api.set(key)
                break
    
    # MISSING METHOD: View Logs
    def view_logs(self):
        """View application logs"""
        try:
            log_window = tk.Toplevel(self.root)
            log_window.title("Application Logs")
            log_window.geometry("700x500")
            log_window.transient(self.root)
            
            log_text = tk.Text(log_window, wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(log_text)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            log_text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=log_text.yview)
            
            with open('weather_app.log', 'r') as f:
                logs = f.read()
                log_text.insert(tk.END, logs)
            
            log_text.config(state=tk.DISABLED)
            
            button_frame = ttk.Frame(log_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Refresh", 
                      command=lambda: self.refresh_logs(log_text)).pack(side=tk.LEFT)
            
            ttk.Button(button_frame, text="Clear Logs", 
                      command=lambda: self.clear_logs(log_text)).pack(side=tk.LEFT, padx=10)
            
            ttk.Button(button_frame, text="Close", 
                      command=log_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {str(e)}")
    
    # MISSING METHOD: Refresh Logs
    def refresh_logs(self, log_text):
        """Refresh log display"""
        try:
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            
            with open('weather_app.log', 'r') as f:
                logs = f.read()
                log_text.insert(tk.END, logs)
            
            log_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Could not refresh logs: {str(e)}")
    
    # MISSING METHOD: Clear Logs
    def clear_logs(self, log_text):
        """Clear log file"""
        confirm = messagebox.askyesno("Confirm", "Clear all logs?")
        if confirm:
            try:
                with open('weather_app.log', 'w') as f:
                    f.write("Logs cleared on " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
                
                self.refresh_logs(log_text)
                messagebox.showinfo("Logs", "Log file cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear logs: {str(e)}")
    
    # MISSING METHOD: Show About
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                          "Advanced Weather Forecast v2.0\n\n"
                          "A professional weather application with support for\n"
                          "multiple weather APIs, data visualization, and customization.\n\n"
                          "© 2025 Weather App Team")
    
    # The rest of your methods go here as they were in your previous code
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'api_key': '',
            'units': 'metric',
            'theme': 'light',
            'favorite_cities': [],
            'search_history': [],
            'active_api': 'openweathermap',
            'auto_refresh': False,
            'refresh_interval': 30,
            'custom_colors': {}
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logging.error(f"Error loading config: {str(e)}")
                return default_config
        return default_config
    
    def save_config(self):
        """Save current configuration"""
        try:
            self.config['api_key'] = self.api_key
            self.config['units'] = self.units.get()
            self.config['theme'] = self.theme.get()
            self.config['favorite_cities'] = self.favorite_cities
            self.config['search_history'] = self.search_history[-20:]  # Keep last 20
            self.config['active_api'] = self.active_api.get()
            self.config['last_city'] = self.current_city.get()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
            messagebox.showerror("Error", f"Could not save configuration: {str(e)}")
    
    def show_api_key_prompt(self):
        """Show prompt to enter API key"""
        # Switch to settings tab
        self.notebook.select(self.settings_tab)
        
        # Create a popup to guide the user
        api_prompt = tk.Toplevel(self.root)
        api_prompt.title("API Key Required")
        api_prompt.geometry("500x350")
        api_prompt.transient(self.root)
        api_prompt.grab_set()
        
        ttk.Label(api_prompt, text="API Key Required", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        ttk.Label(api_prompt, text="This weather app requires an API key from OpenWeatherMap.", 
                 wraplength=450).pack(padx=20, pady=5)
        
        ttk.Label(api_prompt, text="How to get a FREE API key:", 
                 font=("Arial", 12, "bold")).pack(padx=20, pady=5, anchor=tk.W)
        
        steps = [
            "1. Go to https://openweathermap.org/",
            "2. Click 'Sign Up' and create a free account",
            "3. After signing in, go to 'API Keys' tab in your account",
            "4. Copy your API key (or create a new one)"
        ]
        
        for step in steps:
            ttk.Label(api_prompt, text=step, wraplength=450).pack(padx=30, pady=2, anchor=tk.W)
        
        ttk.Label(api_prompt, text="Then enter your API key in the settings tab.", 
                 wraplength=450).pack(padx=20, pady=10)
        
        # API Key entry
        key_frame = ttk.Frame(api_prompt)
        key_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        key_entry = ttk.Entry(key_frame, width=40)
        key_entry.pack(side=tk.LEFT, padx=5)
        
        def save_key_from_prompt():
            key = key_entry.get().strip()
            if key:
                self.api_key = key
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, key)
                self.save_config()
                api_prompt.destroy()
                messagebox.showinfo("API Key", "API key saved successfully! You can now search for weather.")
            else:
                messagebox.showerror("Error", "Please enter a valid API key")
        
        ttk.Button(api_prompt, text="Save API Key", 
                  command=save_key_from_prompt).pack(pady=10)
        
        ttk.Label(api_prompt, text="Note: The basic OpenWeatherMap plan is free and allows 1,000 API calls per day.", 
                 wraplength=450, font=("Arial", 9, "italic")).pack(padx=20, pady=10)
    
    def apply_theme(self):
        """Apply the selected theme"""
        if self.theme.get() == 'dark':
            self.bg_color = '#2E2E2E'
            self.fg_color = '#FFFFFF'
            self.accent_color = '#007ACC'
            self.highlight_color = '#3C3C3C'
            
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure ttk styles for dark theme
            style.configure('TFrame', background=self.bg_color)
            style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
            style.configure('TButton', background=self.accent_color, foreground=self.fg_color)
            style.configure('TNotebook', background=self.bg_color, tabmargins=[2, 5, 2, 0])
            style.configure('TNotebook.Tab', background=self.highlight_color, 
                           foreground=self.fg_color, padding=[10, 2])
            style.map('TNotebook.Tab', background=[('selected', self.accent_color)])
            
            # Configure root window
            self.root.configure(bg=self.bg_color)
            
            # Custom colors from config
            custom_colors = self.config.get('custom_colors', {}).get('dark', {})
            for widget, color in custom_colors.items():
                try:
                    style.configure(widget, background=color)
                except:
                    pass
        else:  # Light theme
            self.bg_color = '#F0F0F0'
            self.fg_color = '#000000'
            self.accent_color = '#0078D7'
            self.highlight_color = '#E5E5E5'
            
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure ttk styles for light theme
            style.configure('TFrame', background=self.bg_color)
            style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
            style.configure('TButton', background=self.accent_color, foreground='white')
            style.configure('TNotebook', background=self.bg_color)
            style.configure('TNotebook.Tab', background=self.highlight_color, 
                           foreground=self.fg_color, padding=[10, 2])
            style.map('TNotebook.Tab', background=[('selected', self.accent_color)],
                      foreground=[('selected', 'white')])
            
            # Configure root window
            self.root.configure(bg=self.bg_color)
            
            # Custom colors from config
            custom_colors = self.config.get('custom_colors', {}).get('light', {})
            for widget, color in custom_colors.items():
                try:
                    style.configure(widget, background=color)
                except:
                    pass
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Create main menu
        self.create_menu()
        
        # Create main notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.current_weather_tab = ttk.Frame(self.notebook)
        self.forecast_tab = ttk.Frame(self.notebook)
        self.charts_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.current_weather_tab, text="Current Weather")
        self.notebook.add(self.forecast_tab, text="5-Day Forecast")
        self.notebook.add(self.charts_tab, text="Charts & Trends")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Set up each tab
        self.setup_current_weather_tab()
        self.setup_forecast_tab()
        self.setup_charts_tab()
        self.setup_settings_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set up auto-refresh if enabled
        if self.config.get('auto_refresh', False):
            self.setup_auto_refresh()
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_command(label="Export Weather Data", command=self.export_weather_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Clear History", command=self.clear_history)
        edit_menu.add_command(label="Manage Favorites", command=self.manage_favorites)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_radiobutton(label="Light Theme", variable=self.theme, value="light", 
                                  command=self.change_theme)
        theme_menu.add_radiobutton(label="Dark Theme", variable=self.theme, value="dark", 
                                  command=self.change_theme)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        view_menu.add_command(label="Customize Colors", command=self.customize_colors)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="View Logs", command=self.view_logs)
        help_menu.add_command(label="Get API Key Help", command=self.show_api_key_help)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def show_api_key_help(self):
        """Show help for getting an API key"""
        self.show_api_key_prompt()
    
    # Include rest of your methods...
    # ... (copy from your previous code)

    # Add other required methods
    def fetch_weather_data(self, city, api_key, api_info):
        """Fetch weather data from API in a separate thread"""
        try:
            # Current weather
            if self.active_api.get() == 'openweathermap':
                params = {
                    "q": city,
                    "appid": api_key,
                    "units": self.units.get()
                }
            
            current_response = requests.get(api_info['current_url'], params=params, timeout=10)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Forecast data
            forecast_response = requests.get(api_info['forecast_url'], params=params, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Process and display data in the main thread
            self.root.after(0, lambda: self.process_weather_data(current_data, forecast_data))
            
            # Update status
            self.root.after(0, lambda: self.status_bar.config(
                text=f"Weather data for {city} updated at {datetime.now().strftime('%H:%M:%S')}"))
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {str(e)}")
            self.root.after(0, lambda: self.handle_api_error(str(e)))
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {str(e)}")
            self.root.after(0, lambda: self.handle_api_error("Invalid data received from API"))
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self.root.after(0, lambda: self.handle_api_error(f"Unexpected error: {str(e)}"))

    def process_weather_data(self, current_data, forecast_data):
        """Process and display weather data"""
        # Store the data
        self.current_weather = current_data
        self.forecast_data = forecast_data
        
        # Update UI based on which API we're using
        if self.active_api.get() == 'openweathermap':
            self.process_openweathermap_data(current_data, forecast_data)
        
        # Update the chart
        self.update_chart()
        
        # Save city to config
        self.config['last_city'] = self.current_city.get()
        self.save_config()
        
        # Update favorite button
        self.update_favorite_button()

    def process_openweathermap_data(self, current_data, forecast_data):
        """Process OpenWeatherMap API data"""
        # Current weather tab
        city_name = f"{current_data['name']}, {current_data['sys']['country']}"
        self.city_label.config(text=city_name)
        self.date_label.config(
            text=f"As of {datetime.fromtimestamp(current_data['dt']).strftime('%Y-%m-%d %H:%M')}")
        
        # Temperature and description
        unit_symbol = "°C" if self.units.get() == "metric" else "°F"
        self.temp_label.config(text=f"{current_data['main']['temp']:.1f}{unit_symbol}")
        self.desc_label.config(text=current_data['weather'][0]['description'].capitalize())
        
        # Load weather icon
        icon_code = current_data['weather'][0]['icon']
        self.load_weather_icon(icon_code, self.weather_icon)
        
        # Basic info
        self.basic_info_labels["feels_like"].config(
            text=f"{current_data['main']['feels_like']:.1f}{unit_symbol}")
        self.basic_info_labels["humidity"].config(text=f"{current_data['main']['humidity']}%")
        
        wind_unit = "m/s" if self.units.get() == "metric" else "mph"
        self.basic_info_labels["wind"].config(
            text=f"{current_data['wind']['speed']} {wind_unit}")
        
        self.basic_info_labels["pressure"].config(
            text=f"{current_data['main']['pressure']} hPa")
        
        # Detailed info
        self.detail_labels["min_temp"].config(
            text=f"{current_data['main']['temp_min']:.1f}{unit_symbol}")
        self.detail_labels["max_temp"].config(
            text=f"{current_data['main']['temp_max']:.1f}{unit_symbol}")
        
        # Convert sunrise/sunset timestamps
        sunrise = datetime.fromtimestamp(current_data['sys']['sunrise'])
        sunset = datetime.fromtimestamp(current_data['sys']['sunset'])
        
        self.detail_labels["sunrise"].config(text=sunrise.strftime('%H:%M'))
        self.detail_labels["sunset"].config(text=sunset.strftime('%H:%M'))
        
        # Visibility
        visibility_km = current_data.get('visibility', 0) / 1000
        self.detail_labels["visibility"].config(
            text=f"{visibility_km:.1f} km")
        
        # Wind direction
        wind_direction = self.get_wind_direction(current_data['wind'].get('deg', 0))
        self.detail_labels["wind_direction"].config(text=wind_direction)
        
        # Cloud coverage
        self.detail_labels["clouds"].config(
            text=f"{current_data['clouds']['all']}%")
        
        # UV Index if available
        self.detail_labels["uv_index"].config(text="N/A")  # API doesn't provide this
        
        # Update forecast tab
        self.forecast_city_label.config(text=f"5-Day Forecast for {city_name}")
        
        # Process forecast data
        forecast_list = forecast_data['list']
        day_forecasts = {}
        
        # Group by day
        for item in forecast_list:
            dt = datetime.fromtimestamp(item['dt'])
            day = dt.strftime('%Y-%m-%d')
            
            # Take noon forecast for each day if available
            if day not in day_forecasts or abs(dt.hour - 12) < abs(datetime.fromtimestamp(day_forecasts[day]['dt']).hour - 12):
                day_forecasts[day] = item
        
        # Clear previous forecast cards
        for widget in self.forecast_container.winfo_children():
            widget.destroy()
        
        # Create new forecast cards
        sorted_days = sorted(day_forecasts.keys())[:5]  # Limit to 5 days
        
        for i, day in enumerate(sorted_days):
            forecast = day_forecasts[day]
            dt = datetime.fromtimestamp(forecast['dt'])
            
            card = ttk.LabelFrame(self.forecast_container, text=dt.strftime('%A'))
            card.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
            
            # Date
            ttk.Label(card, text=dt.strftime('%b %d')).pack(padx=5, pady=2)
            
            # Icon
            icon_label = ttk.Label(card)
            icon_label.pack(padx=5, pady=2)
            self.load_weather_icon(forecast['weather'][0]['icon'], icon_label)
            
            # Temp min/max
            temp_text = f"{forecast['main']['temp_max']:.1f}{unit_symbol} / {forecast['main']['temp_min']:.1f}{unit_symbol}"
            ttk.Label(card, text=temp_text).pack(padx=5, pady=2)
            
            # Description
            ttk.Label(card, text=forecast['weather'][0]['description'].capitalize()).pack(padx=5, pady=2)
            
            # Additional info
            ttk.Label(card, text=f"Humidity: {forecast['main']['humidity']}%").pack(padx=5, pady=2)
            ttk.Label(card, text=f"Wind: {forecast['wind']['speed']} {wind_unit}").pack(padx=5, pady=2)
        
        # Update charts tab
        self.charts_city_label.config(text=f"Weather Trends for {city_name}")

    def load_weather_icon(self, icon_code, label_widget):
        """Load weather icon from API and display"""
        try:
            api_info = self.available_apis.get(self.active_api.get())
            icon_url = api_info['icon_url'].format(icon=icon_code)
            
            if icon_code in self.weather_icons:
                # Use cached icon
                label_widget.config(image=self.weather_icons[icon_code])
            else:
                # Fetch new icon
                response = requests.get(icon_url, timeout=5)
                response.raise_for_status()
                
                image = Image.open(BytesIO(response.content))
                tk_image = ImageTk.PhotoImage(image)
                
                # Cache the icon
                self.weather_icons[icon_code] = tk_image
                
                # Display icon
                label_widget.config(image=tk_image)
        except Exception as e:
            logging.error(f"Error loading weather icon: {str(e)}")
            label_widget.config(image=None, text="[Icon]")

    def get_wind_direction(self, degrees):
        """Convert wind direction degrees to cardinal direction"""
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def update_chart(self):
        """Update the weather chart based on selected type"""
        if not self.forecast_data:
            return
        
        # Clear previous chart
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # Get chart type
        chart_type = self.chart_type.get()
        
        # Create new figure
        fig, ax = plt.subplots(figsize=(10, 6), dpi=80)
        
        # Process data based on API
        if self.active_api.get() == 'openweathermap':
            # Extract data points
            dates = []
            values = []
            
            for item in self.forecast_data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                dates.append(dt)
                
                if chart_type == 'temperature':
                    values.append(item['main']['temp'])
                    y_label = 'Temperature (°C)' if self.units.get() == 'metric' else 'Temperature (°F)'
                    title = 'Temperature Forecast'
                elif chart_type == 'humidity':
                    values.append(item['main']['humidity'])
                    y_label = 'Humidity (%)'
                    title = 'Humidity Forecast'
                elif chart_type == 'pressure':
                    values.append(item['main']['pressure'])
                    y_label = 'Pressure (hPa)'
                    title = 'Pressure Forecast'
                elif chart_type == 'wind_speed':
                    values.append(item['wind']['speed'])
                    y_label = 'Wind Speed (m/s)' if self.units.get() == 'metric' else 'Wind Speed (mph)'
                    title = 'Wind Speed Forecast'
            
            # Plot data
            ax.plot(dates, values, marker='o', linestyle='-', color=self.accent_color)
            
            # Configure plot
            ax.set_title(title)
            ax.set_xlabel('Date')
            ax.set_ylabel(y_label)
            
            # Format x-axis to show readable dates
            fig.autofmt_xdate()
            
            # Apply theme colors
            if self.theme.get() == 'dark':
                fig.patch.set_facecolor(self.bg_color)
                ax.set_facecolor(self.highlight_color)
                ax.tick_params(colors=self.fg_color)
                ax.xaxis.label.set_color(self.fg_color)
                ax.yaxis.label.set_color(self.fg_color)
                ax.title.set_color(self.fg_color)
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_empty_chart(self):
        """Create an empty chart with a message"""
        fig, ax = plt.subplots(figsize=(10, 6), dpi=80)
        ax.text(0.5, 0.5, 'Search for a city to view weather charts', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=14)
        ax.set_axis_off()
        
        # Apply theme colors
        if self.theme.get() == 'dark':
            fig.patch.set_facecolor(self.bg_color)
            ax.set_facecolor(self.bg_color)
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def toggle_favorite(self):
        """Add or remove current city from favorites"""
        city = self.current_city.get()
        if not city:
            return
        
        if city in self.favorite_cities:
            self.favorite_cities.remove(city)
            messagebox.showinfo("Favorites", f"{city} removed from favorites")
        else:
            self.favorite_cities.append(city)
            messagebox.showinfo("Favorites", f"{city} added to favorites")
        
        self.update_favorite_button()
        self.save_config()

    def update_favorite_button(self):
        """Update favorite button state based on current city"""
        city = self.current_city.get()
        if city in self.favorite_cities:
            self.fav_btn.config(text="♥ Remove from Favorites")
        else:
            self.fav_btn.config(text="♡ Add to Favorites")

    def get_location(self):
        """Get user's current location using IP geolocation"""
        try:
            self.status_bar.config(text="Detecting location...")
            self.root.update_idletasks()
            
            # Call IP geolocation API
            response = requests.get("https://ipapi.co/json/", timeout=5)
            response.raise_for_status()
            location_data = response.json()
            
            city = location_data.get('city')
            if city:
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, city)
                self.current_city.set(city)
                self.get_weather()
            else:
                raise Exception("Could not determine city from IP address")
            
        except Exception as e:
            logging.error(f"Error detecting location: {str(e)}")
            messagebox.showerror("Location Error", 
                               f"Could not detect your location: {str(e)}")
            self.status_bar.config(text="Ready")

    def handle_api_error(self, error_message):
        """Handle API errors"""
        messagebox.showerror("API Error", error_message)
        self.status_bar.config(text=f"Error: {error_message}")

    def toggle_auto_refresh(self):
        """Toggle auto-refresh feature"""
        if self.auto_refresh_var.get():
            try:
                # Validate interval
                interval = int(self.refresh_interval.get())
                if interval < 5:
                    messagebox.showinfo("Auto-refresh", "Minimum refresh interval is 5 minutes")
                    self.refresh_interval.set("5")
                    interval = 5
                
                self.config['auto_refresh'] = True
                self.config['refresh_interval'] = interval
                self.save_config()
                
                self.setup_auto_refresh()
                messagebox.showinfo("Auto-refresh", 
                                  f"Weather will refresh every {interval} minutes")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for refresh interval")
                self.auto_refresh_var.set(False)
        else:
            self.config['auto_refresh'] = False
            self.save_config()
            messagebox.showinfo("Auto-refresh", "Auto-refresh disabled")

    def setup_auto_refresh(self):
        """Set up auto-refresh timer"""
        if hasattr(self, 'refresh_timer_id'):
            self.root.after_cancel(self.refresh_timer_id)
        
        if self.auto_refresh_var.get() and self.current_city.get():
            interval_ms = int(self.refresh_interval.get()) * 60 * 1000
            self.refresh_timer_id = self.root.after(interval_ms, self.auto_refresh)

    def auto_refresh(self):
        """Auto-refresh weather data"""
        if self.current_city.get():
            self.get_weather()
        
        # Schedule next refresh
        self.setup_auto_refresh()

    def setup_current_weather_tab(self):
        """Set up the current weather tab UI"""
        # Search frame at top
        search_frame = ttk.Frame(self.current_weather_tab)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # City entry with autocomplete
        ttk.Label(search_frame, text="City:").grid(row=0, column=0, padx=5, pady=5)
        self.city_entry = ttk.Combobox(search_frame, width=25, textvariable=self.current_city)
        self.city_entry.grid(row=0, column=1, padx=5, pady=5)
        self.city_entry['values'] = self.search_history
        
        # Search button
        search_btn = ttk.Button(search_frame, text="Search", command=self.get_weather)
        search_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Location button (get current location)
        location_btn = ttk.Button(search_frame, text="Current Location", 
                                 command=self.get_location)
        location_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Favorite toggle button
        self.fav_btn = ttk.Button(search_frame, text="♡ Add to Favorites", 
                                 command=self.toggle_favorite)
        self.fav_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # API key status indicator
        if not self.api_key:
            api_warning = ttk.Label(self.current_weather_tab, 
                                  text="⚠️ API Key Required - Go to Settings Tab", 
                                  foreground="red")
            api_warning.pack(fill=tk.X, padx=10, pady=5)
            
            settings_btn = ttk.Button(self.current_weather_tab, text="Go to Settings", 
                                    command=lambda: self.notebook.select(self.settings_tab))
            settings_btn.pack(pady=5)
        
        # Main container for weather info
        self.weather_container = ttk.Frame(self.current_weather_tab)
        self.weather_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Current weather frame
        self.current_weather_frame = ttk.LabelFrame(self.weather_container, text="Current Weather")
        self.current_weather_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # City and date frame
        header_frame = ttk.Frame(self.current_weather_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.city_label = ttk.Label(header_frame, text="--", font=("Arial", 18, "bold"))
        self.city_label.grid(row=0, column=0, sticky=tk.W)
        
        self.date_label = ttk.Label(header_frame, text="--", font=("Arial", 12))
        self.date_label.grid(row=1, column=0, sticky=tk.W)
        
        # Weather icon and main info
        main_info_frame = ttk.Frame(self.current_weather_frame)
        main_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side - icon and temp
        icon_temp_frame = ttk.Frame(main_info_frame)
        icon_temp_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.weather_icon = ttk.Label(icon_temp_frame)
        self.weather_icon.grid(row=0, column=0, rowspan=2, padx=10)
        
        self.temp_label = ttk.Label(icon_temp_frame, text="--", font=("Arial", 32))
        self.temp_label.grid(row=0, column=1)
        
        self.desc_label = ttk.Label(icon_temp_frame, text="--", font=("Arial", 14))
        self.desc_label.grid(row=1, column=1)
        
        # Right side - feels like and other basic info
        basic_info_frame = ttk.Frame(main_info_frame)
        basic_info_frame.grid(row=0, column=1, sticky=tk.E, padx=20)
        
        labels = ["Feels Like", "Humidity", "Wind", "Pressure"]
        self.basic_info_labels = {}
        
        for i, label in enumerate(labels):
            ttk.Label(basic_info_frame, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, pady=2)
            self.basic_info_labels[label.lower().replace(" ", "_")] = ttk.Label(
                basic_info_frame, text="--")
            self.basic_info_labels[label.lower().replace(" ", "_")].grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Detailed weather information
        detailed_frame = ttk.LabelFrame(self.current_weather_frame, text="Additional Information")
        detailed_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create grid for detailed info
        details = [
            "Min Temp", "Max Temp", "Sunrise", "Sunset", 
            "Visibility", "Wind Direction", "Clouds", "UV Index"
        ]
        
        self.detail_labels = {}
        for i, detail in enumerate(details):
            row, col = divmod(i, 4)
            ttk.Label(detailed_frame, text=f"{detail}:").grid(
                row=row, column=col*2, sticky=tk.W, padx=5, pady=5)
            self.detail_labels[detail.lower().replace(" ", "_")] = ttk.Label(
                detailed_frame, text="--")
            self.detail_labels[detail.lower().replace(" ", "_")].grid(
                row=row, column=col*2+1, sticky=tk.W, padx=5, pady=5)
        
        # Alert section for weather warnings
        self.alert_frame = ttk.LabelFrame(self.weather_container, text="Weather Alerts")
        self.alert_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.alert_text = tk.Text(self.alert_frame, height=3, wrap=tk.WORD)
        self.alert_text.pack(fill=tk.X, padx=5, pady=5)
        self.alert_text.insert(tk.END, "No weather alerts for this location.")
        self.alert_text.config(state=tk.DISABLED)

    def setup_forecast_tab(self):
        """Set up the forecast tab UI"""
        # Header frame
        header_frame = ttk.Frame(self.forecast_tab)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.forecast_city_label = ttk.Label(header_frame, text="5-Day Forecast for --", 
                                           font=("Arial", 16, "bold"))
        self.forecast_city_label.pack(side=tk.LEFT)
        
        # Container for forecast cards
        self.forecast_container = ttk.Frame(self.forecast_tab)
        self.forecast_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create placeholder for forecast cards
        for i in range(5):
            card = ttk.LabelFrame(self.forecast_container, text=f"Day {i+1}")
            card.grid(row=0, column=i, padx=5, pady=5, sticky=tk.NSEW)
            
            # Date
            ttk.Label(card, text="--").pack(padx=5, pady=2)
            
            # Icon placeholder
            ttk.Label(card, text="[Icon]").pack(padx=5, pady=2)
            
            # Temp
            ttk.Label(card, text="--").pack(padx=5, pady=2)
            
            # Description
            ttk.Label(card, text="--").pack(padx=5, pady=2)
        
        # Configure grid
        for i in range(5):
            self.forecast_container.columnconfigure(i, weight=1)

    def setup_charts_tab(self):
        """Set up the charts tab UI"""
        # Header frame
        header_frame = ttk.Frame(self.charts_tab)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.charts_city_label = ttk.Label(header_frame, text="Weather Trends for --", 
                                          font=("Arial", 16, "bold"))
        self.charts_city_label.pack(side=tk.LEFT)
        
        # Chart selection
        chart_selection_frame = ttk.Frame(self.charts_tab)
        chart_selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(chart_selection_frame, text="Select Chart:").pack(side=tk.LEFT, padx=5)
        
        self.chart_type = tk.StringVar(value="temperature")
        charts = [
            ("Temperature", "temperature"),
            ("Humidity", "humidity"),
            ("Pressure", "pressure"),
            ("Wind Speed", "wind_speed")
        ]
        
        for text, value in charts:
            ttk.Radiobutton(chart_selection_frame, text=text, variable=self.chart_type, 
                           value=value, command=self.update_chart).pack(side=tk.LEFT, padx=10)
        
        # Chart container
        self.chart_container = ttk.Frame(self.charts_tab)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial empty chart
        self.create_empty_chart()

    def setup_settings_tab(self):
        """Set up the settings tab UI"""
        # API Settings section - HIGHLIGHT THIS SECTION for new users
        api_frame = ttk.LabelFrame(self.settings_tab, text="API Settings (Required)")
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add a help label
        ttk.Label(api_frame, 
                 text="You need an API key from OpenWeatherMap to use this app.",
                 wraplength=600).pack(padx=10, pady=5, anchor=tk.W)
        
        api_help_btn = ttk.Button(api_frame, 
                                text="How to get a free API key", 
                                command=self.show_api_key_help)
        api_help_btn.pack(padx=10, pady=5, anchor=tk.W)
        
        # API selection
        api_select_frame = ttk.Frame(api_frame)
        api_select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_select_frame, text="Weather API Provider:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        api_dropdown = ttk.Combobox(api_select_frame, textvariable=self.active_api, state="readonly")
        api_dropdown['values'] = [api['name'] for api in self.available_apis.values()]
        api_dropdown.grid(row=0, column=1, padx=5, pady=5)
        api_dropdown.bind("<<ComboboxSelected>>", self.on_api_change)
        
        # API Key entry
        api_key_frame = ttk.Frame(api_frame)
        api_key_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_key_frame, text="API Key:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_key_entry = ttk.Entry(api_key_frame, width=40)
        if self.api_key:
            self.api_key_entry.insert(0, self.api_key)
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        api_key_buttons = ttk.Frame(api_key_frame)
        api_key_buttons.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(api_key_buttons, text="Save Key", 
                  command=self.save_api_key).pack(side=tk.LEFT, padx=2)
        
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_key_buttons, text="Show Key", 
                       variable=self.show_key_var, 
                       command=self.toggle_show_key).pack(side=tk.LEFT, padx=10)
        
        # Test API key button
        ttk.Button(api_frame, text="Test API Key", 
                  command=self.test_api_key).pack(padx=10, pady=5, anchor=tk.W)
        
        # Display Settings section
        display_frame = ttk.LabelFrame(self.settings_tab, text="Display Settings")
        display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Units selection
        units_frame = ttk.Frame(display_frame)
        units_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(units_frame, text="Temperature Units:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Radiobutton(units_frame, text="Celsius (°C)", 
                       variable=self.units, value="metric").grid(
                           row=0, column=1, padx=5, pady=5)
        
        ttk.Radiobutton(units_frame, text="Fahrenheit (°F)", 
                       variable=self.units, value="imperial").grid(
                           row=0, column=2, padx=5, pady=5)
        
        # Auto-refresh settings
        refresh_frame = ttk.Frame(display_frame)
        refresh_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(refresh_frame, text="Auto-refresh:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=self.config.get('auto_refresh', False))
        ttk.Checkbutton(refresh_frame, text="Enable", 
                       variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).grid(
                           row=0, column=1, padx=5, pady=5)
        
        ttk.Label(refresh_frame, text="Refresh interval (minutes):").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.refresh_interval = tk.StringVar(value=str(self.config.get('refresh_interval', 30)))
        interval_spin = ttk.Spinbox(refresh_frame, from_=5, to=120, 
                                   textvariable=self.refresh_interval, width=5)
        interval_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    def test_api_key(self):
        """Test if the current API key works"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        self.status_bar.config(text="Testing API key...")
        self.root.update_idletasks()
        
        try:
            # Test with a simple request for London
            params = {
                "q": "London",
                "appid": api_key,
                "units": "metric"
            }
            
            api_info = self.available_apis[self.active_api.get()]
            response = requests.get(api_info['current_url'], params=params, timeout=10)
            
            if response.status_code == 200:
                self.api_key = api_key
                self.save_config()
                messagebox.showinfo("Success", "API key is valid! You can now search for weather.")
                self.status_bar.config(text="API key verified successfully")
            else:
                error_msg = response.json().get('message', 'Unknown error')
                messagebox.showerror("API Error", f"Error: {error_msg}")
                self.status_bar.config(text=f"API key test failed: {error_msg}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to weather service: {str(e)}")
            self.status_bar.config(text="API key test failed - connection error")
    
    def get_weather(self):
        """Fetch current weather and forecast data"""
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showerror("Error", "Please enter a city name")
            return
        
        # Update status
        self.status_bar.config(text=f"Fetching weather data for {city}...")
        self.root.update_idletasks()
        
        # Add to search history if not already there
        if city not in self.search_history:
            self.search_history.append(city)
            self.city_entry['values'] = self.search_history
        
        # Update current city
        self.current_city.set(city)
        
        # Check API key
        api_key = self.api_key or self.api_key_entry.get().strip()
        if not api_key:
            self.notebook.select(self.settings_tab)
            messagebox.showerror("Error", "Please enter your API key in Settings tab")
            self.status_bar.config(text="Error: No API key provided")
            return
        
        # Get selected API info
        api_info = self.available_apis.get(self.active_api.get())
        if not api_info:
            messagebox.showerror("Error", "Invalid API selection")
            self.status_bar.config(text="Error: Invalid API selection")
            return
        
        # Start data fetching in a separate thread to keep UI responsive
        threading.Thread(target=self.fetch_weather_data, 
                        args=(city, api_key, api_info), 
                        daemon=True).start()
    
    def save_api_key(self):
        """Save API key to configuration"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.api_key = api_key
            self.save_config()
            messagebox.showinfo("Settings", "API key saved successfully")
            
            # If we're showing the warning in the weather tab, refresh the UI
            self.setup_current_weather_tab()
        else:
            messagebox.showerror("Error", "Please enter a valid API key")
    
    def toggle_show_key(self):
        """Toggle showing/hiding API key"""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

def main():
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()