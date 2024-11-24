from flask import Flask, jsonify, request
import hashlib
import time
import json
import requests
import argparse

app = Flask(__name__)

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp or time.time()
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'previous_hash': self.previous_hash,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

class Blockchain:
    def __init__(self, difficulty=2):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions = []
        self.nodes = set()

    def create_genesis_block(self):
        return Block(0, "0", "Genesis Block", time.time())

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

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

blockchain = Blockchain()

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not values or 'transaction' not in values:
        return 'Invalid transaction data', 400

    transaction = values['transaction']
    blockchain.add_transaction(transaction)
    return jsonify({'message': 'Transaction added successfully!'}), 201

@app.route('/mine', methods=['GET'])
def mine():
    blockchain.mine_pending_transactions()
    response = {
        'message': 'New block mined successfully!',
        'index': blockchain.get_latest_block().index,
        'hash': blockchain.get_latest_block().hash
    }

    for node in blockchain.nodes:
        try:
            requests.get(f'http://{node}/nodes/resolve')
        except requests.exceptions.RequestException:
            pass

    return jsonify(response)

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = [{
        'index': block.index,
        'previous_hash': block.previous_hash,
        'transactions': block.transactions,
        'timestamp': block.timestamp,
        'hash': block.hash
    } for block in blockchain.chain]

    return jsonify({'chain': chain_data, 'length': len(blockchain.chain)})

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None or not isinstance(nodes, list):
        return "Invalid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({'message': 'Nodes added successfully!', 'total_nodes': list(blockchain.nodes)})

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain()
    if replaced:
        return jsonify({
            'message': 'Our chain was replaced', 
            'new_chain': [{'index': block.index, 'previous_hash': block.previous_hash, 
                           'transactions': block.transactions, 'timestamp': block.timestamp, 
                           'hash': block.hash} for block in blockchain.chain]
        }), 200
    else:
        return jsonify({
            'message': 'Our chain is authoritative', 
            'chain': [{'index': block.index, 'previous_hash': block.previous_hash, 
                       'transactions': block.transactions, 'timestamp': block.timestamp, 
                       'hash': block.hash} for block in blockchain.chain]
        }), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Blockchain Node')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask app on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
