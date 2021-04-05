Python bot that in tandom with rocket league and some mods will allow an on demand hosting service for you're copy of the game on a machine. 

The idea is that you have another computer or server with a copy of rocket league, bakkes and some plugins installed, and then this bot running with your discord token and information.

You'll need to configure an env file and an example is provided:
```
BOT_ID=this is the id of the bot
MY_ID=this is the id of the owner (basically going to serve as an admin)
DISCORD_TOKEN=secret token provided form discord
BAKKES_SERVER=ws://127.0.0.1:9002 (IP:port, the provided is default)
RCON_PASSWORD=password (rcon password, again this is default)
RL_PATH=(path to RL exe)
CUSTOM_PATH=(path to custom maps)
GAME_PASSWORD=(this is predefined at the moment)
```
Note: GAME_PASSWORD is the password to join the game
this is defined by you based on the game settings and isn't working via
plugins at the moment. To set up a password, start a local lan match with
a password, and that will save it. Ideally this will be removed and can be
auto-generated per match or defined by discord commands but for now this is
the best we go

To install all the necessary packages run:
`pip install -r requirements.txt`

If you wish to run the map_info.json scraper install all the necessary packages there too:
`pip install -r scraper_reqs.txt`

Note: if you are using a virtual python env like conda such as I am using
you may need to install some of these packages via anaconda:
`conda install -c anaconda pywin32`
`conda install -c conda-forge selenium`
`conda install -c anaconda beautifulsoup4`

python 3.9 doesn't appear to be compatible