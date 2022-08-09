import json

def parseRawWeather(weatherData, checkForRain, checkForTemperature):
    # load the weatherData as a json
    weatherData = json.loads(weatherData)