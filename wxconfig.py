# Location variable to customise weather display
# Get current weather, For parameters see https://openweathermap.org/current
# Configuration for weather.py

# Location & language
CITY = "London"
COUNTRYCODE = "GB"
LANG = "EN"

# Open weathermap Key (Contact OpenWeatherMap.org directly if you need a new key)
API_KEY="080535da15e1e2a21f933846b0ba824a"

# Temperature units metric(C) or imperial(F)
# Units standard, metric and imperial units
UNITS = "metric"

# Atmospheric pressure units millibars(M) or inches mercury(I)
PRESSURE_UNITS = "M"

# Set date format, US format =  %H:%M %m/%d/%Y
# To display timezone use %Z  dateformat=%H:%M %Z %d/%m/%Y
DATE_FORMAT = "%H:%M %d/%m/%Y"

# Exit command either "" or the command to execute
#EXIT_COMMAND = "sudo systemctl restart radiod.service"
EXIT_COMMAND = ""

# UDP server for IR remote commands
UDP_HOST='localhost'
UDP_PORT=5100
