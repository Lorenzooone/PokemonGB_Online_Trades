#!/usr/bin/env python

import asyncio
import websockets
import threading
from time import sleep
from .gsc_trading_strings import GSCTradingStrings
from .gsc_trading_listener import GSCTradingListener

class WebsocketRunner (threading.Thread):
    """
    Class for running the websocket as a standalone piece.
    """
    SLEEP_TIMER = 0.01
    
    def __init__(self, menu, kill_function):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.hll = GSCTradingListener()
        self.kill_function = kill_function
        self.ws = WebsocketClient(menu.server[0], menu.server[1], kill_function)

    def run(self):
        self.ws.get_pool(self.hll)

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

    async def consumer_handler(websocket, other):
        async for message in websocket:
            response = other.process_received_data(message, websocket, preparer=True)
            if response[2] is not None:
                other.to_send = response[2]
                while other.to_send is not None:
                    await asyncio.sleep(WebsocketClient.SLEEP_TIMER)
            
    async def producer_handler(websocket, other):
        while True:
            if other.to_send is not None:
                await websocket.send(other.to_send)
                other.to_send = None
            else:
                await asyncio.sleep(WebsocketClient.SLEEP_TIMER)

    async def handler(websocket, other, loop):
        consumer_task = loop.create_task(WebsocketClient.consumer_handler(websocket, other))
        producer_task = loop.create_task(WebsocketClient.producer_handler(websocket, other))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    async def server_connect(other, loop):
        """
        Function which tries to get a websocket connection to the server.
        """
        try:
            async with websockets.connect("ws://"+ WebsocketClient.host +":" + str(WebsocketClient.port) + "/pool", ping_interval=None) as websocket:
                await WebsocketClient.handler(websocket, other, loop)
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
    
    def get_pool(self, other):
        """
        Calls server_connect and waits for it.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(WebsocketClient.server_connect(other, loop))