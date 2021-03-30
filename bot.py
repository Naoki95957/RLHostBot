from asyncio.tasks import all_tasks
from datetime import timedelta
from operator import index
import os
from os import kill, path
from discord.ext import tasks
import asyncio
import discord
import pickle
import copy
import json
import time
import re
import psutil
import subprocess
import websockets
from threading import Thread
from dotenv import load_dotenv
from pprint import pprint

from websockets.client import WebSocketClientProtocol

# TODO add proper format help for commands
# TODO list all commands (in help)
# TODO show all presets
# TODO prettier way to handle mutators?
# TODO playlists? maps + presets?

# how many seconds you would like to get updates
PLUGIN_FREQUENCY = 5
# Will always attempt to link the plugin
ALWAYS_RECONNECT = True

MUTATORS = {
    "FreePlay" : ["Default", "FreePlay"],
    "GameTimes" : ["Default", "10Minutes", "20Minutes", "UnlimitedTime"],
    "GameScores" : ["Default", "Max1", "Max3", "Max5", "Max7", "UnlimitedScore"],
    "OvertimeRules" : ["Default", "Overtime5MinutesFirstScore", "Overtime5MinutesRandom"],
    "MaxTimeRules" : ["Default", "MaxTime11Minutes"],
    "MatchGames" : ["Default", "3Games", "5Games", "7Games"],
    "GameSpeed" : ["Default", "SloMoGameSpeed", "SloMoDistanceBall"],
    "BallMaxSpeed" : ["Default", "SlowBall", "FastBall", "SuperFastBall"],
    "BallType" : ["Default", "Ball_CubeBall", "Ball_Puck", "Ball_BasketBall", "Ball_Haunted", "Ball_BeachBall"],
    "BallGravity" : ["Default", "LowGravityBall", "HighGravityBall", "SuperGravityBall"],
    "BallWeight" : ["Default", "LightBall", "HeavyBall", "SuperLightBall", "MagnusBall", "MagnusBeachBall"],
    "BallScale" : ["Default", "SmallBall", "MediumBall", "BigBall", "GiantBall"],
    "BallBounciness" : ["Default", "LowBounciness", "HighBounciness", "SuperBounciness"],
    "MultiBall" : ["Default", "TwoBalls", "FourBalls", "SixBalls"],
    "Boosters" : ["Default", "NoBooster", "UnlimitedBooster", "SlowRecharge", "RapidRecharge"],
    "Items" : [
        "Default", "ItemsMode", "ItemsModeSlow",
        "ItemsModeBallManipulators", "ItemsModeCarManipulators", "ItemsModeSprings",
        "ItemsModeSpikes", "ItemsModeRugby", "ItemsModeHauntedBallBeam"],
    "BoosterStrengths" : ["Default", "BoostMultiplier1_5x", "BoostMultiplier2x", "BoostMultiplier10x"],
    "Gravity" : ["Default", "LowGravity", "HighGravity", "SuperGravity", "ReverseGravity"],
    "Demolish" : ["Default", "NoDemolish", "DemolishAll", "AlwaysDemolishOpposing", "AlwaysDemolish"],
    "RespawnTime" : ["Default", "TwoSecondsRespawn", "OnceSecondRespawn", "DisableGoalDelay"],
    "BotLoadouts" : ["Default", "RandomizedBotLoadouts"],
    "AudioRules" : ["Default", "HauntedAudio"],
    "GameEventRules" : ["Default", "HauntedGameEventRules", "RugbyGameEventRules"]
}

