import os
from os import kill, path
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


class PlayBot(discord.Client):

    bot_id = 1234567890
    my_id = 1234567890
    bakkesmod_server = 'ws://127.0.0.1:9002'
    rcon_password = 'password'
    token = None
    rl_path = ""

    rl_pid = None
    companion_plugin_connected = False
    reconnect = False;

    str_pattern = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"
    
    file = "./bot_stuff.p"
    background_timer = 15 # how frequently background tasks will be executed
    permitted_roles = []
    base_command = "!play"
    roles = []
    
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
        self.token = os.getenv('DISCORD_TOKEN')
        self.print_statements = print_statements

    def initialize(self):
        Thread(target=self.__background_loop).start()
        Thread(target=self.between_plugin_callback).start()
        self.run(self.token)

    def join_bot_thread(self):
        if self.__bot_thread and isinstance(self.__bot_thread, Thread):
            self.__bot_thread.join()

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
        if argv[0] == self.base_command:
            if argv[1] == 'help':
                await self.help_command(message)
            elif argv[1] == 'permit':
                # if permissions are empty or ...
                if (not self.permitted_roles) or self.has_permission(message):
                    await self.set_permit_command(message)
                else:
                    await self.permission_failure(message)
            elif argv[1] == 'remove':
                if self.has_permission(message):
                    await self.remove_permit_command(message)
                else:
                    await self.permission_failure(message)
            elif argv[1] == 'startRL':
                if self.has_permission(message):
                    await self.start_game()
                else:
                    await self.permission_failure(message)
            elif argv[1] == 'killRL':
                if self.has_permission(message):
                    await self.kill_game()
                else:
                    await self.permission_failure(message)
            elif argv[1] == 'console':
                if self.has_permission(message):
                    await self.pass_to_console(argv, message)
                else:
                    await self.permission_failure(message)
            elif argv[1] == 'link-plugin':
                if self.has_permission(message):
                    self.reconnect = True
                else:
                    await self.permission_failure(message)
            else:
                await self.help_command(argv, True)

    async def remove_permit_command(self, message: discord.Message):
        cont = str(message.content)
        try:
            role_id = int(cont.replace(self.base_command + ' remove ', ''))
            self.permitted_roles.pop(self.permitted_roles.index(role_id))
            await message.channel.send("I will no longer listen to the " + self.get_role(role_id).name +" role")
        except Exception as e:
            await message.channel.send("Sorry, I couldn't undersand that")

    async def pass_to_console(self, argv: list, message: discord.message):
        if self.has_permission(message):
            command = ""
            for i in range(2, len(argv)):
                command += (argv[i] + " ")
            try:
                await self.attempt_to_sendRL(command)
            except Exception as e:
                self.print("Command failed")
                self.print(e)
        else:
            await self.permission_failure(message)

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
            " ping [role id]\n"+
            "\tsets which role will be pinged\n\n"+
            self.base_command +
            " count [integer]\n"+
            "\tsets how many players will be needed to make a ping\n\n"+
            self.base_command +
            " permit [role id]\n"+
            "\tsets which roles can control my settings\n\n"+
            self.base_command +
            " remove [role id]\n"+
            "\tremoves which roles can control my settings\n\n"+
            self.base_command +
            " reaction [emoji]\n"+
            "\tsets which emoji will used\n\n"+
            self.base_command +
            " [d:h:m]\n"+
            "\tschedules an event 'd:h:m' time from now and if enough players wanna join in, it'll ping! Formats are: `d:h:m`, `h:m`, and `m`\n\n"+
            self.base_command +
            " help\n"+
            "\tget the list of commands"
        )
        embed_var = discord.Embed(title="Commands", description=desc)
        msg = None
        if error_response:
            msg = "Sorry, I didn't understand that :("
        await message.channel.send(content=msg, embed=embed_var)

    async def attempt_to_sendRL(self, message: str) -> WebSocketClientProtocol:
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
            if self.reconnect:
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
                        # We'll run this indefinitely basically
                        while self.companion_plugin_connected:
                            # query command for info
                            await websocket.send('hcp status')
                            # get back info
                            game_status = await websocket.recv()
                            game_status = game_status.replace("$%", "\"")
                            if (game_status != "ERR"):
                                test = json.loads(str(game_status))
                                self.print("current match data:")
                                self.print(test)
                                # TODO do stuff with status info
                            else:
                                # not in game
                                # update status
                                pass
                            time.sleep(15)
                except Exception as e:
                    self.print("Failed to connect to RL")
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
