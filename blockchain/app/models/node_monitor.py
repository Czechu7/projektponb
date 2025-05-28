
import asyncio
import json
from signalrcore.hub_connection_builder import HubConnectionBuilder
import logging
from concurrent.futures import Future
import argparse
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=5001)
args = parser.parse_args()

class NodeMonitor:
    def __init__(self, port,node_address = None, signalr_url="http://localhost:4999/blockchainhub"):
        self.port = args.port
        self.node_address = f"http://127.0.0.1:{self.port}"  
        self.hub_connection = HubConnectionBuilder()\
            .with_url(signalr_url)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            })\
            .build()
        self.node_statuses = {}
        self.is_connected = False
        
    async def start_monitoring(self):
        try:
            def handle_open():
                self.is_connected = True
                logger.info(f"Node {self.node_address} connected")

            def handle_close():
                self.is_connected = False
                logger.info("Connection closed")
                
            self.hub_connection.on_open(handle_open)
            self.hub_connection.on_close(handle_close)
            self.hub_connection.on_error(lambda data: logger.error(f"Connection error: {data}"))
            
            self.hub_connection.on("ReceiveNodeStatus", self.handle_node_status)
            self.hub_connection.on("ReceiveNewBlock", self.handle_new_block)
            
            while True:
                try:
                    if not self.is_connected:
                        future = self.hub_connection.start()
                        if isinstance(future, Future):
                            await asyncio.wrap_future(future)
                    
                    await self.report_status("active")
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Connection error, retrying: {e}")
                    self.is_connected = False
                    await asyncio.sleep(5)  
                    
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            
    async def report_status(self, status):
        if self.is_connected:
            try:
                future = self.hub_connection.send("UpdateNodeStatus", [self.node_address, status])
                if isinstance(future, Future):
                    await asyncio.wrap_future(future)
            except Exception as e:
                logger.error(f"Error in status reporting: {e}")
                self.is_connected = False
        
    async def broadcast_block(self, block_data):
        await self.hub_connection.send("BroadcastNewBlock", [self.node_address, json.dumps(block_data)])
        
    def handle_node_status(self, data):
            node_address, status = data
            self.node_statuses[node_address] = status
            print(f"Node {node_address} status: {status}")
    def get_node_status(self, node_address):
        return self.node_statuses.get(node_address, "unknown")
        
    def get_all_statuses(self):
        nodes = [f"http://localhost:{port}" for port in range(5001, 5006)]
        return {node: self.node_statuses.get(node, "unknown") for node in nodes}
    
    def handle_new_block(self, data):
        node_address, block_data = data
        print(f"New block from {node_address}: {block_data}")