class PlayBot(discord.Client):

    bot_id = 1234567890
    my_id = 1234567890
    bakkesmod_server = ''
    rcon_password = ''
    token = None
    rl_path = ""
    custom_path = ""
    ip_address = ""
    game_password = ""

    rl_pid = None
    companion_plugin_connected = False
    reconnect = False;

    str_pattern = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"
    
    file = "./bot_stuff.p"
    background_timer = 15 # how frequently background tasks will be executed
    permitted_roles = []
    base_command = "!host"
    listening_channels = []
    # used to display score info in discord :)
    binded_message = None
    binded_message_ID = None
    binded_message_channel = None
    roles = []
    custom_map_dictionary = {}

    match_data = {}
    
    print_statements = False

    __bot_thread = None

    def __init__(self, print_statements=False):
        super().__init__()
        load_dotenv('./config.env')
        self.pattern = re.compile(self.str_pattern)
        self.bot_id = os.getenv('BOT_ID')
        self.my_id = os.getenv('MY_ID')
        self.bakkesmod_server = os.getenv('BAKKES_SERVER')
        self.rcon_password = os.getenv('RCON_PASSWORD')
        self.rl_path = os.getenv('RL_PATH')
        self.custom_path = os.getenv('CUSTOM_PATH')
        self.token = os.getenv('DISCORD_TOKEN')
        self.game_password = os.getenv('GAME_PASSWORD')
        self.print_statements = print_statements

    def initialize(self):
        Thread(target=self.__background_loop).start()
        Thread(target=self.between_plugin_callback).start()
        self.index_custom_maps()
        self.update_companion_message.start()
        self.run(self.token)

    def join_bot_thread(self):
        if self.__bot_thread and isinstance(self.__bot_thread, Thread):
            self.__bot_thread.join()

    def index_custom_maps(self):
        """
        This just indexes custom maps and puts them into a dictionary for future use
        """
        map_index = {}
        for root, dirs, files in os.walk(self.custom_path):
            for file in files:
                if file.endswith('.udk'):
                    map_index[file.replace('.udk', '')] = os.path.join(root, file)
        self.custom_map_dictionary = map_index

    def enable_print_statements(self, val: bool):
        """
        Enables or disables all print statements to terminal for the bot

        Args:
            val (bool): True/False
        """
        self.print_statements = val

    def print_statements_enabled(self) -> bool:
        """
        Fetches whether print statements were enabled or not

        Returns:
            bool: True/False
        """
        return self.print_statements

    async def on_ready(self):
        self.try_loading()
        for guild in self.guilds:
            if self.print_statements:
                print(
                    f'{self.user} is connected to the following guilds:\n'
                    f'{guild.name}(id: {guild.id})'
                    f'\nChannel list: {guild.text_channels}'
                    f'\nRoles in order: {guild.roles}'
                )
            self.roles.extend(guild.roles)
        await PlayBot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.listening, name="others play Rocket League"))

    async def on_message(self, message: discord.message.Message):
        if message.author.id == self.bot_id or self.base_command not in str(message.content):
            return
        try:
           await self.handle_command(self.tokenize(message.content), message)
        except Exception as e:
            pass
        self.try_saving()

    async def handle_command(self, argv: list, message: discord.Message):
        if message.channel.id in self.listening_channels or message.author.id == int(self.my_id):
            if argv[0] == self.base_command:
                # help command
                if argv[1] == 'help':
                    await self.help_command(message)
                # allows user to add roles that bot will listen to
                elif argv[1] == 'permit':
                    # if permissions are empty or ...
                    if (not self.permitted_roles) or self.has_permission(message):
                        await self.set_permit_command(message)
                    else:
                        await self.permission_failure(message)
                # add channel for bot to listen to
                elif argv[1] == 'addchannel':
                    if (not self.listening_channels) or self.has_permission(message):
                        self.listening_channels.append(message.channel.id)
                        await message.channel.send("Added channel")
                    else:
                        await self.permission_failure(message)
                # remove channel for bot to listen to
                elif argv[1] == 'removechannel':
                    if (self.listening_channels) or self.has_permission(message):
                        self.listening_channels.remove(message.channel.id)
                        await message.channel.send("Removed channel")
                    else:
                        await self.permission_failure(message)
                # lists maps known to the bot
                elif argv[1] == 'maps':
                        await self.list_maps(message)
                # reloads bot's index (not rl's)
                elif argv[1] == 'reload-maps':
                    if self.has_permission(message):
                        await self.index_custom_maps()
                    else:
                        await self.permission_failure(message)
                # removes a role from permissions
                elif argv[1] == 'demote':
                    if self.has_permission(message):
                        await self.remove_permit_command(message)
                    else:
                        await self.permission_failure(message)
                elif argv[1] == 'bind':
                    if self.has_permission(message):
                        await self.bind_message(message)
                    else:
                        await self.permission_failure(message)
                elif argv[1] == 'unbind':
                    if self.has_permission(message):
                        self.binded_message = None
                        self.binded_message_channel = None
                        self.binded_message_ID = None
                        await message.channel.send("Binding dropped")
                    else:
                        await self.permission_failure(message)
                # automatically does some of the start up sequence
                elif argv[1] == 'start':
                    if self.companion_plugin_connected:
                        message = await message.channel.send("RL is already running")
                    else:
                        message = await message.channel.send("Working on it ...")
                        await self.start_game()
                        time.sleep(20)
                        # TODO may not need to do this if I publish my plugin
                        # will need to rename the plugin for sure lol
                        await self.attempt_to_sendRL("plugin load plugin2")
                        time.sleep(1)
                        await self.attempt_to_sendRL("hcp start_rp")
                        time.sleep(1)
                        await self.attempt_to_sendRL("rp_custom_path " + self.custom_path.replace("\\", "/"))
                        time.sleep(1)
                        self.reconnect = True
                        await message.edit(content="Done")
                # mutator passing
                elif argv[1] == 'mutator':
                    try:
                        await self.handle_mutators(argv, message)
                    except Exception as e:
                        await message.channel.send("Sorry I didn't understand that")
                # preset passing
                elif argv[1] == 'preset':
                    try:
                        await self.attempt_to_sendRL("rp preset " + argv[2])
                        await message.channel.send("preset sent")
                    except Exception as e:
                        await message.channel.send("Sorry I didn't understand that")
                # selects the map and send it to rl
                elif argv[1] == 'restart':
                    if self.has_permission(message):
                        message = await message.channel.send("Working on it ...")
                        await self.kill_game()
                        time.sleep(5)
                        await self.start_game()
                        time.sleep(20)
                        # TODO may not need to do this if I publish my plugin
                        # will need to rename the plugin for sure lol
                        await self.attempt_to_sendRL("plugin load plugin2")
                        time.sleep(1)
                        await self.attempt_to_sendRL("hcp start_rp")
                        time.sleep(1)
                        await self.attempt_to_sendRL("rp_custom_path " + self.custom_path.replace("\\", "/"))
                        time.sleep(1)
                        self.reconnect = True
                        await message.edit(content="Done")
                    else:
                        await self.permission_failure(message)
                # selects the map and send it to rl
                elif argv[1] == 'map':
                    if argv[2] in self.custom_map_dictionary.keys():
                        await self.attempt_to_sendRL("rp map " + argv[2])
                        await message.channel.send("Sent map to game")
                    else:
                        await message.channel.send("I couldn't find that map :(")
                # selects the map and send it to rl
                # TODO if users are in game check if
                # you are sure you want to do this
                elif argv[1] == 'host':
                    await self.attempt_to_sendRL("rp host")
                    message = await message.channel.send("Game will attempt to host...")
                    time.sleep(15)
                    if self.match_data:
                        await message.edit(
                            content = "Match is online\nIP:" +
                            self.ip_address + "\n" +
                            self.game_password
                        )
                # sends map (full path) to rl
                elif argv[1] == 'mapd':
                        await self.attempt_to_sendRL("rp mapd " + argv[2])
                        await message.channel.send("Sent map to game")
                # script that restarts rl
                elif argv[1] == 'restartRL':
                    if self.has_permission(message):
                        await self.kill_game()
                        time.sleep(1)
                        await self.start_game()
                        await message.channel.send("Game restarted")
                    else:
                        await self.permission_failure(message)
                # starts RL
                elif argv[1] == 'startRL':
                    if self.has_permission(message):
                        await self.start_game()
                        await message.channel.send("Game started")
                    else:
                        await self.permission_failure(message)
                # kills/closes RL
                elif argv[1] == 'killRL':
                    if self.has_permission(message):
                        await self.kill_game()
                        await message.channel.send("Game killed")
                    else:
                        await self.permission_failure(message)
                # allows one to access bakkesconsole
                elif argv[1] == 'console':
                    if self.has_permission(message):
                        await self.pass_to_console(argv, message)
                        await message.channel.send("Sent instructions to game")
                    else:
                        await self.permission_failure(message)
                # link companion plugin for info
                elif argv[1] == 'setIP':
                    if self.has_permission(message):
                        self.ip_address = str(argv[2]).replace("\"", "")
                        await message.channel.send("IP address is now set up as: " + self.ip_address)
                    else:
                        await self.permission_failure(message)
                elif argv[1] == 'link-plugin':
                    if self.has_permission(message):
                        self.reconnect = True
                        await message.channel.send("Will attempt to connect to game")
                    else:
                        await self.permission_failure(message)
                else:
                    await self.help_command(argv, True)

    async def handle_mutators(self, argv: list, message: discord.Message):
        if len(argv) > 2:
            for key in MUTATORS.keys():
                if argv[2].lower() == key.lower():
                    argv[2] = key
            if len(argv) > 3 and argv[3].lower() in (string.lower() for string in MUTATORS[argv[2]]):
                if argv[3].lower() == "default":
                    await self.attempt_to_sendRL("rp mutator " + argv[2] + " \\\"\\\"")
                else:
                    await self.attempt_to_sendRL("rp mutator " + argv[2] + " " + argv[3])
                await message.channel.send("Mutator sent")
            else:
                options = ""
                for value in MUTATORS[argv[2]]:
                    options += value + "\n"
                await message.channel.send("Options for mutator " + argv[2] + " are:\n" + options)
        else:
            options = ""
            for value in MUTATORS.keys():
                options += value + "\n"
            await message.channel.send("Availible mutators are:\n" + options)

    async def list_maps(self, message: discord.Message):
        try:
            embed_var = discord.Embed(
                description="Here is a list of all the maps I can host:")
            value_str = ""
            extras = False
            keys = list(self.custom_map_dictionary.keys())
            keys.sort()
            for map_key in keys:
                # there is a 1024 char limit on value for embed fields
                if len(value_str + map_key + "\n") > 1023:
                    name = "Maps"
                    if extras:
                        name = "cont."
                    embed_var.add_field(name=name, value=copy.deepcopy(value_str))
                    value_str = ""
                    extras = True
                # this seems kinda weird but theres a 6k character limit and
                # I didn't wanna change the logic. My head is already tired
                if len(embed_var) > 4975:
                    await message.channel.send(embed=embed_var)
                    embed_var = discord.Embed(
                        description="Here is a list of all the maps I can host:")
                    value_str = ""
                    extras = False
                value_str += map_key + "\n"
            embed_var.add_field(name=name, value=copy.deepcopy(value_str))
            await message.channel.send(embed=embed_var)
        except Exception as e:
            await message.channel.send("Sorry, I couldn't find the maps :(")
    async def remove_permit_command(self, message: discord.Message):
        cont = str(message.content)
        try:
            role_id = int(cont.replace(self.base_command + ' remove ', ''))
            self.permitted_roles.pop(self.permitted_roles.index(role_id))
            await message.channel.send("I will no longer listen to the " + self.get_role(role_id).name +" role")
        except Exception as e:
            await message.channel.send("Sorry, I couldn't undersand that")

    async def pass_to_console(self, argv: list, message: discord.message):
            command = ""
            for i in range(2, len(argv)):
                command += (argv[i] + " ")
            try:
                await self.attempt_to_sendRL(command)
            except Exception as e:
                self.print("Command failed")
                self.print(e)

    async def set_permit_command(self, message: discord.Message):
        try:
            role_id = int(str(message.content).replace(self.base_command + ' permit ', ''))
            self.permitted_roles.append(role_id)
            await message.channel.send("I will listen to the " + self.get_role(role_id).name +" role when they command me to :)")
        except Exception as e:
            await message.channel.send("Sorry, I couldn't undersand that")

    async def help_command(self, message: discord.Message, error_response=False):
        desc = (
            self.base_command +
            " addchannel*\n"+
            "\tListen to a channel:\n\tArgs: [channel id]\n\n"+
            self.base_command +
            " bind*\n"+
            "\tBind scoreboard to this channel:\n\tArgs: None\n\n"+
            self.base_command +
            " console*\n"+
            "\tPass arguments directly to game console:\n\tArgs: [...]\n\n"+
            self.base_command +
            " demote*\n"+
            "\tRemove a role from permissions:\n\tArgs: [role id]\n\n"+
            self.base_command +
            " host\n"+
            "\tStart up a game!:\n\tArgs: None\n\n"+
            self.base_command +
            " killRL*\n"+
            "\tTerminates rocket league:\n\tArgs: None\n\n"+
            self.base_command +
            " link-plugin*\n"+
            "\tAttempts to start communication with custom plugin:\n\tArgs: None\n\n"+
            self.base_command +
            " map\n"+
            "\tPicks map to be hosted:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
            self.base_command +
            " mapd*\n"+
            "\tLoad map from directory listing:\n\tArgs: [full path of map]\n\n"+
            self.base_command +
            " maps\n"+
            "\tList all the availble maps:\n\tArgs: None\n\n"+
            self.base_command +
            " mutator\n"+
            "\tEdit availible mutators:\n\tArgs: [mutator][value]\n\t(if this is confusing hit F6 and follow instructions on `rp mutator`)\n\n"+
            self.base_command +
            " permit*\n"+
            "\tAdds a role to permssions:\n\tArgs: [role id]\n\n"+
            self.base_command +
            " preset\n"+
            "\tLoad in a predefined preset:\n\tArgs: [name of preset (case sensitve)]\n\n"+
            self.base_command +
            " reload-maps*\n"+
            "\tRe-indexes known maps (just the bot):\n\tArgs: None\n\n"+
            self.base_command +
            " removechannel*\n"+
            "\tStops listening to the channel:\n\tArgs: [channel id]\n\n"+
            self.base_command +
            " restart*\n"+
            "\tRestarts rocket league and reloads plugins:\n\tArgs: None\n\n"+
            self.base_command +
            " restartRL*\n"+
            "\tOnly restarts the rocket league application:\n\tArgs: None\n\n"+
            self.base_command +
            " setIP*\n"+
            "\tSets the IP to be reported:\n\tArgs: [ip address (use double quotes)]\n\n"+
            self.base_command +
            " startRL*\n"+
            "\tOnly starts up rocket league application:\n\tArgs: None\n\n"+
            self.base_command +
            " start\n"+
            "\tStarts application and loads plugins:\n\tArgs: None\n\n"+
            self.base_command +
            " unbind*\n"+
            "\tUnbinds 'scoreboard' message:\n\tArgs: None\n\n"+
            self.base_command +
            " help\n"+
            "\tPrints list of commands:\n\tArgs: None\n\n"
        )
        embed_var = discord.Embed(title="Commands", description=desc)
        embed_var.add_field(name="commands with a *", value="can only be executed by those with permissions", inline=False)
        msg = None
        if error_response:
            msg = "Sorry, I didn't understand that :("
        await message.channel.send(content=msg, embed=embed_var)

    async def attempt_to_sendRL(self, message: str):
        try:
            async with websockets.connect(self.bakkesmod_server, timeout=0.3) as websocket:
                await websocket.send('rcon_password ' + self.rcon_password)
                auth_status = await websocket.recv()
                assert auth_status == 'authyes'
                await websocket.send(message.encode())
                await websocket.close()
        except Exception as e:
            self.print("Failed to connect to RL")
            return None

    async def bind_message(self, message: discord.Message):
        self.binded_message = await message.channel.send("Binding...")
        self.binded_message_ID = self.binded_message.id
        self.binded_message_channel = self.binded_message.channel.id
        self.try_saving()

    @tasks.loop(seconds=PLUGIN_FREQUENCY)
    async def update_companion_message(self):
        await self.wait_until_ready()
        if not self.binded_message:
            if self.binded_message_ID and self.binded_message_channel:
                channel = self.get_channel(self.binded_message_channel)
                self.binded_message = await channel.fetch_message(self.binded_message_ID)
            else:
                return
        else:
            await self.binded_message.edit(content="", embed=self.get_score_embed())

    def get_score_embed(self) -> discord.Embed:
        if self.match_data:
            title = "Current Game"
            match_time = timedelta(seconds=int(self.match_data['matchlength']))
            passed_time = timedelta(seconds=float(self.match_data['gametime']))

            if self.match_data['overtime']:
                title += " - Over Time"
            if (not self.match_data['gameactive']) and self.match_data['gametime']:
                title = "Game Over"
            if self.match_data['unlimited']:
                match_time = "unlimited"
            if self.match_data['overtime']:
                passed_time += match_time

            embed_var = discord.Embed(
                title=title
            )
            embed_var.add_field(name="Map:", value=self.match_data['map'])
            embed_var.add_field(name="Match Length:", value=str(match_time), inline=False)
            embed_var.add_field(name="Duration:", value=str(passed_time), inline=False)
            team_0 = self.parse_team_info(self.match_data['teams'][0])
            embed_var.add_field(
                name=team_0[0],
                value=team_0[1], 
                inline=True
            )
            team_1 = self.parse_team_info(self.match_data['teams'][1])
            embed_var.add_field(
                name=team_1[0],
                value=team_1[1], 
                inline=True
            )
            return embed_var
        else:
            title = "OFFLINE - No game running currently"
            if self.companion_plugin_connected:
                title = "ONLINE - No game running currently"
            return discord.Embed(
                title=title,
            )

    def parse_team_info(self, team: dict) -> tuple:
        title = team['name'] + ' - ' + str(team['score'])
        players = ""
        for i in range(0, len(team['players'])):
            p = team['players'][i]
            players += (
                p['name'] +
                ' Sc-' + str(p['score']) +
                ' G-' + str(p['goals']) +
                ' A-' + str(p['assists']) +
                ' S-' + str(p['saves']) +
                ' Sh-' + str(p['shots']) 
                + "\n"
            )
        if not players:
            players = "None"
        return title, players

    async def start_game(self):
        """
        Starts up rocket league exe
        """
        self.print("Starting RL")
        subprocess.Popen(self.rl_path)

    async def kill_game(self):
        """
        Finds rocket league and kills the process
        """
        self.print("Killing RL")
        try:
            for proc in psutil.process_iter():
                try:
                    # would need to check others if it wasn't a windows only game
                    if "RocketLeague.exe" in proc.name():
                        self.print(["PID found:", proc.pid])
                        psutil.Process(proc.pid).kill()
                        self.companion_plugin_connected = False
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            self.print("Failed to kill proces")
            self.print(e)

    async def restart_game(self):
        """
        Simply restarts the game
        """
        self.kill_game()
        time.sleep(1)
        self.start_game()

    async def permission_failure(self, message: discord.Message):
        """
        Helper function, just decides how to send a failure message
        """
        if self.permitted_roles:
            await message.channel.send("Sorry, you do not have permission <@" + str(message.author.id) + ">")
        else:
            await message.channel.send("Permissions must be set first! <@" + str(message.author.id) + ">")

    def between_plugin_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.__companion_plugin())
        loop.close()
   
    async def __companion_plugin(self):
        """
        this loop will attempt to remain in contact with the game to get
        general status updates on the game state

        Returns:
            **never**
        """
        while 1:
            if self.reconnect or ALWAYS_RECONNECT:
                self.print("Attempting to connect to companion plugin")
                self.reconnect = False
                try:
                    async with websockets.connect(self.bakkesmod_server, timeout=3) as websocket:
                        await websocket.send('rcon_password ' + self.rcon_password)
                        auth_status = await websocket.recv()
                        assert auth_status == 'authyes'
                        # send general check command
                        await websocket.send('hcp')
                        companion_status = await websocket.recv()
                        assert companion_status == 'OK'
                        self.companion_plugin_connected = True
                        # connection is established
                        # We'll basically run this indefinitely
                        while self.companion_plugin_connected:
                            # query command for info
                            await websocket.send('hcp status')
                            # get back info
                            game_status = await websocket.recv()
                            if (game_status != "ERR"):
                                self.match_data = copy.deepcopy(json.loads(str(game_status)))
                                print(self.match_data)
                            else:
                                self.match_data = {}
                            time.sleep(PLUGIN_FREQUENCY)
                except Exception as e:
                    self.print("Failed to connect to RL")
            self.match_data = {}
            time.sleep(5)

    def tokenize(self, line: str):
        """
        Helper that tokenizes line into an argument vector

        Args:
            line (str): a command straight off the command line

        Returns:
            argv [list]: Contains each seperate word
        """
        if not self.pattern:
            self.pattern = re.compile(self.str_pattern)
        argv = []
        none_matched = True
        for match in re.finditer(self.pattern, line):
            if none_matched:
                none_matched = False
            argv.append(match.group(0).rstrip())
        if none_matched:
            argv.append(line)
        return argv

    def try_loading(self):
        """
        Helper that loads in save file so that some previous commands are loaded
        """
        try:
            if path.exists(self.file):
                dictionary = pickle.load(open(self.file, 'rb'))
                self.permitted_roles = dictionary['permitted_roles']
                self.base_command = dictionary['base_command']
                self.background_timer = dictionary['timer']
                self.binded_message_ID = dictionary['bindID']
                self.binded_message_channel = dictionary['bindChannel']
                self.listening_channels = dictionary['listeningChannels']
                self.ip_address = dictionary['IP_address']
                if self.print_statements:
                    print('File loaded')
                    pprint(dictionary)
        except Exception as e:
            if self.print_statements:
                print("failed to load file :/")
                print(e)

    def try_saving(self):
        """
        Helper that saves a file so that some previous commands can be loaded
        """
        dictionary = self.get_bot_info()
        pickle.dump(dictionary, open(self.file, 'wb'))
        if self.print_statements:
            print("File saved")
            pprint(dictionary)
    
    def get_bot_info(self) -> dict:
        """
        Helper used to get data prepped for serialization

        Returns:
            dict: important bits of object data
        """
        dictionary = {}
        dictionary['permitted_roles'] = copy.deepcopy(self.permitted_roles)
        dictionary['base_command'] = copy.deepcopy(self.base_command)
        dictionary['timer'] = copy.deepcopy(self.background_timer)
        dictionary['bindID'] = copy.deepcopy(self.binded_message_ID)
        dictionary['bindChannel'] = copy.deepcopy(self.binded_message_channel)
        dictionary['listeningChannels'] = copy.deepcopy(self.listening_channels)
        dictionary['IP_address'] = copy.deepcopy(self.ip_address)
        return dictionary

    def __background_loop(self):
        while True:
            time.sleep(self.background_timer)
            self.try_saving()

    def has_permission(self, message: discord.message) -> bool:
        """
        Helper funciton that checks if this message is from a permited role/person

        Args:
            message (discord.message): the discord message in question

        Returns:
            bool: true for valid / false for unrecoginzed
        """
        return message.author.top_role.id in self.permitted_roles or message.author.id == int(self.my_id)

    def get_role(self, id: int) -> discord.Role:
        """
        Helper function that gets discord role object from id

        Args:
            id (int): role ID

        Returns:
            discord.Role : discord role object
        """
        for role in self.roles:
            if role.id == id:
                return role
        return None

    def print(self, message):
        if self.print_statements:
            print(message)

    def __del__(self):
        self.try_saving()


def main():
    bot = PlayBot(print_statements=True)
    bot.initialize()
    
if __name__ == "__main__":
    main()
