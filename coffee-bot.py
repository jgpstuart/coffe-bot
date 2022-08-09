import tweepy
import configparser
import requests
import weather
import yaml
import random

# picks a location to meet from coffee locations master list
def pick_location(COFFEE_SHOP_LIST, VISITED_COFFEE_SHOPS):
    location_name = ""
    while location_name == "":
        # get a random location from the list of locations
        with open(COFFEE_SHOP_LIST) as locations:
            location_list = yaml.load(locations, Loader=yaml.FullLoader)
            location_pick = random.choice(location_list)
            location_name = location_pick["name"]
            location_address = location_pick["address"]
            location_url = location_pick["url"] if location_pick.get("url") else "" # use get here in case there is no url (returns None)

            # check to see if it's in the list of recently visited locations
            with open(VISITED_COFFEE_SHOPS) as recently_visited:
                recent_locations = yaml.load(recently_visited, Loader=yaml.FullLoader) or {}
                for dict in recent_locations:
                    if dict["name"] == location_name:
                        location_name = ""
    
    # add the location to the recently visited list
    with open(VISITED_COFFEE_SHOPS, "r+") as file:
        recently_visited = yaml.load(file, Loader=yaml.FullLoader) or []
        recently_visited.append(location_pick.copy())
        print("Picked location is: " + location_name)
        file.seek(0)
        yaml.dump(recently_visited, file)
    
    return location_name, location_address, location_url

# when all locations have been visited, erase the top half of the list
def truncate_visited(COFFEE_SHOP_LIST, VISITED_COFFEE_SHOPS):
    with open(COFFEE_SHOP_LIST) as locations:
        location_list = yaml.load(locations, Loader=yaml.FullLoader)
        with open(VISITED_COFFEE_SHOPS, "r+") as recently_visited:
                recent_locations = yaml.load(recently_visited, Loader=yaml.FullLoader) or {}
                if len(recent_locations) == len(location_list):
                    halved_locations = recent_locations[len(recent_locations)//2:]
                    recently_visited.seek(0)
                    recently_visited.truncate(0)
                    yaml.dump(halved_locations, recently_visited)

# load config varaibles
config = configparser.ConfigParser()
config.read('config.ini')

lat = config['lat/long']['weather_lat']
long = config['lat/long']['weather_long']
API_KEY = config['twitterAPIKey']['api_key']
API_KEY_SECRET = config['twitterAPIKey']['api_key_secret']
ACCESS_TOKEN = config['twitterAccessToken']['access_token']
ACCESS_TOKEN_SECRET = config['twitterAccessToken']['access_token_secret']
BEARER_TOKEN = config['twitterBearerToken']['bearer_token']
WEATHER_API_KEY = config['weatherApiKey']['weather_api_key']
COFFEE_SHOP_LIST = config['coffeeLocations']['coffee_shop_list']
VISITED_COFFEE_SHOPS = config['coffeeLocations']['coffee_shops_visited']

# Weather Checks
checkForRain = True if config['weather']['check_rain'] == "True" else False
checkForTemperature = True if config['weather']['check_temperature'] == "True" else False

# Authenticate to Twitter
auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Create API object for interacting with Twitter
api = tweepy.API(auth)

try:
    api.verify_credentials()
except:
    # TODO: create logging for this message
    print("Error during authentication")

# check weather for Calgary
url = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&units=metric" % (lat, long, WEATHER_API_KEY)
response = requests.get(url)

# if raining, post tweet that meetup isn't happening
# TODO: get the weather check setup done
if checkForRain or checkForTemperature:
    weather.parseRawWeather(response.text, checkForRain, checkForTemperature)

# check if the list of recently visited locations is the same size as the master list
truncate_visited(COFFEE_SHOP_LIST, VISITED_COFFEE_SHOPS)

# get a location from the locations list
location_name, location_address, location_url = pick_location(COFFEE_SHOP_LIST, VISITED_COFFEE_SHOPS)

# put the string together for the meeting
tweet = "This week's meetup will be at " + location_name + " located at " + location_address + ": " + location_url + "\nSee you soon! #CoffeeOutside #coffeeyyc"
print(tweet)

# post the tweet
api.update_status(tweet)