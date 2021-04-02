from datetime import timedelta
import os
from os import path
from discord import reaction
from discord.ext import tasks
import math
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


# TODO log scoreboard entries? 
# TODO show all presets
# read presets bakkes? or scratch that and make your own?
# commands:
# list presets
#   lists aval presets
# TODO playlists? maps + presets?
# make map + preset, ... ?
# so make is the command
# map is manditory, preset is optional
# and ',' indicates next term?

# fix fugly code

# how many seconds you would like to get updates
PLUGIN_FREQUENCY = 5

# how long game will go to main menu once game is over to avoid long lobby times
# time would be IDLE_COUNT * PLUGIN_FREQUENCY seconds
IDLE_COUNT = 60

# Will always attempt to link the plugin
ALWAYS_RECONNECT = True

# used to divide up the massive amount of mutators into multiple messages
MUTATOR_MESSAGES = 2

# This is used to let the bot know when is a safe time to call on rcon and bakkes
# to start injecting.
# This is also kind of arbitrary since it depends on fast you load the game
GAME_LOAD_TIME = 20

# TODO Move the 'mutator_value_dictionary' into a parallel list under the values
# say value_names : [...]?
# "Mutator" : : {"emote" : ":emoji:", "values" : ["value0", "value1", ...], "value_names" : ["<meaning>", ...]}
MUTATORS = {
    "FreePlay" : {
        "alt_name" : "Free Play",
        "emote" : "🆓",
        "values" : ["Default", "FreePlay"],
        "Default": "Disable Free Play"
    },
    "GameTimes" : {
        "alt_name" : "Match Length",
        "emote" : "🕐",
        "values" : ["Default", "10Minutes", "20Minutes", "UnlimitedTime"],
        "Default" : "5 Minutes"
    },
    "GameScores" : {
        "alt_name" : "Max Score",
        "emote" : "🗜️",
        "values" : ["Default", "Max1", "Max3", "Max5", "Max7", "UnlimitedScore"]
    },
    "OvertimeRules" : {
        "alt_name" : "Overtime",
        "emote" : "⏲️",
        "values" : ["Default", "Overtime5MinutesFirstScore", "Overtime5MinutesRandom"],
        "Default": "Unlimited"
    },
    "MaxTimeRules" : {
        "alt_name" : "Max Time Limit",
        "emote" : "⏰",
        "values" : ["Default", "MaxTime11Minutes"]
    },
    "MatchGames" : {
        "alt_name" : "Serires Length",
        "emote" : "🏁",
        "values" : ["Default", "3Games", "5Games", "7Games"],
        "Default": "Unlimited"
    },
    "GameSpeed" : {
        "alt_name" : "Game Speed",
        "emote" : "🎚️",
        "values" : ["Default", "SloMoGameSpeed", "SloMoDistanceBall"]
    },
    "BallMaxSpeed" : {
        "alt_name" : "Ball Max Speed",
        "emote" : "🏎️",
        "values" : ["Default", "SlowBall", "FastBall", "SuperFastBall"]
    },
    "BallType" : {
        "alt_name" : "Ball Type",
        "emote" : "🏀",
        "values" : ["Default", "Ball_CubeBall", "Ball_Puck", "Ball_BasketBall", "Ball_Haunted", "Ball_BeachBall"]
    },
    "BallGravity" : {
        "alt_name" : "Ball Gravity",
        "emote" : "🪂",
        "values" : ["Default", "LowGravityBall", "HighGravityBall", "SuperGravityBall"]
    },
    "BallWeight" : {
        "alt_name" : "Ball Physics",
        "emote" : "🪃",
        "values" : ["Default", "LightBall", "HeavyBall", "SuperLightBall", "MagnusBall", "MagnusBeachBall"]
    },
    "BallScale" : {
        "alt_name" : "Ball Size",
        "emote" : "💗",
        "values" : ["Default", "SmallBall", "MediumBall", "BigBall", "GiantBall"]
    },
    "BallBounciness" : {
        "alt_name" : "Ball Bounciness",
        "emote" : "🏓",
        "values" : ["Default", "LowBounciness", "HighBounciness", "SuperBounciness"]
    },
    "MultiBall" : {
        "alt_name" : "Number of Balls",
        "emote" : "🤡",
        "values" : ["Default", "TwoBalls", "FourBalls", "SixBalls"],
        "Default": "One"
    },
    "Boosters" : {
        "alt_name" : "Boost Amount",
        "emote" : "🔥",
        "values" : ["Default", "NoBooster", "UnlimitedBooster", "SlowRecharge", "RapidRecharge"]
    },
    "Items" : {
        "alt_name" : "Rumble",
        "emote" : "🌪️",
        "values" : [
            "Default", "ItemsMode", "ItemsModeSlow",
            "ItemsModeBallManipulators", "ItemsModeCarManipulators", "ItemsModeSprings",
            "ItemsModeSpikes", "ItemsModeRugby", "ItemsModeHauntedBallBeam"
        ],
        "Default": "None"
    },
    "BoosterStrengths" : {
        "alt_name" : "Boost Strength",
        "emote" : "💪",
        "values" : ["Default", "BoostMultiplier1_5x", "BoostMultiplier2x", "BoostMultiplier10x"],
        "Default": "1x"
    },
    "Gravity" : {
        "alt_name" : "Gravity",
        "emote" : "🍂",
        "values" : ["Default", "LowGravity", "HighGravity", "SuperGravity", "ReverseGravity"]
    },
    "Demolish" : {
        "alt_name" : "Demolish",
        "emote" : "🪖",
        "values" : ["Default", "NoDemolish", "DemolishAll", "AlwaysDemolishOpposing", "AlwaysDemolish"]
    },
    "RespawnTime" : {
        "alt_name" : "Respawn Time",
        "emote" : "🐈",
        "values" : ["Default", "TwoSecondsRespawn", "OnceSecondRespawn", "DisableGoalDelay"],
        "Default": "3 Seconds"
    },
    "BotLoadouts" : {
        "alt_name" : "Bot Loadouts",
        "emote" : "🎒",
        "values" : ["Default", "RandomizedBotLoadouts"]
    },
    "AudioRules" : {
        "alt_name" : "Audio",
        "emote" : "🔊",
        "values" : ["Default", "HauntedAudio"]
    },
    "GameEventRules" : {
        "alt_name" : "Game Event",
        "emote" : "🎲",
        "values" : ["Default", "HauntedGameEventRules", "RugbyGameEventRules"]
    }
}

