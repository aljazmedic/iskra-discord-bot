import asyncio
import datetime
import os
from os import path

import logging
from arguments import run_args_init
from discord import Game
from discord.ext.commands import Bot
from discord.ext import commands
import dotenv

logger = logging.getLogger()

class IskraBot(Bot):
	def __init__(self, *args, **kwargs):
		super(IskraBot, self).__init__(*args, **kwargs)
		self.default_server_id = os.getenv("DEFAULT_DISCORD_SERVER_ID")
		self.start_time = None

	@commands.Cog.listener()
	async def on_ready(self):
		# Check if default server is set
		self.start_time = datetime.datetime.now()
		logger.info('Logged in as')
		logger.info(f"Name:      \t{self.user.name}")
		logger.info(f"ID:        \t{self.user.id}")
		logger.info(f"Start time:\t{self.start_time}")
		logger.info(f"Join link: \t{self.generate_join_link()}")
		await self.change_status()

	def generate_join_link(self, permissions=8, scope='bot'):
		return f"https://discordapp.com/oauth2/authorize?client_id={self.user.id}&scope={scope}&permissions={permissions}"

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		logger.info(f"Joined server {guild.name}")
		default_server_id = os.getenv("DEFAULT_DISCORD_SERVER_ID")
		if not default_server_id:
			default_server_id = str(guild.id)
			dotenv.set_key(dotenv_path=path.join(path.curdir, ".env"), key_to_set="DEFAULT_DISCORD_SERVER_ID",
							value_to_set=default_server_id)
			logger.info(f'Added default server: {guild.name} ({guild.id})')
		else:
			await guild.leave()

	async def log_active_time(self):
		await self.wait_until_ready()
		while not self.is_closed:
			await asyncio.sleep(5)
			logger.info(f"Running time:\t {datetime.datetime.now() - self.start_time}")

	async def change_status(self):
		await self.wait_until_ready()
		await self.change_presence(activity=Game(name="with your Mom *Kappa*"))


def main():
	args_parsed = run_args_init()
	uniquestr = datetime.datetime.now().strftime("%d-%b_%H%M%S")
	logFormatter = logging.Formatter(
		fmt='%(asctime)-15s - (%(relativeCreated)-8d ms) |%(levelname)-7s| @ [%(threadName)-12.12s] %(name)15.15s - %(message)s',
		datefmt='%d-%b %H:%M:%S')
	if args_parsed.verbose:
		dbg_lvl = logging.DEBUG
		print("Verbose mode:")
	elif args_parsed.quiet:
		dbg_lvl = logging.WARNING
	else:
		dbg_lvl = logging.INFO
	os.makedirs(args_parsed.log_dir, exist_ok=True)
	fileHandler = logging.FileHandler(os.path.join(args_parsed.log_dir, args_parsed.log_file_name % uniquestr),
										mode=args_parsed.log_mode)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(dbg_lvl)
	fileHandler.setLevel(logging.DEBUG)
	consoleHandler.setFormatter(logFormatter)
	fileHandler.setFormatter(logFormatter)

	global logger
	logger.setLevel(dbg_lvl)
	logger.addHandler(consoleHandler)
	logger.addHandler(fileHandler)

	# Bot section #
	bot = IskraBot(command_prefix='.')
	bot.remove_command('help')
	dotenv.load_dotenv()
	from cogs.moderation import ModerationCog
	from cogs.music_commands import MusicCog
	from cogs.weather_commands import WeatherCog

	bot.add_cog(ModerationCog(bot))
	# bot.add_cog(MusicCog(bot))
	bot.add_cog(WeatherCog(bot, os.getenv("OPEN_WEATHER_API_KEY")))

	token = os.getenv("DISCORD_API_KEY")
	bot.run(token)


if __name__ == '__main__':
	main()
