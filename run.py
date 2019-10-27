import asyncio
import datetime
import os
from os import path

import logging
from arguments import run_args_init
from discord import Game, Guild, TextChannel
from discord.ext.commands import Bot
from discord.ext import commands
import discord.utils
import dotenv

logger = logging.getLogger()
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)


class IskraBot(Bot):
	def __init__(self, *args, **kwargs):
		super(IskraBot, self).__init__(*args, **kwargs)
		dotenv.load_dotenv(dotenv_path=path.join(path.curdir, ".env"))
		self._default_guild_id = int(os.getenv("DEFAULT_DISCORD_GUILD_ID", 0))
		self._status_channel_id = int(os.getenv("DEFAULT_DISCORD_STATUS_CHANNEL_ID", 0))
		logging.debug("Started with values: {}, {}".format(self._default_guild_id is not None, self._status_channel_id is not None))

	async def wait_for(self, event, *_, check=None, timeout=None):
		g: Guild = await super().wait_for(event, check=check, timeout=timeout)
		logger.debug(f'Joined {g.name}, from wait_for')
		return g

	@commands.Cog.listener()
	async def on_ready(self):
		# Check if default server is set
		logger.info('Logged in as')
		logger.info(f"Name:      \t{self.user.name}")
		logger.info(f"ID:        \t{self.user.id}")
		logger.info(f"Join link: \t{self.generate_join_link()}")
		await self.change_status()
		guild: Guild = await self.get_default_guild()
		logger.info(f"Connected to {guild.name}, setup complete!")
		await self.get_status_channel()
		if not discord.utils.get(guild.roles, name="New"):
			await guild.create_role(name="New")
		self.loop.create_task(self.update_status_channel())

	def generate_join_link(self, permissions=8, scope='bot'):
		return f"https://discordapp.com/oauth2/authorize?client_id={self.user.id}&scope={scope}&permissions={permissions}"

	async def get_status_channel(self) -> discord.TextChannel:
		"""
		:return: Gets default status channel
		"""
		dotenv.load_dotenv(dotenv_path=path.join(path.curdir, ".env"))
		self._status_channel_id = int(os.getenv("DEFAULT_DISCORD_STATUS_CHANNEL_ID", 0))
		if not self._status_channel_id:
			# Gets the guild and creates a channel
			default_guild: Guild = self.get_default_guild()
			status_channel: TextChannel = discord.utils.get(default_guild.text_channels, name='status-channel')
			overwrites = {
				default_guild.default_role: discord.PermissionOverwrite(read_messages=False)
			}
			if not status_channel:
				status_channel = default_guild.create_text_channel('status-channel', overwrites=overwrites)
			else:
				await status_channel.edit(overwrites=overwrites)

			self._status_channel_id = status_channel.id
			dotenv.set_key(	dotenv_path=path.join(os.curdir, ".env"),
							key_to_set="DEFAULT_DISCORD_STATUS_CHANNEL_ID",
							value_to_set=str(self._status_channel_id).replace("\"", "").replace("'", ""))
			dotenv.load_dotenv(dotenv_path=path.join(path.curdir, ".env"))

			logger.info(f'Added default status channel: {status_channel.name} ({status_channel.id})')
			return status_channel
		logger.debug(f"Getting channel with: {self._status_channel_id}")
		return self.get_channel(self._status_channel_id)

	async def get_default_guild(self) -> discord.Guild:
		dotenv.load_dotenv(dotenv_path=path.join(path.curdir, ".env"))
		self._default_guild_id = int(os.getenv("DEFAULT_DISCORD_GUILD_ID", 0))
		if not self._default_guild_id:
			guild: Guild = await self.wait_for('guild_join')
			dotenv.set_key(	dotenv_path=path.join(os.curdir, ".env"),
							key_to_set="DEFAULT_DISCORD_GUILD_ID",
							value_to_set=str(guild.id).replace("\"", "").replace("'", ""))

			logger.info(f'Added default guild: {guild.name} ({guild.id})')
		else:
			guild: Guild = self.get_guild(self._default_guild_id)
		return guild

	@commands.Cog.listener()
	async def on_guild_join(self, guild: Guild):
		logger.debug(f"on_guild_join {guild.name}")
		if (await self.get_default_guild()).id and guild.id != await self.get_default_guild():
			await guild.leave()

	async def change_status(self):
		await self.wait_until_ready()
		await self.change_presence(activity=Game(name="with your Mom *Kappa*"))

	async def update_status_channel(self):
		await self.wait_until_ready()
		while True:
			guild: Guild = await self.get_default_guild()
			status_channel: TextChannel = await self.get_status_channel()

			def is_online(m: discord.Member):
				return m.status in (discord.Status.online, discord.Status.idle) and not m.bot

			status_str = f"{sum([is_online(m) for m in guild.members])} active out of {guild.member_count}"
			logger.debug(f"Active members: {status_str}")
			await status_channel.edit(name=status_str)
			await asyncio.sleep(5)


def main():
	args_parsed = run_args_init()
	uniquestr = datetime.datetime.now().strftime("%d-%b_%H%M%S")
	log_formatter = logging.Formatter(
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
	file_handler = logging.FileHandler(os.path.join(args_parsed.log_dir, args_parsed.log_file_name % uniquestr),
										mode=args_parsed.log_mode)

	console_handler = logging.StreamHandler()
	console_handler.setLevel(dbg_lvl)
	file_handler.setLevel(logging.DEBUG)
	console_handler.setFormatter(log_formatter)
	file_handler.setFormatter(log_formatter)

	global logger
	logger.setLevel(dbg_lvl)
	logger.addHandler(console_handler)
	logger.addHandler(file_handler)

	# Bot section #
	bot = IskraBot(command_prefix='.')
	bot.remove_command('help')
	dotenv.load_dotenv(dotenv_path=path.join(os.curdir, ".env"))
	"""
		# TODO Import modules and add them using
		from cogs.extension_file import Extension
		bot.add_cog(Extension(bot))
	"""

	from cogs.weather import WeatherCog

	bot.add_cog(WeatherCog(bot))

	token = os.getenv("DISCORD_API_KEY")
	bot.run(token)


if __name__ == '__main__':
	main()
