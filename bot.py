from datetime import timedelta
import os
from os import path
from discord.ext import tasks
from pathlib import Path
import win32gui, win32con
import shutil
import threading
import subprocess
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
# 
# TODO show all presets
# read presets bakkes? or scratch that and make your own?
# commands:
# list presets
#   lists aval presets
# 
# TODO big feature: playlists? maps + presets?
# make map + preset, ... ?
# so make is the command
# map is manditory, preset is optional
# and ',' indicates next term?
# 
# read playlists? edit them?

# fix fugly code

# how many seconds you would like to get updates
# on the scoreboard
PLUGIN_FREQUENCY = 5

# how long game will idle with no players before going to main menu 
# time would be IDLE_COUNT * PLUGIN_FREQUENCY seconds
# so 120 would be 10min
IDLE_COUNT = 120

# Will always attempt to link the plugin
# it's best to leave this on
ALWAYS_RECONNECT = True

# used to divide up the massive amount of mutators into multiple messages
# Minimum is 2! this is bc the max reactions you can have is 20
# and there are 24 reactions in total needed
MUTATOR_MESSAGES = 2

# This is used to let the bot know when is a safe time to call on rcon and bakkes
# to start injecting.
# This is also kind of arbitrary since it depends on fast you load the game
GAME_LOAD_TIME = 20

# I'm adding support for both udk and upk files. 
# Hosting with either doesn't appear to matter; so may as well take them both
# MAP_EXTENSION_TYPE = ".udk"

