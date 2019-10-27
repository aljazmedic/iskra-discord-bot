from discord.ext import commands
import discord, logging
from discord.ext.commands import has_permissions, Bot

logger = logging.getLogger(__name__)

class ModerationCog(commands.Cog, name='Moderation Cog'):
	def __init__(self, bot: discord.ext.commands.Bot):
		self.bot = bot

	@commands.command(name='ping', aliases=["Beer"], pass_context=True,
				 description="Answers with \"'mention' Pong!\"", brief="Replies Pong!")
	async def ping(self, context: discord.ext.commands.Context):
		user_mention = context.message.author.mention
		await context.send("%s Pong!" % user_mention)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		channel = member.guild.system_channel
		role = discord.utils.get(member.server.roles, name='New')
		if role:
			await member.add_roles(role)

	@commands.command(pass_context=True)
	async def help(self, context):
		author = context.message.author

		embed = discord.Embed(color=discord.Color.orange())

		embed.set_author(name='Help')
		embed.add_field(name='roles <user=You>', value='Returns roles of user')
		await self.bot.send_message(author, embed=embed)

	@commands.command(name="?load")
	@has_permissions(administrator=True)
	async def load(self, bot_extension):
		try:
			self.bot.load_extension(bot_extension)
			logger.debug(f"Loaded {bot_extension}")
		except Exception as error:
			logger.debug(f'{bot_extension} cannot be loaded. [{error}]')

	@commands.command(name="?unload")
	@has_permissions(administrator=True)
	async def unload(self, bot_extension):
		try:
			self.bot.unload_extension(bot_extension)
			logger.info(f"Unloaded {bot_extension}")
		except Exception as error:
			logger.debug(f'{bot_extension} cannot be unloaded. [{error}]')

	@commands.command(name="?reload")
	@has_permissions(administrator=True)
	async def reload(self, bot_extension):
		try:
			self.bot.unload_extension(bot_extension)
			self.bot.load_extension(bot_extension)
			logger.debug(f"Reloaded {bot_extension}")
		except Exception as error:
			logger.debug(f'{bot_extension} cannot be reloaded. [{error}]')

	@commands.command(name="?list_extensions")
	@has_permissions(administrator=True)
	async def reload(self, bot_extension):
		try:
			self.bot.list_extensions()
			self.bot.unload_extension(bot_extension)
			self.bot.load_extension(bot_extension)
			logger.debug(f"Reloaded {bot_extension}")
		except Exception as error:
			logger.debug(f'{bot_extension} cannot be reloaded. [{error}]')
