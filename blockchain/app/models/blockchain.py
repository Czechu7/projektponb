import time
import requests
import logging
import zlib
from .block import Block
import argparse
from .node_monitor import NodeMonitor
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=5001)
args = parser.parse_args()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        for node in predefined_nodes:
            self.register_node(node)

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
        if self.vote_on_transaction(transaction):
            self.pending_transactions.append(transaction)
            logger.info(f"Transaction {transaction} added successfully!")
            return True
        logger.info(f"Transaction {transaction} rejected!")
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

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)

        for node in network:
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

        if longest_chain:
            self.chain = longest_chain
            return True

        return False

    def vote_on_transaction(self, transaction):
        transaction_data = transaction['data']
        calculated_crc = zlib.crc32(transaction_data.encode('utf-8'))
        if calculated_crc != transaction['crc']:
            logger.info(f"Transaction {transaction} rejected due to CRC mismatch!")
            return False

        votes = 0
        for node in self.nodes:
            response = requests.post(f'http://{node}/vote', json={'transaction': transaction})
            if response.status_code == 200 and response.json().get('vote') == 'yes':
                votes += 1
                logger.info(f"Node {node} voted YES for transaction {transaction}")
            else:
                logger.info(f"Node {node} voted NO for transaction {transaction}")

        if votes >= self.consensus_threshold:
            logger.info(f"Transaction {transaction} approved with {votes} votes")
        else:
            logger.info(f"Transaction {transaction} rejected with {votes} votes")

        return votes >= self.consensus_threshold
