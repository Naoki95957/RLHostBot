from bot import HostingBot
from bot_terminal import BotTerminal

def main():
    bot = HostingBot(print_statements=True)
    bot.initialize()
    # TODO reincorperate backdoor terminal at some point
    # terminal = BotTerminal(bot).start()
    
if __name__ == "__main__":
    main()