# TODO Move the into a JSON maybe?
# "Mutator" : : {"emote" : ":emoji:", "values" : ["value0", "value1", ...], "val_names" : ["<meaning>", ...]}
MUTATORS = {
    # TAGame is custom written and modded in
    "TAGame" : {
        "alt_name" : "Game Mode",
        "emote" : "🎮",
        "values" : [ "TA0", "TA1", "TA2", "TA3", "TA5", "TA6", "TA7"],
        "val_names" : ["Soccar", "Hoops", "Snow Day", "Rumble", "Dropshot", "Heatseeker", "Gridiron"],
    },
    "FreePlay" : {
        "alt_name" : "Free Play",
        "emote" : "🆓",
        "values" : ["Default", "FreePlay"],
        "val_names" : ["Disable Free Play", "Enable Freeplay"],
    },
    "GameTimes" : {
        "alt_name" : "Match Length",
        "emote" : "🕐",
        "values" : ["Default", "10Minutes", "20Minutes", "UnlimitedTime"],
        "val_names" : ["5 Minutes", "10 minutes", "20 minutes", "Unlimited"],
    },
    "GameScores" : {
        "alt_name" : "Max Score",
        "emote" : "🗜️",
        "values" : ["Default", "Max1", "Max3", "Max5", "Max7", "UnlimitedScore"],
        "val_names" : ["Default", "1 Goal", "3 Goals", "5 Goals", "7 Goals"],
    },
    "OvertimeRules" : {
        "alt_name" : "Overtime",
        "emote" : "⏲️",
        "values" : ["Default", "Overtime5MinutesFirstScore", "Overtime5MinutesRandom"],
        "val_names" : ["Unlimited", "+5 Max, First Score", "+5 Max, Random Team"],
    },
    "MaxTimeRules" : {
        "alt_name" : "Max Time Limit",
        "emote" : "⏰",
        "values" : ["Default", "MaxTime11Minutes"],
        "val_names" : ["Default", "11 Minutes"],
    },
    "MatchGames" : {
        "alt_name" : "Serires Length",
        "emote" : "🏁",
        "values" : ["Default", "3Games", "5Games", "7Games"],
        "val_names" : ["Unlimited", "3 Games", "5 Games", "7 Games"],
    },
    "GameSpeed" : {
        "alt_name" : "Game Speed",
        "emote" : "🎚️",
        "values" : ["Default", "SloMoGameSpeed", "SloMoDistanceBall"],
        "val_names" : ["Default", "Slo-mo", "Time Warp"],
    },
    "BallMaxSpeed" : {
        "alt_name" : "Ball Max Speed",
        "emote" : "🏎️",
        "values" : ["Default", "SlowBall", "FastBall", "SuperFastBall"],
        "val_names" : ["Default", "Slow", "Fast", "Super Fast"],
    },
    "BallType" : {
        "alt_name" : "Ball Type",
        "emote" : "🏀",
        "values" : ["Default", "Ball_CubeBall", "Ball_Puck", "Ball_BasketBall", "Ball_Haunted", "Ball_BeachBall"],
        "val_names" : ["Default", "Cube", "Puck", "Basketball", "Haunted Ball", "Beach Ball"],
    },
    "BallGravity" : {
        "alt_name" : "Ball Gravity",
        "emote" : "🪂",
        "values" : ["Default", "LowGravityBall", "HighGravityBall", "SuperGravityBall"],
        "val_names" : ["Default", "Low", "High", "Super High"],
    },
    "BallWeight" : {
        "alt_name" : "Ball Physics",
        "emote" : "🪃",
        "values" : ["Default", "LightBall", "HeavyBall", "SuperLightBall", "MagnusBall", "MagnusBeachBall"],
        "val_names" : ["Default", "Light", "Heavy", "Super Light", "Curve", "Beach Ball Curve"],
    },
    "BallScale" : {
        "alt_name" : "Ball Size",
        "emote" : "💗",
        "values" : ["Default", "SmallBall", "MediumBall", "BigBall", "GiantBall"],
        "val_names" : ["Default", "Small", "Medium", "Large", "Gigantic"],
    },
    "BallBounciness" : {
        "alt_name" : "Ball Bounciness",
        "emote" : "🏓",
        "values" : ["Default", "LowBounciness", "HighBounciness", "SuperBounciness"],
        "val_names" : ["Default", "Low", "High", "Super High"],
    },
    "MultiBall" : {
        "alt_name" : "Number of Balls",
        "emote" : "🤡",
        "values" : ["Default", "TwoBalls", "FourBalls", "SixBalls"],
        "val_names" : ["One", "Two", "Four", "Six"],
    },
    "Boosters" : {
        "alt_name" : "Boost Amount",
        "emote" : "🔥",
        "values" : ["Default", "NoBooster", "UnlimitedBooster", "SlowRecharge", "RapidRecharge"],
        "val_names" : ["Default", "No Boost", "Unlimited", "Recharge (slow)", "Recharge (fast)"],
    },
    "Items" : {
        "alt_name" : "Rumble",
        "emote" : "🌪️",
        "values" : [
            "Default", "ItemsMode", "ItemsModeSlow",
            "ItemsModeBallManipulators", "ItemsModeCarManipulators", "ItemsModeSprings",
            "ItemsModeSpikes", "ItemsModeRugby", "ItemsModeHauntedBallBeam"
        ],
        "val_names" : [
            "None", "Default", "Slow", "Civilized", "Destruction Derby",
            "Spring Loaded", "Spikes Only", "Rugby", "Haunted Ball Beam"
        ],
    },
    "BoosterStrengths" : {
        "alt_name" : "Boost Strength",
        "emote" : "💪",
        "values" : ["Default", "BoostMultiplier1_5x", "BoostMultiplier2x", "BoostMultiplier10x"],
        "val_names" : ["1x", "1.5x", "2x", "10x"],
    },
    "Gravity" : {
        "alt_name" : "Gravity",
        "emote" : "🍂",
        "values" : ["Default", "LowGravity", "HighGravity", "SuperGravity", "ReverseGravity"],
        "val_names" : ["Default", "Low", "High", "Super High"],
    },
    "Demolish" : {
        "alt_name" : "Demolish",
        "emote" : "🪖",
        "values" : ["Default", "NoDemolish", "DemolishAll", "AlwaysDemolishOpposing", "AlwaysDemolish"],
        "val_names" : ["Default", "Disabled", "Friendly Fire", "On Contact", "On Contact (FF)",],
    },
    "RespawnTime" : {
        "alt_name" : "Respawn Time",
        "emote" : "🐈",
        "values" : ["Default", "TwoSecondsRespawn", "OnceSecondRespawn", "DisableGoalDelay"],
        "val_names" : ["3 Seconds", "2 Seconds", "1 Second", "Disable Goal Reset"],
    },
    "BotLoadouts" : {
        "alt_name" : "Bot Loadouts",
        "emote" : "🎒",
        "values" : ["Default", "RandomizedBotLoadouts"],
        "val_names" : ["Default", "Random"],
    },
    "AudioRules" : {
        "alt_name" : "Audio",
        "emote" : "🔊",
        "values" : ["Default", "HauntedAudio"],
        "val_names" : ["Default", "Haunted"],
    },
    "GameEventRules" : {
        "alt_name" : "Game Event",
        "emote" : "🎲",
        "values" : ["Default", "HauntedGameEventRules", "RugbyGameEventRules"],
        "val_names" : ["Default", "Haunted", "Rugby"],
    }
}

