# RLHostBot

### A python based discord bot that in tandom with rocket league and some mods will allow an on demand hosting service for you're copy of the game on a machine. 

The idea is that you have another computer or server with a copy of rocket league, bakkes and some plugins installed, and then this bot running with your discord token and information.


## Installation

### Files

  #### config.env

  You'll need to configure an env file and an example is provided:
  ```
  BOT_ID=this is the id of the bot
  MY_ID=this is the id of the owner (basically going to serve as an admin)
  DISCORD_TOKEN=secret token provided form discord
  BAKKES_SERVER=ws://127.0.0.1:9002 (ws[WebSocket]://IP:port, the provided is default)
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
  the best we go.

  If you wish to change the rcon password, you can change this with bakkesconsole:
  `rcon_password "new password"`

  #### rcon_commands.cfg
  I've attached what commands I recommend whitelisting however you can do what you want.
  The provided file is under `sample_files`
  You will at the least need to add:
  ```
  hcp
  rp
  rp_custom_path
  ```

  #### Plugins
  You will need to install the 2 provided plugins for now as well. 
  You will need to manually install `RLHBotCompanion.dll` and `moddedRP.dll` located
  in the `plugins` folder I provided. To do this put it in your `...bakkesmod/plugins`
  folder. Eventually Rocket Plugin will support hosting from command but until this
  all that we have is a quick mod I wrote up. The other plugin I might plublish
  sooner or later but it is also needed to get status updates on the game.
  If you don't have cpp installed you will likely need this too:
  https://aka.ms/vs/16/release/vc_redist.x64.exe

### Python
To install all the necessary packages run:
`pip install -r requirements.txt`

If you wish to run the map_info.json scraper install all the necessary packages there too:
`pip install -r scraper_reqs.txt`

Note: if you are using a virtual python env like conda (such as I am using),
you may need to install some of these packages via anaconda:
- `conda install -c anaconda pywin32`
- `conda install -c conda-forge selenium`
- `conda install -c anaconda beautifulsoup4`
- etc...

python 3.9 doesn't appear to be compatible so get 3.7 or 3.8

### Running the bot
Assuming everything is configured and ready to go:
- [x] Rocket League
- [x] Bakkesmod
- [x] config.env
- [x] Python + packages 
- [x] Reconfigured rcon whitelist
- [x] RLHBotCompanion.dll
- [x] moddedRP.dll
- [x] It's advisable to intsall netcode due to some maps needing it

You should be able to run `python main.py` or `python bot.py` for now.
I plan on having a terminal like back door but until then, you can run in debug mode
to change the values on the fly if needed. 

There is a provided scraper for map information gathering as it'll will occasionally be needed to add maps and what not
but is not necessary if you plan on adding a limited number of maps. These files, including a chrome driver for version 89
is included in `scraper_stuff`

map_info.json and your maps directory should be in sync. Without them it'll just list path/file.
Map files are assumed all `.udk` files