# This translate the raw 'value' (except defaults) for the mutators to something more understandable
# Default is left out since the actual value is "", literally \"\"
MUTATOR_VALUE_DICTIONARY = {
    # free play
    "FreePlay" : "Enable Freeplay",
    # match length
    "10Minutes" : "10 minutes",
    "20Minutes" : "20 minutes",
    "UnlimitedTime" : "Unlimited",
    # max score
    "Max1" : "1 Goal",
    "Max3" : "3 Goals",
    "Max5" : "5 Goals",
    "Max7" : "7 Goals",
    # overtime
    "UnlimitedScore" : "Unlimited",
    "Overtime5MinutesFirstScore" : "+5 Max, First Score", 
    "Overtime5MinutesRandom" : "+5 Max, Random Team",
    # max time limit
    "MaxTime11Minutes" : "11 Minutes",
    # series length
    "3Games" : "3 Games",
    "5Games" : "5 Games",
    "7Games" : "7 Games",
    # game speed
    "SloMoGameSpeed" : "Slo-mo",
    "SloMoDistanceBall" : "Time Warp",
    # ball max speed
    "SlowBall" : "Slow",
    "FastBall" : "Fast",
    "SuperFastBall" : "Super Fast",
    # ball type
    "Ball_CubeBall" : "Cube",
    "Ball_Puck" : "Puck",
    "Ball_BasketBall" : "Basketball",
    "Ball_Haunted" : "Haunted Ball",
    "Ball_BeachBall" : "Beach Ball",
    # ball gravity
    "LowGravityBall" : "Low",
    "HighGravityBall" : "High",
    "SuperGravityBall" : "Super High",
    # ball physics
    "LightBall" : "Light",
    "HeavyBall" : "Heavy",
    "SuperLightBall" : "Super Light",
    "MagnusBall" : "Curve",
    "MagnusBeachBall" : "Beach Ball Curve",
    # ball size
    "SmallBall" : "Small",
    "MediumBall" : "Medium",
    "BigBall" : "Large",
    "GiantBall" : "Gigantic",
    # ball bounciness
    "LowBounciness" : "Low",
    "HighBounciness" : "High",
    "SuperBounciness" : "Super High",
    # number of balls
    "TwoBalls" : "Two",
    "FourBalls" : "Four",
    "SixBalls" : "Six",
    # boost amount
    "NoBooster" : "No Boost",
    "UnlimitedBooster" : "Unlimited",
    "SlowRecharge" : "Recharge (slow)",
    "RapidRecharge" : "Recharge (fast)",
    # rumble
    "ItemsMode" : "Default",
    "ItemsModeSlow" : "Slow",
    "ItemsModeBallManipulators" : "Civilized",
    "ItemsModeCarManipulators" : "Destruction Derby",
    "ItemsModeSprings" : "Spring Loaded",
    "ItemsModeSpikes" : "Spikes Only",
    "ItemsModeRugby" : "Rugby",
    "ItemsModeHauntedBallBeam" : "Haunted Ball Beam",
    # boost strength
    "BoostMultiplier1_5x" : "1.5x",
    "BoostMultiplier2x" : "2x",
    "BoostMultiplier10x" : "10x",
    # gravity
    "LowGravity" : "Low",
    "HighGravity" : "High",
    "SuperGravity" : "Super High",
    "ReverseGravity" : "Reverse",
    # demolish
    "NoDemolish" : "Disabled",
    "DemolishAll" : "Friendly Fire",
    "AlwaysDemolishOpposing" : "On Contact",
    "AlwaysDemolish" : "On Contact (FF)",
    # respawn time
    "TwoSecondsRespawn" : "2 Seconds",
    "OnceSecondRespawn" : "1 Second",
    "DisableGoalDelay" : "Disable Goal Reset",
    # bot loadouts
    "RandomizedBotLoadouts" : "Random",
    # Audio
    "HauntedAudio" : "Haunted",
    # Game event
    "HauntedGameEventRules" : "Haunted",
    "RugbyGameEventRules" : "Rugby"
}

