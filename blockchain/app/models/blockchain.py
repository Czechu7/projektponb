import time
import requests
import logging
import zlib
from .block import Block
import argparse
from .node_monitor import NodeMonitor
import threading

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=5001)
args = parser.parse_args()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MASTER_SERVER_IP = "127.0.0.1:4999"

class Blockchain:
    def __init__(self, difficulty=2):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions = []
        self.nodes = set()
        self.port = args.port
        self.node_address = f"http://127.0.0.1:{self.port}"  
        self.node_monitor = NodeMonitor(port=self.port, node_address=self.node_address)
        predefined_nodes = [
            "127.0.0.1:5001",
            "127.0.0.1:5002",
            "127.0.0.1:5003",
            "127.0.0.1:5004",
            "127.0.0.1:5005",
            "127.0.0.1:5006"
        ]

        self.consensus_threshold = len(predefined_nodes) // 2 + 1
        self.node_failures = {node: 0 for node in predefined_nodes}

        self.isSimulatedCrcError = False

        for node in predefined_nodes:
            self.register_node(node)

        # Auto start synchronization thread
        # threading.Thread(target=self.synchronize_with_network, daemon=True).start()
            # Auto start monitoring ping
            # threading.Thread(target=self.ping_nodes, daemon=True).start()
        threading.Thread(target=self.get_active_nodes, daemon=True).start()
        # threading.Thread(target=self.synchronize_after_start, daemon=True).start()

    def create_genesis_block(self):
        return Block(0, "0", "Genesis Block", time.time())

    async def start_monitoring(self):
        await self.node_monitor.start_monitoring()
        await self.node_monitor.report_status("active")
            
    def get_active_nodes(self):
        return self.node_monitor.get_all_statuses()
    
    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if 'data' not in transaction or 'crc' not in transaction:
            raise ValueError("Transaction must contain 'data' and 'crc' fields")

        # logger.info(f"[Port {self.port}] Adding transaction: {transaction}")

        if self.vote_on_transaction(transaction):
            self.pending_transactions.append(transaction)
            # logger.info(f"[Port {self.port}] Transaction {transaction} added successfully!")
            return True
        # logger.info(f"[Port {self.port}] Transaction {transaction} rejected!")
        logger.info(f"[Port {self.port}] Transaction rejected!")
        return False

    def mine_pending_transactions(self):
        block = Block(len(self.chain), self.get_latest_block().hash, self.pending_transactions)
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []

    def is_chain_valid(self, chain=None):
        chain = chain or self.chain
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def register_node(self, address):
        self.nodes.add(address)

    def register_node_in_network(self, address):
        print(f"[Port {self.port}] Registering node {address} in network")
        self.nodes.add(address)
        for node in self.nodes:
            try:
                requests.post(f'http://{node}/nodes/register', json={'nodes': [address]})
            except requests.exceptions.RequestException as e:
                logger.error(f"[Port {self.port}] Error registering node {address} in network): {e}")


    def remove_node(self, address):
        if address in self.nodes:
            self.nodes.remove(address)
            logger.info(f"[Port {self.port}] Node {address} removed from the network")

    def replace_chain(self):
        longest_chain = None
        max_length = len(self.chain)

        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Konwersja łańcucha na listę obiektów Block
                    chain = [Block(block['index'], block['previous_hash'], block['transactions'], block['timestamp']) for block in chain]
                    for block in chain:
                        block.hash = block.calculate_hash()

                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain
                        logger.info(f"[Port {self.port}] Found a longer chain from node {node} with length {length}")

            except requests.exceptions.RequestException as e:
                logger.error(f"[Port {self.port}] Error synchronizing with node {node}: {e}")

        if longest_chain:
            self.chain = longest_chain
            logger.info(f"[Port {self.port}] Blockchain synchronized with the longest chain from the network")
            return True
        else:
            logger.info(f"[Port {self.port}] No longer chain found, keeping the current chain")
            return False

    def vote_on_transaction(self, transaction):
        transaction_data = transaction['data']

        if self.isSimulatedCrcError:
            calculated_crc = '123123123123'
        else:
            calculated_crc = zlib.crc32(transaction_data.encode('utf-8'))

        if calculated_crc != transaction['crc']:
            # logger.info(f"[Port {self.port}] Transaction {transaction} rejected due to CRC mismatch!")
            logger.info(f"[Port {self.port}] Transaction rejected due to CRC mismatch!")
            return False

        votes = 0
        for node in self.nodes:
            response = requests.post(f'http://{node}/vote', json={'transaction': transaction})
            if response.status_code == 200 and response.json().get('vote') == 'yes':
                votes += 1
                # logger.info(f"[Port {self.port}] Node {node} voted YES for transaction {transaction}")
                logger.info(f"[Port {self.port}] Node {node} voted YES for transaction")
            else:
                # logger.info(f"[Port {self.port}] Node {node} voted NO for transaction {transaction}")
                logger.info(f"[Port {self.port}] Node {node} voted NO for transaction")

        if votes >= self.consensus_threshold:
            # logger.info(f"[Port {self.port}] Transaction {transaction} approved with {votes} votes")
            logger.info(f"[Port {self.port}] Transaction approved with {votes} votes")
        else:
            # logger.info(f"[Port {self.port}] Transaction {transaction} rejected with {votes} votes")
            logger.info(f"[Port {self.port}] Transaction rejected with {votes} votes")

        return votes >= self.consensus_threshold

    def synchronize_with_network(self):
        # time.sleep(10)  # Sleep 10 seconds
        longest_chain = None
        max_length = len(self.chain)

        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    chain = [Block(block['index'], block['previous_hash'], block['transactions'], block['timestamp']) for block in chain]
                    for block in chain:
                        block.hash = block.calculate_hash()

                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain
                        logger.info(f"[Port {self.port}] Found a longer chain from node {node} with length {length}")

            except requests.exceptions.RequestException as e:
                logger.error(f"[Port {self.port}] Error synchronizing with node {node}: {e}")

        if longest_chain:
            self.chain = longest_chain
            logger.info(f"[Port {self.port}] Blockchain synchronized with the longest chain from the network")
            return True
        else:
            logger.info(f"[Port {self.port}] No longer chain found, keeping the current chain")
            return False
        
    def synchronize_after_start(self):
        time.sleep(10)
        while True:
            if len(self.nodes) == 1:
                self.get_active_nodes()
                time.sleep(5)
                self.synchronize_with_network()
                if len(self.chain) > 1:
                    break

    # def ping_nodes(self):
    #         while True:
    #             time.sleep(10)  # Sleep 10 seconds
    #             # print(f"[Port {self.port}] Starting node ping")
    #             for node in list(self.nodes):
    #                 try:
    #                     response = requests.post(f'http://{node}/ping')
    #                     if response.status_code == 200:
    #                         self.node_failures[node] = 0
    #                         # logger.info(f"[Port {self.port}] Node {node} responded to ping")
    #                     else:
    #                         self.node_failures[node] += 1
    #                        # logger.info(f"[Port {self.port}] Node {node} failed to respond to ping ({self.node_failures[node]} failures)")
    #                 except requests.exceptions.RequestException as e:
    #                     self.node_failures[node] += 1
    #                     logger.error(f"[Port {self.port}] Error pinging node {node}: {e} ({self.node_failures[node]} failures)")

    #                 if self.node_failures[node] >= 3:
    #                     self.remove_node(node)
                

    def get_active_nodes(self):
        while True:
            time.sleep(30)
            try:
                address = f"http://{MASTER_SERVER_IP}/api/nodes"
                response = requests.get(address).json()
                active_addresses = [item["address"] for item in response if item["status"] == "active"]
                cleaned_addresses = [addr.replace("http://", "") for addr in active_addresses]

                if self.nodes != set(cleaned_addresses):
                    logger.info(f"[Port {self.port}] Updating active nodes from {self.nodes} to {set(cleaned_addresses)}")
                    self.nodes = set(cleaned_addresses)
                # else:
                    # logger.info(f"[Port {self.port}] No changes in active nodes")

            except Exception as e:
                logger.error(f"[Port {self.port}] Error getting active nodes: {e}")





    def simulated_crc_error(self):
        self.isSimulatedCrcError = not self.isSimulatedCrcError

        return self.isSimulatedCrcError