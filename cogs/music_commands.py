import discord
from discord.ext import commands
import asyncio

import logging

logger = logging.getLogger(__name__)
PLAYERS = {}

"""  ========== VOICE SECTION ==========  """


class MusicCog(commands.Cog, name='Music Cog'):
	def __init__(self, bot):
		self.bot = bot

	@staticmethod
	def log_players(self):
		if PLAYERS:
			try:
				print("Players:")
				for i, (id_, srvr) in enumerate(PLAYERS.items()):
					main_player = srvr['current']
					stat = "Playing" if main_player.is_playing() else "Paused"
					loops = ["Yes" if srvr["loop_1"] else "No", "No" if srvr["loop_q"] == -1 else "Yes"]
					print(f"\t{i+1}. ID:{id_}, Song loop: {loops[0]}, Queue loop : {loops[1]}")
					print(f"\tCurrent: \'{str(main_player.title)}\' ({str(main_player.duration)}s) - " + stat)
					print("\t\t"+", ".join([   f"\'{str(q.title)[:15]}\' ({str(q.duration)}s)" for q in srvr["queue"]   ]))
			except AttributeError:
				pass

	@staticmethod
	def next_player_in_queue_pop(self, id_):
		this_srvr = PLAYERS[id_]
		if this_srvr["loop_1"]:
			this_srvr["current"].start()
		elif this_srvr["queue"] != []:
			if this_srvr["loop_q"] == -1:
				player = this_srvr["queue"].pop(0)
				this_srvr["current"] = player
				player.start()
			else:
				player = this_srvr["queue"][this_srvr["loop_q"]]
				this_srvr["current"] = player
				this_srvr["loop_q"] = this_srvr["loop_q"]%len(this_srvr["queue"])
				player.start()
		else:
			this_srvr["current"] = None

	@staticmethod
	async def get_voice_client(self, context, join_if_not=False):
		voice_client = self.bot.voice_client_in(context.message.server)
		if not voice_client:
			#client is not in a voice channel
			if join_if_not:

				#joining authors voice channel
				channel = context.message.author.voice.voice_channel
				if not channel:
					#user isnt in a voice channel
					await context.send(f"You have to be in a voice channel to use this command! :x:")
					raise Exception("User not in a voice channel!")
				await self.bot.join_voice_channel(channel)
				return self.bot.voice_client_in(context.message.server)

			await self.bot.send_message(context.message.channel, f"I am not in a voice channel! :x:")
			raise Exception("Client not in a voice channel")
		return voice_client

	@commands.command(pass_context=True)
	async def fart(self, context):
		pass # TODO find wav

	@commands.command(name="join", pass_context=True)
	async def join_voice_channel(self, context):
		channel = context.message.author.voice.voice_channel
		if not channel:
			# user isnt in a voice channel
			await context.send(f"You have to be in a voice channel to use this command! :x:")
			raise Exception("User not in a voice channel!")

		await self.bot.join_voice_channel(channel)

	@commands.command(name="disconnect", aliases=["leave", "dc"], pass_context=True)
	async def leave(self, context):
		voice_client = await self.get_voice_client(context)

		#pause
		id_ = context.message.server.id
		PLAYERS[id_]["current"].pause()

		if not voice_client:
			await context.send(f"You have to be in a voice channel to use this command! :x:")
			return
		await voice_client.disconnect()

	@commands.command(name="play", aliases=["queue"], pass_context=True)
	async def play(self, context, *qword):
		qword = " ".join(qword)
		server = context.message.server
		voice_client = await self.get_voice_client(context, join_if_not=True)
		player = await voice_client.create_ytdl_player(qword, ytdl_options={'default_search': 'auto'},
														after=lambda: self.next_player_in_queue_pop(server.id))

		queues = PLAYERS.get(server.id, {"current":None, "queue":[], "loop_1":False, "loop_q":-1})
		if not queues["current"]:
			queues["current"] = player
			player.start()
		else:
			queues["queue"].append(player)
			await context.send(f"Queued {player.title}! :white_check_mark:")
		PLAYERS[server.id] = queues



	@commands.command(name="pause", pass_context=True)
	async def pause(self, context):
		id_ = context.message.server.id
		PLAYERS[id_]["current"].pause()

	@commands.command(name="stop", pass_context=True)
	async def stop(self, context):
		id_ = context.message.server.id
		PLAYERS[id_]["current"].stop()

	@commands.command(name="resume", pass_context=True)
	async def resume(self, context):
		await self.get_voice_client(context, join_if_not=True)
		id_ = context.message.server.id
		PLAYERS[id_]["current"].resume()

	@commands.command(name="skip", pass_context=True)#TODO index skip
	async def skip(self, context, n="1"):
		id_ = context.message.server.id
		try:
			n = int(n)
		except ValueError:
			n = 1
		n = min(n, len(PLAYERS[id_]["queue"]))
		id_ = context.message.server.id
		PLAYERS[id_]["current"].stop()
		for _ in range(n):
			print("Skipped 1")
			PLAYERS[id_]["current"] = PLAYERS[id_]["queue"].pop(0)
		PLAYERS[id_]["current"].start()

	@commands.command(name="volume", pass_context=True)#TODO embed
	async def volume(self, context, n):
		try:
			n = int(n)
			n = max(1, min(n, 100))
			id_ = context.message.server.id
			PLAYERS[id_]["current"].volume = n
		except:
			pass

	@commands.command(name="loop", pass_context=True)
	async def loop(self, context):
		id_ = context.message.server.id
		PLAYERS[id_]["loop_1"] = not PLAYERS[id_]["loop_1"]
		loop_n = "Song loop"
		loop_q = "Enabled!" if PLAYERS[id_]["loop_1"] >= 0 else "Disabled!"

		embed = discord.Embed(
				title=loop_n,
				color=discord.Color.blue()
			)
		embed.add_field(name=loop_n, value=loop_q)
		await context.send(embed=embed)

	@commands.command(name="loopqueue", pass_context=True)
	async def loopqueue(self, context):
		id_ = context.message.server.id
		PLAYERS[id_]["loop_q"] = 0 if PLAYERS[id_]["loop_q"] == -1 else -1

		loop_n = "Queue loop"
		loop_q = "Enabled!" if PLAYERS[id_]["loop_q"] >= 0 else "Disabled!"

		embed = discord.Embed(
				title=loop_n,
				color=discord.Color.blue()
			)
		embed.add_field(name=loop_n, value=loop_q)
		await context.send(embed=embed)
