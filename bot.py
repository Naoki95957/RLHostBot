import os
from os import path
from datetime import datetime, timedelta
import discord
import pickle
import copy
import pytz
import time
import re
from threading import Thread
from dotenv import load_dotenv
from pprint import pprint


class PlayBot(discord.Client):

    bot_id = 1234567890
    my_id = 1234567890

    str_pattern = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"
    
    # day * hours * minutes * seconds
    max_event_time = 14 * 24 * 60 * 60 # 604800s

    file = "./bot_stuff.p"
    save_timer = 15 # how frequently the save file will be written
    permitted_roles = []
    role_format = "<@&{0}>"
    threshold = 3
    pinging = "someone"
    base_command = "!play"
    formated_prompt_str = "Who wants to join in and play in {0} days, {1}hrs and {2}m?\nWe need {3} or more people to react with {4} to make it happen!\n\n"
    formated_success_str = "Yo, <@&{0}>! Let's get some games going!"
    formated_failed_str = "Sorry! Looks like we didn't get enough players for this time."
    reaction_str = "⚽"
    running_msgs = []
    roles = []
    
    print_statements = False

    __bot_thread = None

    def __init__(self, print_statements=False):
        super().__init__()
        load_dotenv()
        self.pattern = re.compile(self.str_pattern)
        self.bot_id = os.getenv('BOT_ID')
        self.my_id = os.getenv('MY_ID')
        self.print_statements = print_statements

    def initialize(self):
        Thread(target=self.__save_loop).start()
        self.run(os.getenv('DISCORD_TOKEN'))

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
        # Setting `Playing ` status
        # await Playbot.change_presence(self, activity=discord.Game(name="a game"))

        # # Setting `Streaming ` status
        # await Playbot.change_presence(self, activity=discord.Streaming(name="My Stream", url=my_twitch_url))

        # # Setting `Listening ` status
        await PlayBot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.listening, name="The beautiful sound of DSL"))
        # # Setting `Watching ` status
        # await Playbot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))


    async def on_message(self, message: discord.message.Message):
        cont = str(message.content)
        # Here begins a giant ugly list of command checking
        if message.author.id == self.bot_id or self.base_command not in cont:
            return
        try:
            argv = self.tokenize(message.content)
            if argv[0] == self.base_command:
                if argv[1] == 'help':
                    await self.help_command(message)
                elif argv[1] == 'ping':
                    await self.set_ping_command(message)
                elif argv[1] == 'permit':
                    await self.set_permit_command(message)
                elif argv[1] == 'remove':
                    await self.remove_permit_command(message)
                elif argv[1] == 'count':
                    await self.set_threshold_command(message)
                elif argv[1] == 'reaction':
                    await self.set_reaction_command(message)
                elif cont.startswith(self.base_command):
                    # This is the main command -> 'd:h:m'
                    await self.create_reactive_message_command(message)
        except Exception as e:
            pass
        self.try_saving()

    async def create_reactive_message_command(self, message: discord.Message):
        cont = str(message.content)
        if len(cont.split(' ')) > 1:
            try:
                time_str = cont.split(' ')[1]
                time_split = time_str.split(':')
                days = 0
                hrs = 0
                minutes = int(time_split[0])                    
                if len(time_split) == 2:
                    hrs = int(time_split[0])
                    minutes = int(time_split[1])
                elif len(time_split) > 2:
                    days = int(time_split[0])
                    hrs = int(time_split[1])
                    minutes = int(time_split[2])
                now = datetime.now(tz=pytz.timezone(BOT_TIME_ZONE))
                delta = timedelta(days=days, hours=hrs, minutes=minutes)
                now = now + delta
                delay_seconds = int(delta.total_seconds())
                if delay_seconds > self.max_event_time:
                    await message.channel.send("Sorry that's too far into the future!\n")
                    return
                embed_var = discord.Embed(
                    title="Let's Play!", 
                    description=self.formated_prompt_str.format(
                        delta.days, 
                        int(delta.seconds / (60 * 60)),
                        int(delta.seconds / 60) % 60,
                        self.threshold, 
                        self.reaction_str))
                embed_var.add_field(name='Pacific Time', value=now.strftime("%A\n%d/%m/%Y\n%I:%M %p"))
                now = now.astimezone(tz=pytz.timezone('US/Eastern'))
                embed_var.add_field(name='Eastern Time', value=now.strftime("%A\n%d/%m/%Y\n%I:%M %p"))
                now = now.astimezone(tz=pytz.timezone('Europe/Madrid'))
                embed_var.add_field(name='Central European Time', value=now.strftime("%A\n%d/%m/%Y\n%I:%M %p"))

                self.running_msgs.append(
                    ReactiveMessage(
                        message.channel, 
                        embed_var, 
                        self.reaction_str, 
                        self.formated_success_str.format(self.pinging), 
                        self.formated_failed_str, 
                        delay_seconds, 
                        self.threshold
                    )
                )
            except Exception as e:
                await message.channel.send(
                    "Sorry I couldn't understand that :(\n" +
                    "The defualt format is `" + self.base_command + "h:m`. You can use these formats: `d:h:m`, `h:m`, and `m`")
        else:
            await message.channel.send("<@" + str(message.author.id) + ">, there should be 2 arguments. EG: `!play 1:00` to play in 1hr")

    async def set_reaction_command(self, message: discord.Message):
        cont = str(message.content)
        if message.author.top_role.id in self.permitted_roles:
            try:
                temp = cont.replace(self.base_command + ' reaction ', '')
                await message.add_reaction(temp)
                self.reaction_str = temp
            except Exception as e:
                await message.channel.send("I can't use that emoji :(")
        else:
            await self.permission_failure(message)

    async def set_threshold_command(self, message: discord.Message):
        cont = str(message.content)
        if message.author.top_role.id in self.permitted_roles:
            try:
                self.threshold = int(cont.replace(self.base_command + ' count ', ''))
                await message.channel.send("I will ping when I see " + str(self.threshold) + " or more players moving forward :)")
            except Exception as e:
                await message.channel.send("Sorry I couldn't understand that :(")
        else:
            await self.permission_failure(message)

    async def remove_permit_command(self, message: discord.Message):
        cont = str(message.content)
        if message.author.top_role.id in self.permitted_roles:
            try:
                role_id = int(cont.replace(self.base_command + ' remove ', ''))
                self.permitted_roles.pop(self.permitted_roles.index(role_id))
                await message.channel.send("I will no longer listen to the " + self.get_role(role_id).name +" role")
            except Exception as e:
                await message.channel.send("Sorry, I couldn't undersand that")
        else:
            await self.permission_failure(message)

    async def set_permit_command(self, message: discord.Message):
        cont = str(message.content)
        if (not self.permitted_roles) or message.author.top_role.id in self.permitted_roles or message.author.id == int(self.my_id):
            try:
                role_id = int(cont.replace(self.base_command + ' permit ', ''))
                self.permitted_roles.append(role_id)
                await message.channel.send("I will listen to the " + self.get_role(role_id).name +" role when they command me to :)")
            except Exception as e:
                await message.channel.send("Sorry, I couldn't undersand that")
        else:
            await self.permission_failure(message)

    async def help_command(self, message: discord.Message):
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
        await message.channel.send(embed=embed_var)

    async def set_ping_command(self, message: discord.Message):
        cont = str(message.content)
        if message.author.top_role.id in self.permitted_roles:
            try:
                self.pinging = int(cont.replace(self.base_command + ' ping ', ''))
                name = "them"
                role = self.get_role(self.pinging)
                if role:
                    name = role.name
                await message.channel.send("I will ping " + name +" when the time comes :)")
            except Exception as e:
                await message.channel.send("Sorry, I couldn't undersand that")
        else:
            await self.permission_failure(message)

    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.user.User):
        # Checking reactions
        message = reaction.message
        for rmsg in self.running_msgs:
            if rmsg.is_complete():
                self.running_msgs.pop(self.running_msgs.index(rmsg))
            elif (
                    message.id == rmsg.get_msg().id 
                    and user.id != self.bot_id
                    and rmsg.get_threshold() <= reaction.count
                ):
                await rmsg.send_success_msg()
                rmsg.passed_threshold()
                self.running_msgs.pop(self.running_msgs.index(rmsg))

    async def permission_failure(self, message: discord.Message):
        """
        Helper function, just decides how to send a failure message
        """
        if self.permitted_roles:
            await message.channel.send("Sorry, you do not have permission <@" + str(message.author.id) + ">")
        else:
            await message.channel.send("Permissions must be set first! <@" + str(message.author.id) + ">")

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
                self.threshold = dictionary['threshold']
                self.base_command = dictionary['base_command']
                self.reaction_str = dictionary['reaction_str']
                self.pinging = dictionary['pinging']
                self.running_msgs = [reactive_message_builder(rmsg_dict, self.guilds) for rmsg_dict in dictionary['running_msgs']]
                self.save_time = dictionary['save_timer']
                self.max_event_time = dictionary['max_event_time']
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
        for rmsg in self.running_msgs:
            if rmsg.is_complete():
                self.running_msgs.pop(self.running_msgs.index(rmsg))
        dictionary = {}
        dictionary['permitted_roles'] = copy.deepcopy(self.permitted_roles)
        dictionary['threshold'] = copy.deepcopy(self.threshold)
        dictionary['base_command'] = copy.deepcopy(self.base_command)
        dictionary['reaction_str'] = copy.deepcopy(self.reaction_str)
        dictionary['pinging'] = copy.deepcopy(self.pinging)
        dictionary['running_msgs'] = copy.deepcopy([rmsg.to_dictionary() for rmsg in self.running_msgs])
        dictionary['save_timer'] = copy.deepcopy(self.save_timer)
        dictionary['max_event_time'] = copy.deepcopy(self.max_event_time)
        return dictionary

    def __save_loop(self):
        while True:
            time.sleep(self.save_timer)
            self.try_saving()

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

    def __del__(self):
        self.try_saving()


def main():
    bot = PlayBot(print_statements=True)
    
if __name__ == "__main__":
    main()
