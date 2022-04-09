#!/usr/bin/env python

import asyncio
import websockets
from gsc_trading_strings import GSCTradingStrings

class WebsocketClient:
    """
    Class for connecting to the websocket server.
    """
    host = None
    port = None
    SLEEP_TIMER = 0.01
    
    def __init__(self, host, port, kill_function):
        WebsocketClient.host = host
        WebsocketClient.port = port
        WebsocketClient.kill_function = kill_function

    async def get_peer_server_connect(serving_host, serving_port, room):
        """
        Function which tries to get a P2P connection to another client
        by registering to a room in the websocket server.
        :param room: Room in which the client registers.
        """
        try:
            async with websockets.connect("ws://"+ WebsocketClient.host +":" + str(WebsocketClient.port) + "/link/"+str(room).zfill(5), ping_interval=None) as websocket:
                await websocket.send(serving_host + ":" + str(serving_port))
                data = await websocket.recv()
                return data
        except Exception as e:
            print(GSCTradingStrings.websocket_client_error_str, str(e))
            WebsocketClient.kill_function()
    
    def get_peer(self, serving_host, serving_port, room):
        """
        Calls get_peer_server_connect and waits for it.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(WebsocketClient.get_peer_server_connect(serving_host, serving_port, room))