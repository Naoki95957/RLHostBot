from bot import PlayBot
from bot_terminal import BotTerminal    

def main():
    bot = PlayBot(print_statements=True)
    bot.initialize()
    # terminal = BotTerminal(bot).start()
    
if __name__ == "__main__":
    main()