# no mutators take more than 9 so 12 should be enough for now
# these will be the 'options' for the values on a given mutator
EMOTE_OPTIONS = [
    '🇦', '🇧',
    '🇨', '🇩',
    '🇪', '🇫',
    '🇬', '🇭',
    '🇮', '🇯',
    '🇰', '🇱'
]

VOTE_TO_PASS_EMOTE = "🗳️"

# This json is in the form:
# "file.udk" : {"title":"my custom map", "author":"by me", "description":"don't use plz"}
MAP_LIST = "./map_info.json"

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
    reconnect = False
    players_connected = 0
    idle_counter = 0
    vote_listing = None

    active_mutator_messages = []
    stop_adding_reactions = False
    in_reactions = False
    current_reaction = None
    admin_locked = False
    match_request_message = None

    str_pattern = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"
    master_map_list = None
    
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
        self.master_map_list = json.load(open(MAP_LIST))

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
                    list_name = self.master_map_list[file]['title']
                    iteration = 0
                    while (list_name in map_index.keys()):
                        iteration += 1
                        list_name = self.master_map_list[file]['title'] + " (" + str(iteration) + ")"
                    map_index[list_name] = os.path.join(root, file)
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
            # await message.channel.send("I didn't understand that")
            pass
        self.try_saving()

    async def handle_command(self, argv: list, message: discord.Message):
        if message.channel.id in self.listening_channels or message.author.id == int(self.my_id):
            if argv[0] == self.base_command:
                self.idle_counter = 0
                # help command
                if argv[1] == 'help':
                    await self.help_command(message)
                # allows user to add roles that bot will listen to
                elif argv[1] == 'permit':
                    if self.has_permission(message):
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
                # Lock is to allow an admin to use the bot for events etc
                elif argv[1] == 'lock':
                    if self.has_permission(message):
                        self.admin_locked = True
                        await message.channel.send("Editing commands locked")
                    else:
                        await self.permission_failure(message)
                # unlock reverses the lock -> to allow players to use the bot again
                elif argv[1] == 'unlock':
                    if self.has_permission(message):
                        self.admin_unlocked = False
                        await message.channel.send("Editing commands unlocked")
                    else:
                        await self.permission_failure(message)
                # lists maps known to the bot
                elif argv[1] == 'list-maps':
                    if self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
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
                        await message.channel.send("RL is already running")
                    elif self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
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
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        try:
                            await self.handle_mutators(argv, message.channel)
                        except Exception as e:
                            # exceptions will be printed based on code logic, no need for it here
                            pass 
                # preset passing
                elif argv[1] == 'preset':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        try:
                            await self.attempt_to_sendRL("rp preset " + argv[2])
                            await message.channel.send("Sent preset to game")
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
                # also prints the selected map info
                elif argv[1] == 'map':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    if self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        await self.send_selected_map(argv[2], message.channel)
                # attempts to start up the match with the given settings
                elif argv[1] == 'host':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.admin_locked and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        await self.attempt_to_host(message.channel)
                # sends map (full path) to rl
                elif argv[1] == 'mapd':
                    if self.has_permission(message):
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
                            if not self.companion_plugin_connected:
                                await message.channel.send("RL is not running")
                            else:
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

    async def send_selected_map(self, arg: str, channel: discord.TextChannel):
        try:
            message = await channel.send("Getting map info...")
            # this should be the full path
            file_path = self.custom_map_dictionary[arg.replace("\"", "")]
            file_name = os.path.basename(file_path)
            title = self.master_map_list[file_name]['title']
            author = self.master_map_list[file_name]['author']
            description = self.master_map_list[file_name]['description']
            await self.attempt_to_sendRL('rp map ' + file_name.replace(".udk", ""))
            message_str = ("Map sent to game:\n\n" +
                "*file: " + file_name + "*\n"
                "**" + title + "**\n" +
                "**By: " + author + "**\n\n" + description)
            await message.edit(content=message_str)
        except Exception as e:
            await message.edit(content="Sorry, I couldn't find that map :(")
    
    async def attempt_to_host(self, channel: discord.TextChannel, bypass=False):
        if bypass or not self.players_connected:
            if self.vote_listing:
                await self.vote_listing[0].delete()
                self.vote_listing = None
            await self.attempt_to_sendRL("rp host")
            self.match_request_message = await channel.send("Game will attempt to host...")
        else:
            need_to_pass_vote = max(2, math.ceil(self.players_connected / 2))
            message = await channel.send(
                "There are still players in the match!\n" +
                "Either have all players leave and ask to host again or have " +
                str(need_to_pass_vote) + " players vote to pass by reacting to this message.")
            await message.add_reaction(VOTE_TO_PASS_EMOTE)
            self.vote_listing = (message, need_to_pass_vote)
            

    async def handle_mutators(self, argv: list, channel: discord.TextChannel):
        self.stop_adding_reactions = False
        if len(argv) > 2:
            argv[2] = argv[2].replace("\"", "")
            for key in MUTATORS.keys():
                if argv[2].lower() == key.lower() or argv[2].lower() == MUTATORS[key]['alt_name'].lower():
                    argv[2] = key
                    break
            if len(argv) > 3:
                argv[3] = argv[3].replace("\"", "")
                # default or default name
                if argv[3].lower() == "default" or ('Default' in MUTATORS[argv[2]] and argv[3].lower() == MUTATORS[argv[2]]['Default'].lower()):
                    await self.attempt_to_sendRL("rp mutator " + argv[2] + " \\\"\\\"")
                    await self.clear_active_messages()
                    await channel.send("Sent mutator to game")
                # direct key matching (they have to be devs to know this... but I'll leave it in here I guess)
                elif argv[3].lower() in (string.lower() for string in MUTATORS[argv[2]]):
                    await self.attempt_to_sendRL("rp mutator \"" + argv[2] + "\" \"" + argv[3] + "\"")
                    await self.clear_active_messages()
                    await channel.send("Sent mutator to game")
                # else detect if arg3 is of the variant name to some key
                else:
                    # check if it's just a matching term to one of the raw values
                    found = argv[3].lower() in (val.lower() for val in MUTATORS[argv[2]]['values'])
                    # if not we can check the translations made
                    if not found:
                        for key in MUTATOR_VALUE_DICTIONARY.keys():
                            if argv[3].lower() == MUTATOR_VALUE_DICTIONARY[key].lower():
                                argv[3] = key
                                found = True
                                break
                    if found:
                        # success
                        await self.attempt_to_sendRL("rp mutator \"" + argv[2] + "\" \"" + argv[3] + "\"")
                        await self.clear_active_messages()
                        await channel.send("Sent mutator to game")
                    else:
                        await channel.send("Sorry I didn't understand that...")
                        # call back message down to the point where we didn't understand it to reload the prompt
                        await self.handle_mutators([argv[0], argv[1], argv[2]], channel)
            else:
                # print the values
                options = ""
                emoji = 0
                for value in MUTATORS[argv[2]]['values']:
                    if value == "Default":
                        if "Default" in MUTATORS[argv[2]]:
                            value = MUTATORS[argv[2]]['Default']
                    else:
                        value = MUTATOR_VALUE_DICTIONARY[value]
                    options += EMOTE_OPTIONS[emoji] + " " + value + "\n"
                    emoji += 1
                while(self.in_reactions):
                    # I can't control the scheduler and I'm too lazy to put a mutex on something like discord bots
                    time.sleep(0.5)
                message = await channel.send("Options for mutator " + MUTATORS[argv[2]]['alt_name'] + " are:\n" + options)
                self.in_reactions = True
                for i in range(0, emoji):
                    if self.active_mutator_messages:
                        await self.clear_active_messages()
                    if self.stop_adding_reactions or not self.in_reactions:
                        await message.delete()
                        return
                    if self.current_reaction:
                        if self.current_reaction.message.id == message.id:
                            await message.delete()
                            self.in_reactions = False
                            await self.handle_reaction(self.current_reaction, bypass=True, mutator=argv[2])
                            return
                        else:
                            self.current_reaction = None
                    await message.add_reaction(EMOTE_OPTIONS[i])
                self.in_reactions = False
                self.active_mutator_messages.append((message, argv[2]))
        else:
            # print the mutators
            mutators_per_message = math.ceil(len(MUTATORS.keys()) / MUTATOR_MESSAGES)
            keys = list(MUTATORS.keys())
            mutator_index = 0
            prompt = "Availible mutators are:\n"
            for message_index in range(0, MUTATOR_MESSAGES):
                reactions = []
                options = ""
                for i in range(mutator_index, mutator_index + mutators_per_message):
                    if mutator_index < len(MUTATORS.keys()):
                        options += MUTATORS[keys[mutator_index]]['emote'] + " " + MUTATORS[keys[i]]['alt_name'] + "\n"
                        reactions.append(MUTATORS[keys[mutator_index]]['emote'])
                        mutator_index += 1
                    else:
                        break
                message = await channel.send(prompt + options)
                self.active_mutator_messages.append((message, None))
                # this boolean helps main undestand what scope it's tasks are in
                # since this is scheduling and not multithreading
                self.in_reactions = True
                for emote in reactions:
                    if self.stop_adding_reactions or not self.in_reactions:
                        await message.delete()
                        return
                    if self.current_reaction:
                        if self.current_reaction.message.id == message.id:
                            await self.clear_active_messages()
                            await message.delete()
                            self.in_reactions = False
                            await self.handle_reaction(self.current_reaction, bypass=True)
                            return
                        else:
                            self.current_reaction = None
                    await message.add_reaction(emote)
                self.in_reactions = False
                prompt = "More mutators:\n"

    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.user.User):
        # if bot is tracking messages
        if int(self.bot_id) != user.id:
            self.current_reaction = reaction
        if (self.active_mutator_messages or self.vote_listing) and int(self.bot_id) != user.id:
            # check if reaction is on one of the bots messages
            await self.handle_reaction(reaction)

    async def handle_reaction(self, reaction: discord.reaction.Reaction, bypass=False, mutator=None):
        # check if this is about the host voting
        if self.vote_listing and reaction.message.id == self.vote_listing[0].id:
            if reaction.count > self.vote_listing[1]:
                await self.attempt_to_host(reaction.message.channel, bypass=True)
        # otherise it probably about the mutators
        else:
            is_my_message = False
            for active_message, mutator_category in self.active_mutator_messages:
                if reaction.message.id == active_message.id:
                    is_my_message = True
                    mutator = mutator_category # TODO add break
                    break
            # this is fine since the reaction is actually
            # saved in on_reaction_add for earlier anaylsis
            if is_my_message or bypass:
                arg = str(reaction)
                arg2 = None
                for key in MUTATORS.keys():
                    if arg == MUTATORS[key]['emote']:
                        arg = key
                        break
                    elif arg in EMOTE_OPTIONS:
                        arg2 = MUTATORS[mutator]['values'][EMOTE_OPTIONS.index(arg)]
                        arg = mutator
                        break
                await self.clear_active_messages()
                # rebuild the command equivalent based on reactions
                argv = [" ", "mutator"]
                if arg:
                    argv.append(arg)
                if arg2:
                    argv.append(arg2)
                await self.handle_mutators(argv, reaction.message.channel)

    async def clear_active_messages(self):
        # I don't know why I need both flags, 
        # it seems redundant but it didnt' work without it
        self.stop_adding_reactions = True
        while self.active_mutator_messages:
            self.in_reactions = False
            message, mutator = self.active_mutator_messages.pop()
            await message.delete()

    async def list_maps(self, message: discord.Message):
        description = "Here is a list of all the maps I can host:"
        try:
            embed_var = discord.Embed(
                description=description)
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
                        description=description)
                    value_str = ""
                    description = "Here are some more maps that I can host:"
                    embed_var = discord.Embed(
                        description=description)
                value_str += "\"" + map_key + "\"\n"
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
        desc = ""
        has_permission = self.has_permission(message)
        if has_permission:
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
                " **host**\n"+
                "\tStart up a game! If players are in game it will instead vote:\n\tArgs: None\n\n"+
                self.base_command +
                " killRL*\n"+
                "\tTerminates rocket league:\n\tArgs: None\n\n"+
                self.base_command +
                " link-plugin*\n"+
                "\tAttempts to start communication with custom plugin:\n\tArgs: None\n\n"+
                self.base_command +
                " lock*\n"+
                "\tThis will make all commands require permissions:\n\tArgs: None\n\n"+
                self.base_command +
                " **map**\n"+
                "\tPicks map to be hosted:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
                self.base_command +
                " mapd*\n"+
                "\tLoad map from directory listing:\n\tArgs: [full path of map]\n\n"+
                self.base_command +
                " **list-maps**\n"+
                "\tList all the availble maps:\n\tArgs: None\n\n"+
                self.base_command +
                " **mutator**\n"+
                "\tSend mutators to the game (text and reaction controlled):\n\tArgs: [mutator][value]\n\n"+
                self.base_command +
                " permit*\n"+
                "\tAdds a role to permssions:\n\tArgs: [role id]\n\n"+
                self.base_command +
                " **preset**\n"+
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
                " **start**\n"+
                "\tStarts application and loads plugins:\n\tArgs: None\n\n"+
                self.base_command +
                " unbind*\n"+
                "\tUnbinds 'scoreboard' message:\n\tArgs: None\n\n"+
                self.base_command +
                " unlock*\n"+
                "\tThis will undo the lock command:\n\tArgs: None\n\n"+
                self.base_command +
                " **help**\n"+
                "\tPrints list of commands:\n\tArgs: None\n\n"
            )
        else:
            desc = (
                self.base_command +
                " host\n"+
                "\tStart up a game! If players are in game it will instead vote:\n\tArgs: None\n\n"+
                self.base_command +
                " map\n"+
                "\tPicks map to be hosted:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
                self.base_command +
                " maps\n"+
                "\tList all the availble maps:\n\tArgs: None\n\n"+
                self.base_command +
                " mutator\n"+
                "\tSend mutators to the game (text and reaction controlled):\n\tArgs: [mutator][value]\n\n"+
                self.base_command +
                " preset\n"+
                "\tLoad in a predefined preset:\n\tArgs: [name of preset (case sensitve)]\nWIP\n\n"+
                self.base_command +
                " start\n"+
                "\tStarts application and loads plugins (usefull if a map caused a crash):\n\tArgs: None\n\n"+
                self.base_command +
                " help\n"+
                "\tPrints list of commands:\n\tArgs: None\n\n"
            )
        embed_var = discord.Embed(title="Commands", description=desc)
        if self.admin_locked and not has_permission:
            embed_var.add_field(name="Commands are currently locked", value="You'll need a person with special access to unlock them", inline=False)
        embed_var.add_field(name="commands with a *", value="can only be executed by those with permissions", inline=False)
        embed_var.add_field(name="ALL COMMAND ARGUMENTS MUST BE SINGLE WORD", value="if there is whitespace, use double qoutes -> \"my arg\"", inline=False)
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
        # go to main menu to avoid bugs where in match for super long time
        if self.idle_counter > IDLE_COUNT:
            await self.attempt_to_sendRL("hcp menu")
            self.idle_counter = 0
        # idle counter iterator
        if self.players_connected == 0:
            self.idle_counter += 1
        else:
            self.idle_counter = 0
        # updated the host request if it's found and a match is online
        if self.match_request_message and self.match_data:
            await self.match_request_message.edit(
                content = "Match is online!\n" +
                    "IP: ||" + self.ip_address + "||\n" +
                    "Pass: ||" + self.game_password + "||"
            )
            self.match_request_message = None
        # scoreboard stuff
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
            self.players_connected = len(self.match_data['teams'][0]['players']) + len(self.match_data['teams'][1]['players'])
            match_time = timedelta(seconds=int(self.match_data['matchlength']))
            passed_time = timedelta(seconds=float(self.match_data['gametime']))

            if self.match_data['overtime']:
                title += " - Over Time"
            if (not self.match_data['gameactive']) and self.match_data['gametime']:
                title = "Game Inactive"
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
            self.idle_counter = 0
            title = "OFFLINE - Game is not running"
            if self.companion_plugin_connected:
                title = "ONLINE - In Main Menu"
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

    def has_permission(self, message: discord.Message) -> bool:
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
