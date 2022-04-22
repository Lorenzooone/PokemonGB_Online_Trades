# PokemonGB_Online_Trades
This is an overlay for Pokémon Red/Blue/Yellow and Gold/Silver/Crystal which aims at adding Online Trading support.

Two interfaces are currently available. One for a GB Link Cable to USB Adapter, and the other for BGB.

It focuses on safety for the end Device's data (more on that later) and speed (by having some optimizations put in place).

## Features
### 2-Player Trade
Register to a server's room and trade with another player, just like you would in person!

#### Comunication Modes
The program supports both a Synchronized mode, in which a single byte at a time is exchanged (just like when using the original Link Cable), and a Buffered mode.

When using Buffered mode, the players have to initialize a fake trade (which the program will automatically close) in order to prepare their own data.
Once the data is ready, a single transfer will send it to the other player, who will be able to start the actual trade using it.
This comunication mode, although slower, can be safer if one of the players has connectivity issues.

### Pool Trade
Exchange your Pokémon with one at random from the Server's Pool, and make it available for other players!

### Safety First
Each byte which is sent to your Device is cleaned using Sanity Checks. They make sure your game doesn't crash due to another player's actions.

Said checks can also be removed, if one so chooses.

## Installing the prerequisite packages
Run `pip install websockets`.

If you are using the USB adapter, also run:

`pip install pyUSB` and `pip install winusbcdc`.

## Using the GB Link Cable to USB Adapter
Run `python ./usb_trading.py`.
If the adapter is inserted, it should be detected.

## Using BGB
Run `python ./emulator_trading.py`.
Once you're out of the program's menu, and you have started BGB, you can then left click on the actively running BGB window, and click Link->Connect->Ok.
It should connect to the emulator, once that is done.
