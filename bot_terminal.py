from bot import HostingBot
from pprint import pprint
from threading import Thread
import sys
import re
import pickle

class BotTerminal:
    """
    This is used to run in parallel to the bot to manually control some of it's features in real time

    If someone wanted, since files are save pretty often you can call a subprocess and retain 
    most of the functionallity with all the printouts and debugging tools

    This includes shutting the bot down safely
    """
    terminal_running = False
    str_pattern = "\'.*?\'|\".*?\"|\(.*?\)|[a-zA-Z\d\_\*\-\\\+\/\[\]\?\!\@\#\$\%\&\=\~\`]+"
    pattern = None

    def __init__(self, playbot: HostingBot):
        self.bot = playbot
        self.pattern = re.compile(self.str_pattern)
        self.execute = {
            'help': self.help_command,
            'real-info': self.print_bot_command,
            'saved-info': self.print_file_contents_command,
            'save-timer': self.adjust_save_timer_command,
            'pass': self.force_msg_success_command,
            'fail': self.force_msg_failed_command,
            'del-msg': self.del_msg_command,
            'rename-base': self.rename_base_cmd_command,
            'permit-role': self.add_permitted_role_command,
            'remove-role': self.remove_permitted_role_command,
            'max-time': self.adjust_max_time_command,
            'reaction': self.adjust_reaction_command,
            'ping': self.adjust_ping_role_command,
            'count': self.adjust_threshold_command,
            'save-now': self.save_bot_now_command,
            'exit': None
        }

    def start(self):
        """
        Begins bot on main thread and starts terminal on another

        'exit' will close terminal thread
        """
        Thread(target=self.__start_terminal_thread).start()
        self.bot.initialize()
    
    def __start_terminal_thread(self):
        if not self.bot.print_statements_enabled():
            # Thread(target=self.__terminal_loop).start()
            self.__terminal_loop()
        else:
            print("Bot has print statements enabled! this will interfere w/ the terminal")

    def __terminal_loop(self):
        self.terminal_running = True
        print("Terminal started\n")
        while self.terminal_running:
            print(">", end="", flush=True)
            line = sys.stdin.readline().rstrip()
            if line == 'exit':
                self.terminal_running = False
            else:
                argv = self.__handle_line(line)
                self.__commands(argv)
            print()
        print("Terminal closed")
        print("Joining bot thread and enabling print outs")
        self.bot.enable_print_statements(True)
        self.bot.join_bot_thread()

    def __handle_line(self, line: str):
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

    def __commands(self, argv: list):
        command = argv[0]
        if command in self.execute.keys():
            try:
                self.execute[command](argv)
            except Exception as e:
                print("Command failed:")
                print(e)
        else:
            print("Sorry, I didn't understand that")
            self.execute['help'](argv)
        print()

    def help_command(self, argv: list):
        print("Availible commands are:")
        for k in self.execute.keys():
            print('\t', k)
        print("use the '-h' flag on a command to see further instructions")
        print("To quit terminal, simply type `exit` (This does not shutdown the bot).")

    def adjust_threshold_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer and adjusts the max\n",
                "number participants require to issue a ping\n",
                "Example: count 7\n",
                "Would move the threshold/count to 7 before pinging"
            )
        else:
            try:
                self.bot.threshold = int(argv[1])
            except Exception as e:
                print("Command failed:")
                print(e)

    def adjust_ping_role_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer and adjusts who will be pinged\n",
                "Example: ping 123456\n",
                "Would now ping the role associated to '123456'"
            )
        else:
            try:
                self.bot.pinging = int(argv[1])
            except Exception as e:
                print("Command failed:")
                print(e)

    def adjust_reaction_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes a string and adjusts the emoji used to react with\n",
                "Example: reaction :123:\n",
                "Would now ask users to react with the emoji :123:"
            )
        else:
            try:
                #strips outer qoutes
                if '\'' in argv[1][0]:
                    argv[1] = argv[1][1:-1]
                elif '\"' in argv[1][0]:
                    argv[1] = argv[1][1:-1]
                self.bot.reaction_str = argv[1]
            except Exception as e:
                print("Command failed:")
                print(e)

    def adjust_max_time_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer in seconds and\n",
                "adjusts the max future event time\n",
                "Example: max-time 120\n",
                "Would now set the maximum forward time to 2 minutes"
            )
        else:
            try:
                self.bot.max_event_time = int(argv[1])
            except Exception as e:
                print("Command failed:")
                print(e)

    def rename_base_cmd_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes a string and adjusts base command to use in discord\n",
                "Example: rename-base \"!Let's Play\"\n",
                "Would now require all commands on discord to start with `!Let's Play`"
            )
        else:
            try:
                if '\'' in argv[1][0]:
                    argv[1] = argv[1][1:-1]
                elif '\"' in argv[1][0]:
                    argv[1] = argv[1][1:-1]
                self.bot.base_command = argv[1]
            except Exception as e:
                print("Command failed:")
                print(e)

    def remove_permitted_role_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer that represents a role and removes it\n",
                "from the roles the bot would listen too\n",
                "Example: remove-role 123456\n",
                "Would now remove the role `123456`"
            )
        else:
            try:
                role_id = int(argv[1])
                if role_id in self.bot.permitted_roles:
                    self.bot.permitted_roles.pop(self.bot.permitted_roles.index(role_id))
            except Exception as e:
                print("Command failed:")
                print(e)

    def add_permitted_role_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer that represents a role and adds it\n",
                "into the roles the bot would listen too\n",
                "Example: permit-role 123456\n",
                "Would now add the role `123456`"
            )
        else:
            try:
                role_id = int(argv[1])
                if role_id not in self.bot.permitted_roles:
                    self.bot.permitted_roles.append(role_id)
            except Exception as e:
                print("Command failed:")
                print(e)

    def force_msg_failed_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer that represents a msg id\n",
                "and immediately assumes time has elapsed\n",
                "Example: fail 123456\n",
                "Would now fail the message `123456`"
            )
        else:
            try:
                msg_id = int(argv[1])
                for i in range(0, len(self.bot.running_msgs)):
                    if self.bot.running_msgs[i].get_msg().id == msg_id:
                        self.bot.running_msgs[i].delay = 0
            except Exception as e:
                print("Command failed:")
                print(e)

    def force_msg_success_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer that represents a msg id\n",
                "and immediately assumes it was successful\n",
                "Example: pass 123456\n",
                "Would now pass the message `123456` and ping"
            )
        else:
            try:
                msg_id = int(argv[1])
                for i in range(0, len(self.bot.running_msgs)):
                    if self.bot.running_msgs[i].get_msg().id == msg_id:
                        self.bot.running_msgs[i].threshold = 0
            except Exception as e:
                print("Command failed:")
                print(e)

    def adjust_save_timer_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command takes an integer in seconds and adjusts the frequency of saving\n",
                "Example: save-timer 30\n",
                "Would now set the bot to save every 30 seconds"
            )
        else:
            try:
                self.bot.save_timer = int(argv[1])
            except Exception as e:
                print("Command failed:")
                print(e)
    
    def print_file_contents_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command pretty-prints the contents of the save file\n",
                "Example: save-info\n",
                "Would print the contents"
            )
        else:
            try:
                pprint(pickle.load(open(self.bot.file, 'rb')))
            except Exception as e:
                print("Command failed:")
                print(e)

    def save_bot_now_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command writes the current bot info into the save file\n",
                "Example: save-now\n",
                "Would save the bot status immediately"
            )
        else:
            try:
                self.bot.try_saving()
            except Exception as e:
                print("Command failed:")
                print(e)

    def print_bot_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command pretty-prints class variables of the bot\n",
                "Example: real-info\n",
                "Would print the contents"
            )
        else:
            try:
                pprint(self.bot.get_bot_info())
            except Exception as e:
                print("Command failed:")
                print("\t", e)

    def del_msg_command(self, argv: list):
        if len(argv) > 1 and argv[1] == '-h':
            print(
                "This command drops a currently-tracked message\n",
                "Example: del-msg 123456\n",
                "Would delete the message `123456` from the tracking list"
            )
        else:
            try:
                msg_id = int(argv[1])
                for rmsg in self.bot.running_msgs:
                    if isinstance(rmsg, ReactiveMessage) and rmsg.get_msg().id == msg_id:
                        self.bot.running_msgs.pop(self.bot.running_msgs.index(rmsg))
                        print("Removed msg", msg_id)
            except Exception as e:
                print("Command failed:")
                print(e)
        
                