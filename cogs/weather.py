import discord
import json
import requests
from discord.ext import commands
from geopy.exc import GeocoderNotFound
from geopy.geocoders import Nominatim
import logging

logger = logging.getLogger(__name__)


class WeatherCog(commands.Cog, name='Weather Cog'):
	def __init__(self, bot, appid_):
		self.bot = bot
		self.appid = appid_
		self.geolocator = Nominatim(user_agent="MedoBOT")

	def _get_weather_type(self, lat_lon, type_):
		TYPES = {
			"current": "https://api.openweathermap.org/data/2.5/weather",
			"5d_3h": "https://api.openweathermap.org/data/2.5/forecast"
		}
		query = {
			"lat": lat_lon[0],
			"lon": lat_lon[1],
			"units": "metric",
			"appid": self.appid
		}
		with requests.Session() as sess:
			r = sess.get(TYPES[type_], params=query)
			print(f"GET '{r.url}'")
		print(json.dumps(r.json(), indent=4))
		return r.json()

	def locate_city(self, query_word):
		return self.geolocator.geocode(query_word)

	@staticmethod
	def embed_w_data(self, data_loc, data_w):  # TODO Add custon emojis with deg
		png_url = "https://openweathermap.org/img/w/{}.png"
		color_map = {
			"Clear": 0x5491f2,  # Clear
			"Clouds": 0x96acce,  # Clouds
			"Rain": 0x1668e5  # Rain

		}
		embed = discord.Embed(
			title=f"Weather\n{data_loc['display_name']}",
			color=color_map[data_w["weather"][0]["main"]]
		)
		wth = data_w["weather"][0]
		mn = data_w["main"]
		wind = data_w["wind"]
		embed.set_thumbnail(url=png_url.format(wth["icon"]))
		embed.add_field(name=wth["main"], value=f"{mn['temp']}°C, {mn['pressure']}hPa", inline=True)
		deg = '' if ('deg' not in wind) else f", {str(wind.get('deg'))}°"
		embed.add_field(name="Wind", value=f"{str(wind['speed'])}m/s"+deg)
		embed.set_footer(text="OpenWeather & GeoPY API")
		return embed

	@commands.command(name="weather_now", aliases=["vreme_zdaj", 'weather'], pass_context=True)
	async def weather_at_location(self, context, *place):
		if not place or place == []:
			await context.send(f"{context.message.author.mention} No location specified!")
			return
		place = " ".join(place)
		try:
			location = self.locate_city(place)
			if not location:
				raise GeocoderNotFound
			location = location.raw
		except GeocoderNotFound:
			await context.send(f"{context.message.author.mention} '{place}' cannot be found...")
			return
		weather_data = self._get_weather_type((location["lat"], location["lon"]), "current")
		await context.send(embed=self.embed_w_data(self, location, weather_data))


if __name__ == '__main__':
	from dotenv import load_dotenv
	import os
	load_dotenv()
	w = WeatherCog(None, os.getenv('OPEN_WEATHER_API_KEY'))
	a = w.locate_city("Kranj, Slovenija")
	print(json.dumps(a.raw, indent=4))
	print(w._get_weather_type((a.raw["lat"], a.raw["lon"]), "current"))