# These are default maps in the game and can be loaded with the custom mapd command
DEFAULT_MAPS = {
    "ARCtagon" : "ARC_P",
    "Forbidden Temple" : "CHN_Stadium_P",
    "Mannfield (Night)" : "EuroStadium_Night_P",
    "Mannfield" : "EuroStadium_P",
    "Mannfield (Stormy)" : "EuroStadium_Rainy_P",
    "Farmstead (Night)" : "Farm_Night_P",
    "Urban Central (Haunted)" : "Haunted_TrainStation_P",
    "Dunk House" : "HoopsStadium_P",
    "Pillars" : "Labs_CirclePillars_P",
    "Cosmic (Old)" : "Labs_Cosmic_P",
    "Cosmic (New)" : "Labs_Cosmic_V4_P",
    "Double Goal (Old)" : "Labs_DoubleGoal_P",
    "Double Goal (New)" : "Labs_DoubleGoal_V2_P",
    "Octagon (New)" : "Labs_Octagon_02_P",
    "Octagon (Old)" : "Labs_Octagon_P",
    "Underpass" : "Labs_Underpass_P",
    "Utopia Retro" : "Labs_Utopia_P",
    "Tokyo Underpass" : "NeoTokyo_P",
    "Neo Tokyo" : "NeoTokyo_Standard_P",
    "Beckwith Park (Midnight)" : "Park_Night_P",
    "Beckwith Park" : "Park_P",
    "Beckwith Park (Stormy)" : "Park_Rainy_P",
    "Core 707" : "ShatterShot_P",
    "DFH Stadium (Stormy)" : "Stadium_Foggy_P",
    "DFH Stadium" : "Stadium_P",
    "DFH Stadium (Snowy)" : "Stadium_Winter_P",
    "DFH Stadium (Race Day)" : "Stadium_Race_Day_P",
    "Urban Central (Dawn)" : "TrainStation_Dawn_P",
    "Urban Central (Night)" : "TrainStation_Night_P",
    "Urban Central" : "TrainStation_P",
    "AquaDome" : "Underwater_P",
    "Utopia Coliseum (Dusk)" : "UtopiaStadium_Dusk_P",
    "Utopia Coliseum" : "UtopiaStadium_P",
    "Utopia Coliseum (Snowy)" : "UtopiaStadium_Snow_P",
    "Badlands (Night)" : "Wasteland_Night_P",
    "Badlands" : "Wasteland_P",
    "Starbase ARC" : "arc_standard_P",
    "Salty Shores" : "beach_P",
    "Salty Shores (Night)" : "beach_night_P",
    "Champions Field (Day)" : "cs_day_P",
    "Rivals Arena" : "cs_hw_P",
    "Champions Field" : "cs_P",
    "Champions Field (NFL)" : "BB_P",
    "Mannfield (Snowy)" : "eurostadium_snownight_P",
    "Farmstead" : "farm_P",
    "Neon Fields" : "music_P",
    "DFH Stadium (Day)" : "stadium_day_P",
    "Throwback Stadium (Snowy)" : "throwbackhockey_P",
    "Throwback Stadium" : "throwbackstadium_P",
    "Wasteland (Night)" : "wasteland_Night_S_P",
    "Wasteland" : "wasteland_s_P"
}

# List of presests here so that the bot can help account for case sensitivty
# TODO refactor this to access the cfg files and handle presets there
PRESETS = [
    "Default",
    "Beach Ball",
    "Boomer Ball",
    "Cubic",
    "Demolition",
    "Ghost Hunt",
    "Inverted Ball",
    "Moon Ball",
    "Snow Day",
    "Spike Rush",
    "Time Warp",
]

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
REPEAT_MUTATOR_EMOTE = "🔁"

# This json is in the form:
# "file.udk" : {"title":"my custom map", "author":"by me", "description":"don't use plz"}
MAP_LIST = "./map_info.json"

URL_REGEX = r"<[a-zA-Z]+:.*?>"

STR_COMMAND_PATTERN = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"

RL_EXECUTABLE = "./Binaries/Win64/RocketLeague.exe"

RL_PC_CONSOLE = "./TAGame/CookedPCConsole"

