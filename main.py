from bot import PlayBot
from bot_terminal import BotTerminal

def main():
    bot = PlayBot(print_statements=True)
    bot.initialize()
    # TODO reincorperate back terminal
    # terminal = BotTerminal(bot).start()
    
if __name__ == "__main__":
    main()