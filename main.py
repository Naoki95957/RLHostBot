from bot import HostingBot
from bot_terminal import BotTerminal

def main():
    bot = HostingBot(print_statements=True)
    bot.initialize()
    # TODO reincorperate back terminal
    # terminal = BotTerminal(bot).start()
    
if __name__ == "__main__":
    main()