class HostingBot(discord.Client):

    # stuff for dotenv to setup
    bot_id = 1234567890
    my_id = 1234567890
    bakkesmod_server = ''
    rcon_password = ''
    token = None
    rl_path = ""
    custom_path = ""
    ip_address = ""
    game_password = ""

    # things that the bot will self-set up
    rl_pid = None
    url_embed_count = -1
    companion_plugin_connected = False
    reconnect = False
    players_connected = 0
    idle_counter = 0
    vote_listing = None
    url_pattern = None
    master_map_list = None
    members_list = None
    bot_file_path = None

    # bot/match global stuff
    active_mutator_messages = []
    stop_adding_reactions = False
    in_reactions = False
    current_reaction = None
    admin_locked = False
    match_request_message = None
    last_mutator_message = None
    admin_t_lock = threading.Lock()
    
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
        self.command_pattern = re.compile(STR_COMMAND_PATTERN)
        self.url_pattern = re.compile(URL_REGEX)
        self.bot_id = os.getenv('BOT_ID')
        self.my_id = os.getenv('MY_ID')
        self.bakkesmod_server = os.getenv('BAKKES_SERVER')
        self.rcon_password = os.getenv('RCON_PASSWORD')
        self.rl_path = os.getenv('RL_PATH')
        self.custom_path = os.getenv('CUSTOM_PATH')
        self.token = os.getenv('DISCORD_TOKEN')
        self.game_password = os.getenv('GAME_PASSWORD')
        self.print_statements = print_statements
        self.bot_file_path =  str(Path(str(__file__)).parents[0])
        self.master_map_list = json.load(open(MAP_LIST))

    def initialize(self):
        Thread(target=self.__background_loop).start()
        Thread(target=self.between_plugin_callback).start()
        self.index_custom_maps()
        self.update_companion_message.start()
        self.run(self.token)

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
        self.members_list = self.get_all_members()
        await HostingBot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.listening, name="others play Rocket League"))

    async def on_message(self, message: discord.message.Message):
        if message.author.id == int(self.bot_id) or self.base_command not in str(message.content):
            return
        if isinstance(message.channel, discord.DMChannel):
            if self.base_command in str(message.content):
                await message.channel.send("I only listen from the server.")
            return
        try:
           await self.handle_command(self.tokenize(message.content), message)
        except Exception as e:
            # await message.channel.send("I didn't understand that")
            pass
        self.try_saving()
        
    
    ######################################################### 
    #                                                       #
    #                       COMMANDS                        #
    #                                                       #
    #########################################################
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
                        await self.set_permit_command(argv, message)
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
                        with self.admin_t_lock:
                            self.admin_locked = True
                        await message.channel.send("Editing commands locked")
                    else:
                        await self.permission_failure(message)
                # unlock reverses the lock -> to allow players to use the bot again
                elif argv[1] == 'unlock':
                    if self.has_permission(message):
                        with self.admin_t_lock:
                            self.admin_locked = False
                        await message.channel.send("Editing commands unlocked")
                    else:
                        await self.permission_failure(message)
                # lists maps known to the bot
                elif argv[1] == 'list-maps':
                    if self.is_admin_locked() and not self.has_permission(message):
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
                        await self.remove_permit_command(argv, message)
                    else:
                        await self.permission_failure(message)
                # attach scoreboard to the channel it's called on
                elif argv[1] == 'bind':
                    if self.has_permission(message):
                        await self.bind_message(message)
                    else:
                        await self.permission_failure(message)
                # limit the number of embeds shown on descriptions
                elif argv[1] == 'url-embeds':
                    if self.has_permission(message):
                        try:
                            value = int(argv[2])
                            if value < -1:
                                raise Exception("Value out of bounds")
                            self.url_embed_count = value
                            if value == -1:
                                await message.channel.send("I will allow all embeds on descriptions")
                            else:
                                await message.channel.send("I will only allow " + str(value) + " embeds on descriptions")
                        except Exception as e:
                            await message.channel.send(
                                "I didn't understand that, I need a natrual number " +
                                "between -1 (unlimited), and 10" 
                            )
                    else:
                        await self.permission_failure(message)
                # drops the attachment to any currently set 'scoreboard' message
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
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        message = await message.channel.send("Working on it ...")
                        await self.start_game()
                        # we have no refrence as to when the game loads
                        time.sleep(GAME_LOAD_TIME)
                        # minimize window to help lower-end gpus
                        win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_MINIMIZE)
                        await self.attempt_to_sendRL("plugin unload RocketPlugin")
                        time.sleep(1)
                        await self.attempt_to_sendRL("plugin load moddedRP")
                        time.sleep(1)
                        # TODO may not need to do this if I publish my plugin
                        # will need to rename the plugin for sure lol
                        await self.attempt_to_sendRL("plugin load RLHBotCompanion")
                        time.sleep(1)
                        # starts up rocket plugin GUI
                        await self.attempt_to_sendRL("hcp start_rp")
                        time.sleep(1)
                        # binds rocket plugin path with our maps
                        await self.attempt_to_sendRL("rp_custom_path " + self.custom_path.replace("\\", "/"))
                        time.sleep(1)
                        self.reconnect = True
                        await message.edit(content="Done")
                # mutator passing
                elif argv[1] == 'mutator':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        try:
                            await self.clear_active_messages()
                            await self.handle_mutators(argv, message.channel)
                        except Exception as e:
                            # exceptions will be printed based on code logic, no need for it here
                            pass 
                # preset passing
                # TODO eventually this will be like the mutator selection
                elif argv[1] == 'preset':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        try:
                            understood = False
                            for preset in PRESETS:
                                if argv[2].replace("\"", "").lower() == preset.lower():
                                    argv[2] = "\"" + preset + "\""
                                    understood = True
                                    break
                            if understood:
                                await self.attempt_to_sendRL("rp preset " + argv[2])
                                await message.channel.send("Sent preset to game")
                            else:
                                await message.channel.send("Sorry, I couldn't find that preset")
                        except Exception as e:
                            await message.channel.send("Sorry I didn't understand that")
                # selects the map and send it to rl
                elif argv[1] == 'restart':
                    if self.has_permission(message):
                        await self.handle_command([argv[0], 'killRL'], message)
                        time.sleep(1)
                        await self.handle_command([argv[0], 'start'], message)
                    else:
                        await self.permission_failure(message)
                # selects the map and sends it to rl
                # also prints the selected map info
                elif argv[1] == 'map':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        await self.send_selected_map(argv[2], message.channel)
                # selects the map, loads it, and sends it to rl
                # also prints the selected map info
                elif argv[1] == 'load-map':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        await self.send_selected_map(argv[2], message.channel, True)
                # selects the map, loads it, and sends it to rl
                # also prints the selected map info
                elif argv[1] == 'restore-labs':
                    if self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        shutil.copy(
                                os.path.join(self.bot_file_path, "./sample_files/Labs_Underpass_P.upk"),
                                os.path.join(self.rl_path, os.path.join(RL_PC_CONSOLE, "Labs_Underpass_P.upk"))
                            )
                        await message.channel.send("Underpass has been restored")
                # attempts to start up the match with the given settings
                elif argv[1] == 'host':
                    if not self.companion_plugin_connected:
                        await message.channel.send("RL is not running")
                    elif self.is_admin_locked() and not self.has_permission(message):
                        await message.channel.send("Sorry, the commands are locked right now")
                    else:
                        await self.attempt_to_host(message.channel, bypass=self.has_permission(message))
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
                            await self.pass_to_console(argv, message)
                            await message.channel.send("Sent instructions, may or may not have been recieved")
                        else:
                            await self.permission_failure(message)
                # sets up the ip that the host will relay
                elif argv[1] == 'setIP':
                    if self.has_permission(message):
                        self.ip_address = str(argv[2]).replace("\"", "")
                        await message.channel.send("IP address is now set up as: " + self.ip_address)
                    else:
                        await self.permission_failure(message)
                # link companion plugin for info
                elif argv[1] == 'link-plugin':
                    if self.has_permission(message):
                        self.reconnect = True
                        await message.channel.send("Will attempt to connect to game")
                    else:
                        await self.permission_failure(message)
                else:
                    await self.help_command(argv, True)

    async def send_selected_map(self, arg: str, channel: discord.TextChannel, swap=False):
        """
        This selects a map to be loaded in game

        Args:
            arg (str): the map name/file-name
            channel (discord.TextChannel): used for sendback
            swap (bool, optional): It says to swap it on underpass or not. Defaults to False.
        """
        try:
            message = await channel.send("Getting map info...")
            arg = arg.replace("\"", "")
            # these 2 loops correct for casing
            # if the name matches
            map_name = ""
            if (arg.lower() in (name.lower() for name in DEFAULT_MAPS.keys())):
                for name in DEFAULT_MAPS.keys():
                    if arg.lower() == name.lower():
                        arg = DEFAULT_MAPS[name]
                        map_name = name
            # if it matches the raw file name
            if arg.lower() in (raw_name.lower() for raw_name in DEFAULT_MAPS.values()):
                for val in DEFAULT_MAPS.values():
                    if arg.lower() == val.lower():
                        await self.attempt_to_sendRL("rp mapd " + val)
                        message = await message.edit(content=("Sent map " + map_name + " to the game."))
                        if swap:
                            await message.channel.send(
                                "I just loaded the map normally.\n" + 
                                "Why would I load I standard map with the underpass map???")
                        return
            # this should be the full path
            # this checks the map listing we indexed on init
            if self.master_map_list and not arg.startswith("z-"):
                file_path = self.custom_map_dictionary[arg]
                file_name = os.path.basename(file_path)
                title = self.master_map_list[file_name]['title']
                author = self.master_map_list[file_name]['author']
                description = self.master_map_list[file_name]['description']
                source = ""
                if 'source' in self.master_map_list[file_name]:
                    source = "***Info from: <{0}>***\n".format(self.master_map_list[file_name]["source"])
                if swap:
                    cooked = os.path.join(self.rl_path, RL_PC_CONSOLE)
                    shutil.copy(file_path, os.path.join(cooked, "Labs_Underpass_P.upk"))
                    await self.attempt_to_sendRL('rp mapd Labs_Underpass_P')
                else:
                    basename = file_name.replace(".udk", "")
                    basename = basename.replace(".upk", "")
                    await self.attempt_to_sendRL('rp map ' + basename)
                embed_counter = 0
                matches = re.findall(self.url_pattern, description)
                for i in range(0, len(matches)):
                    if embed_counter < self.url_embed_count  or self.url_embed_count < 0:
                        embed_counter += 1
                        url = matches[i]
                        description = description.replace(url, url[1:-1])
                header = "Map sent to game:\n"
                if swap: 
                    header = "Map loaded in game as Underpass:\n"
                message_str = ( header +
                    "**" + title + "**\n" +
                    "**By: " + author + "**\n" + 
                    "*file: " + file_name + "*\n" + source +"\n" + description)
                message = await message.edit(content=message_str)
            else:
                message_str = ("Map sent to game. I have no info on the map however:\n"
                    "***file: " + self.custom_map_dictionary[arg.replace("\"", "")] + "***")
                message = await message.edit(content=message_str)
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
        """
        helper function that manages mutator selection

        If argv is incomplete, it'll walk the user thru it
        """
        SUCCESS_MESSAGE = (
            "Sent mutator to game. If you wish to send " + 
            "another you can react with the " + REPEAT_MUTATOR_EMOTE + " emote")

        self.stop_adding_reactions = False
        if len(argv) > 2:
            argv[2] = argv[2].replace("\"", "")
            for key in MUTATORS.keys():
                if argv[2].lower() == key.lower() or argv[2].lower() == MUTATORS[key]['alt_name'].lower():
                    argv[2] = key
                    break
            if len(argv) > 3:
                argv[3] = argv[3].replace("\"", "")
                successful_message = None
                # default or default name
                if argv[3].lower() == "default" or (argv[3].lower() == MUTATORS[argv[2]]['val_names'][0].lower()):
                    await self.attempt_to_sendRL("rp mutator " + argv[2] + " \\\"\\\"")
                    await self.clear_active_messages()
                    successful_message = await channel.send(SUCCESS_MESSAGE)
                # direct key matching (they have to be devs to know this... but I'll leave it in here I guess)
                elif argv[3].lower() in (string.lower() for string in MUTATORS[argv[2]]):
                    # The game mode isn't exactly a mutator so it needs a different command sent
                    if argv[2].lower() == "TAGame" or argv[2] == "Game Mode":
                        await self.attempt_to_sendRL("rp mode \"" + argv[3] + "\"")
                        await self.clear_active_messages()
                        successful_message = await channel.send(SUCCESS_MESSAGE)
                    else:
                        await self.attempt_to_sendRL("rp mutator \"" + argv[2] + "\" \"" + argv[3] + "\"")
                        await self.clear_active_messages()
                        successful_message = await channel.send(SUCCESS_MESSAGE)
                # else detect if arg3 is of the variant name to some key
                else:
                    # check if it's just a matching term to one of the raw values
                    found = argv[3].lower() in (val.lower() for val in MUTATORS[argv[2]]['values'])
                    # if not we can check the translations made
                    if not found:
                        for key in MUTATORS[argv[2]]['val_names']:
                            if argv[3].lower() == key.lower():
                                argv[3] = key
                                found = True
                                break
                    # successful match
                    if found:
                        # The game mode isn't exactly a mutator so it needs a different command sent
                        if argv[2].lower() == "TAGame".lower() or argv[2] == "Game Mode".lower():
                            await self.attempt_to_sendRL("rp mode \"" + argv[3] + "\"")
                            await self.clear_active_messages()
                            successful_message = await channel.send(SUCCESS_MESSAGE)
                        else:
                            await self.attempt_to_sendRL("rp mutator \"" + argv[2] + "\" \"" + argv[3] + "\"")
                            await self.clear_active_messages()
                            successful_message = await channel.send(SUCCESS_MESSAGE)
                    else:
                        await channel.send("Sorry I didn't understand that...")
                        # call back message down to the point where we didn't understand it to reload the prompt
                        await self.handle_mutators([argv[0], argv[1], argv[2]], channel)
                if successful_message:
                    self.last_mutator_message = successful_message
                    await successful_message.add_reaction(REPEAT_MUTATOR_EMOTE)
            else:
                # print the values
                options = ""
                val_index = 0
                for value in MUTATORS[argv[2]]['values']:
                    value = MUTATORS[argv[2]]['val_names'][val_index]
                    options += EMOTE_OPTIONS[val_index] + " " + value + "\n"
                    val_index += 1
                while(self.in_reactions):
                    # I can't control the scheduler and I'm too lazy to put a mutex on something like discord bots
                    time.sleep(0.5)
                message = await channel.send("Options for mutator " + MUTATORS[argv[2]]['alt_name'] + " are:\n" + options)
                self.in_reactions = True
                for i in range(0, val_index):
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
            prompt = "Available mutators are:\n"
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
   
    async def list_maps(self, message: discord.Message):
        """
        Lists all maps found int the directory after having indexed the maps

        Args:
            message (discord.Message): used for sendback
        """
        description = "Here is a list of all the maps I can host:"
        try:
            embed_var = discord.Embed(
                description=description)
            value_str = ""
            extras = False
            keys = list(self.custom_map_dictionary.keys())
            keys.sort()
            name = "Maps"
            for map_key in keys:
                # there is a 1024 char limit on value for embed fields
                if len(value_str + map_key + "\n") > 1023:
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
    
    async def remove_permit_command(self, argv: list, message: discord.Message):
        """
        Removes role from list of permitted roles

        Args:
            argv (list of str): gets args, only needs argv[2] for role
            message (discord.Message): used to sendback
        """
        try:
            role_id = int(argv[2])
            self.permitted_roles.pop(self.permitted_roles.index(role_id))
            await message.channel.send("I will no longer listen to the " + self.get_role(role_id).name +" role")
        except Exception as e:
            await message.channel.send("Sorry, I couldn't undersand that")

    async def bind_message(self, message: discord.Message):
        """
        This is used to affix the 'scoreboard' message to some channel

        Args:
            message (discord.Message): used for sendback
        """
        self.binded_message = await message.channel.send("Binding...")
        self.binded_message_ID = self.binded_message.id
        self.binded_message_channel = self.binded_message.channel.id
        self.try_saving()

    async def pass_to_console(self, argv: list, message: discord.message):
        """
        This allows you to send a command directly to bakkesconsole

        If you want to send an str see `attempt_to_sendRL`

        Args:
            argv (list): your args from discord
            message (discord.message): used for sendback
        """
        command = ""
        for i in range(2, len(argv)):
            command += (argv[i] + " ")
        try:
            await self.attempt_to_sendRL(command)
        except Exception as e:
            self.print("Command failed")
            self.print(e)

    async def set_permit_command(self, argv: list, message: discord.Message):
        """
        Adds a role to permitted roles

        Args:
            argv (list of str): gets args, only needs argv[2] for role
            message (discord.Message): used to sendback
        """
        try:
            role_id = int(argv[2])
            self.permitted_roles.append(role_id)
            await message.channel.send("I will listen to the " + self.get_role(role_id).name +" role when they command me to :)")
        except Exception as e:
            await message.channel.send("Sorry, I couldn't undersand that")

    async def start_game(self):
        """
        Starts up rocket league exe
        """
        self.print("Starting RL")
        subprocess.Popen(os.path.join(self.rl_path, RL_EXECUTABLE))

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

    async def help_command(self, message: discord.Message, error_response=False):
        """
        Prints a giant list of commands
        It does do a little bit of logic and shows what the user has permission for

        Args:
            message (discord.Message): user for sendback
            error_response (bool, optional): adds error response if this is what that's for. Defaults to False.
        """
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
                " **load-map**\n"+
                "\tPicks map to be hosted on underpass:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
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
                " **restore-labs**\n"+
                "\tRestores the underpass map to original:\n\tArgs: None\n\n"+
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
                " url-embeds*\n"+
                "\tThis changes the number of embeds on a description message:\n\tArgs: [integer]\n\n"+
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
                " load-map\n"+
                "\tPicks map to be hosted on underpass:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
                self.base_command +
                " map\n"+
                "\tPicks map to be hosted:\n\tArgs: [name of map (if there is a gap use quotes)]\n\n"+
                self.base_command +
                " list-maps\n"+
                "\tList all the availble maps:\n\tArgs: None\n\n"+
                self.base_command +
                " mutator\n"+
                "\tSend mutators to the game (text and reaction controlled):\n\tArgs: [mutator][value]\n\n"+
                self.base_command +
                " preset\n"+
                "\tLoad in a predefined preset:\n\tArgs: [name of preset (case sensitve)]\nWIP\n\n"+
                self.base_command +
                " restore-labs\n"+
                "\tRestores the underpass map to original:\n\tArgs: None\n\n"+
                self.base_command +
                " start\n"+
                "\tStarts application and loads plugins (usefull if a map caused a crash):\n\tArgs: None\n\n"+
                self.base_command +
                " help\n"+
                "\tPrints list of commands:\n\tArgs: None\n\n"
            )
        embed_var = discord.Embed(title="Commands", description=desc)
        if self.is_admin_locked() and not has_permission:
            embed_var.add_field(name="Commands are currently locked", value="You'll need a person with special access to unlock them", inline=False)
        embed_var.add_field(name="commands with a *", value="can only be executed by those with permissions", inline=False)
        embed_var.add_field(name="ALL COMMAND ARGUMENTS MUST BE SINGLE WORD", value="if there is whitespace, use double qoutes -> \"my arg\"", inline=False)
        msg = None
        if error_response:
            msg = "Sorry, I didn't understand that :("
        await message.channel.send(content=msg, embed=embed_var)

    ######################################################### 
    #                                                       #
    #                       REACTIONS                       #
    #                                                       #
    #########################################################
    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.user.User):
        # if bot is tracking messages
        # This is used and needed to kill
        # mutator messages if they are running
        if int(self.bot_id) != user.id:
            if self.is_admin_locked():
                # yes this is redundant but it's expensive and I only want to do this when I HAVE to
                allowed_members = []
                for member in self.members_list:
                    if member.top_role.id in self.permitted_roles:
                        allowed_members.append(member.id)
                if user.id in allowed_members:
                    self.current_reaction = reaction
                    # this is for the redo operation in mutator
                    if (
                        (self.last_mutator_message) and
                        reaction.message.id == self.last_mutator_message.id
                    ):
                        await self.handle_mutators(["", "mutator"], reaction.message.channel)
                    elif (self.active_mutator_messages or self.vote_listing) and int(self.bot_id) != user.id:
                        # check if reaction is on one of the bots messages
                        await self.handle_reaction(reaction)
                else:
                    await reaction.message.channel.send("Sorry <@{0}>, commands are locked right now".format(user.id))
            else:
                self.current_reaction = reaction
                # this is for the redo operation in mutator
                if (
                    (self.last_mutator_message) and
                    reaction.message.id == self.last_mutator_message.id
                ):
                    await self.handle_mutators(["", "mutator"], reaction.message.channel)
                elif (self.active_mutator_messages or self.vote_listing) and int(self.bot_id) != user.id:
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
                    mutator = mutator_category
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

    ######################################################### 
    #                                                       #
    #                       HELPERS                         #
    #                                                       #
    #########################################################

    def join_bot_thread(self):
        """
        this is used for the terminal but I haven't worked on that yet

        It's meant to join the threads
        """
        if self.__bot_thread and isinstance(self.__bot_thread, Thread):
            self.__bot_thread.join()

    def index_custom_maps(self):
        """
        This just indexes custom maps and puts them into a dictionary for future use

        This doesn't do the whole scraper thing, so that'll still need map_info.json
        built before it can be safely used.

        if you want to bypass all this stuff you can use `mapd` command in discord

        the format of the map_info.json is pretty simple and you can use this if you wanted to do a quick update:
        ```
        my_dict = json.load("./map_info.json")
        my_dict['newMap.udk'] = {"title": "my new map", "author":"prob not Leth", "description":"use unlimited boost"}
        payload = json.dump(my_dict)
        open("./map_info.json").write(payload)
        ```
        
        """
        map_index = {}
        # doesn't seem to like this
        # subprocess.Popen([sys.executable, "./map_scraper.py"])
        for root, dirs, files in os.walk(self.custom_path):
            for file in files:
                if file.endswith(".udk") or file.endswith(".upk"):
                    if self.master_map_list:
                        list_name = file
                        if file in self.master_map_list:
                            list_name = self.master_map_list[file]['title']
                        if (
                                list_name in map_index.keys() and
                                os.path.getsize(map_index[list_name]) == os.path.getsize(os.path.join(root, file))
                            ):
                            continue
                        while list_name and (list_name in map_index.keys()):
                            list_name = "z-" + os.path.basename(root) + "/" + file
                        map_index[list_name] = os.path.join(root, file)
                    else:
                        map_index[os.path.join(os.path.basename(root), file)] = os.path.join(root, file)
        self.custom_map_dictionary = map_index
        self.custom_map_dictionary.update(DEFAULT_MAPS)

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

    def is_admin_locked(self) -> bool:
        '''
         I'm using this mutex bc it didn't appear to work for me w/out it
        '''
        with self.admin_t_lock:
            return self.admin_locked

    async def clear_active_messages(self):
        """
            This is used to clean off all the mutator reactive messages since there can be a lot
        """
        # I don't know why I need both flags, 
        # it seems redundant but it didnt' work without it
        self.stop_adding_reactions = True
        while self.active_mutator_messages:
            self.in_reactions = False
            message, mutator = self.active_mutator_messages.pop()
            await message.delete()

    async def attempt_to_sendRL(self, message: str):
        """
        This sends a message to the bakkesconsole

        Args:
            message (str): your message
        """
        try:
            async with websockets.connect(self.bakkesmod_server, timeout=0.3) as websocket:
                await websocket.send('rcon_password ' + self.rcon_password)
                auth_status = await websocket.recv()
                assert auth_status == 'authyes'
                await websocket.send(message.encode())
                await websocket.close()
        except Exception as e:
            self.print("Failed to connect to RL")
            return

    @tasks.loop(seconds=PLUGIN_FREQUENCY)
    async def update_companion_message(self):
        """
        This is what the scoreboard runs on:
        It calls the plugin repeatedly expecting a json package:
        It then scans that package for players and determines if it is idle
        if the game is idle for some time, 
        it'll issue a command to go to the main menu

        if not, it assumes it's in the main menu

        if no response is detected, it is assumed that RL is offline
        """
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
            if self.admin_locked:
                await self.match_request_message.edit(content="Match is online! Details are locked right now.")
            else:
                pass_str = ""
                ip_addr = ""
                if not self.ip_address:
                    ip_addr = "ask admin where to connect"
                else:
                    ip_addr = self.ip_address
                if self.game_password:
                    pass_str = "Pass: ||" + self.game_password + "||"
                await self.match_request_message.edit(
                    content = "Match is online!\n" +
                        "IP: ||" + ip_addr + "||\n" +
                        pass_str
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
        """
        This is a helper function that formats the embed for the scoreboard

        Returns:
            discord.Embed: formated embed based on json package in `self.match_data`
        """
        if self.match_data:
            title = "Current Game"
            self.players_connected = len(self.match_data['teams'][0]['players']) + len(self.match_data['teams'][1]['players'])
            match_time = timedelta(seconds=int(self.match_data['matchlength']))
            passed_time = timedelta(seconds=round(float(self.match_data['gametime'])))

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
            # map name here appears to be based in the udk and has
            # nothing to do with file name or file location...
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
        """
        Another helper function; this is for `get_score_embed`
        This just sorts thru the teams and extracts the info
        
        Args:
            team (dict): a single team
        Returns:
            tuple: ("{team} - {score}", [player0, player1, ...])
        """
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
                                self.print(self.match_data)
                            else:
                                self.match_data = {}
                            time.sleep(PLUGIN_FREQUENCY)
                except Exception as e:
                    self.print("Failed to connect to RL")
                    self.companion_plugin_connected = False
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
        if not self.command_pattern:
            self.command_pattern = re.compile(STR_COMMAND_PATTERN)
        argv = []
        none_matched = True
        for match in re.finditer(self.command_pattern, line):
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
                self.url_embed_count = dictionary['url_embed_count']
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
        dictionary['url_embed_count'] = copy.deepcopy(self.url_embed_count)
        return dictionary

    def __background_loop(self):
        """
        This is used to simple auto save the bot state every few seconds or
        whatever you defined it as -> `self.background_timer`
        """
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
    bot = HostingBot(print_statements=True)
    bot.initialize()
    
if __name__ == "__main__":
    main()
