import requests
from flask import Blueprint, jsonify, request
import zlib
from .models.blockchain import Blockchain
from .models.block import Block  # Dodaj ten import
import argparse
import os
import signal
import logging

bp = Blueprint('blockchain', __name__)
blockchain = Blockchain()

# Routes for adding new transactions
@bp.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not values or 'transaction' not in values:
        return 'Invalid transaction data', 400

    transaction = values['transaction']
    transaction['crc'] = zlib.crc32(transaction['data'].encode('utf-8'))
    sender_node = f"{request.host}"
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")
    print(f"Sender node: {sender_node}")

    if blockchain.add_transaction(transaction, sender_node=sender_node):
        return jsonify({'message': 'Transaction added successfully!'}), 201
    else:
        return jsonify({'message': 'Transaction rejected!'}), 400

# Routes for mining new blocks
@bp.route('/mine', methods=['GET'])
def mine():
    blockchain.mine_pending_transactions()
    response = {
        'message': 'New block mined successfully!',
        'index': blockchain.get_latest_block().index,
        'hash': blockchain.get_latest_block().hash,
    }

    for node in blockchain.nodes:
        try:
            requests.get(f'http://{node}/nodes/resolve')
        except requests.exceptions.RequestException:
            pass

    return jsonify(response)

# Routes for getting the full chain
@bp.route('/chain', methods=['GET'])
def full_chain():
    chain_data = [{
        'index': block.index,
        'previous_hash': block.previous_hash,
        'transactions': block.transactions,
        'timestamp': block.timestamp,
        'hash': block.hash
    } for block in blockchain.chain]

    return jsonify({'chain': chain_data, 'length': len(blockchain.chain)})

# Routes for registering nodes
@bp.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None or not isinstance(nodes, list):
        return "Invalid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({'message': 'Nodes added successfully!', 'total_nodes': list(blockchain.nodes)})



# Routes for registering nodes
@bp.route('/register_in_network', methods=['POST'])
def register_in_newtork():
    values = request.get_json()
    node = values.get('node')
    blockchain.register_node_in_network(node)

        

    return jsonify({'message': 'Nodes added successfully!', 'total_nodes': list(blockchain.nodes)})

# Routes for consensus algorithm
@bp.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain()
    if replaced:
        logging.info(f"[Port {blockchain.port}] Chain was replaced. New chain: {blockchain.chain}")
        return jsonify({
            'message': 'Our chain was replaced', 
            'new_chain': [{'index': block.index, 'previous_hash': block.previous_hash, 
                           'transactions': block.transactions, 'timestamp': block.timestamp, 
                           'hash': block.hash} for block in blockchain.chain]
        }), 200
    else:
        logging.info(f"[Port {blockchain.port}] Chain is authoritative. Current chain: {blockchain.chain}")
        return jsonify({
            'message': 'Our chain is authoritative', 
            'chain': [{'index': block.index, 'previous_hash': block.previous_hash, 
                       'transactions': block.transactions, 'timestamp': block.timestamp, 
                       'hash': block.hash} for block in blockchain.chain]
        }), 200

# Routes for inicializing new node with network
@bp.route('/sync', methods=['POST'])
def sync():
    # values = request.get_json()
    # if not values or 'blocks' not in values:
    #     return 'Invalid blockchain data', 400

    # new_chain = values['blocks']
    if blockchain.synchronize_with_network():
        return jsonify({'message': 'Blockchain synchronized with the longest chain from the network'}), 200
    else:
        return jsonify({'message': 'No longer chain found, keeping the current chain'}), 400


# Routes for voting on transactions
@bp.route('/vote', methods=['POST'])
def vote():
    node_identifier = request.remote_addr
    values = request.get_json()
    if not values or 'transaction' not in values:
        logging.info(f"[Node {node_identifier}] Invalid transaction data received")
        return jsonify({'vote': 'no'}), 400

    transaction = values['transaction']
    logging.info(f"[Node {node_identifier}] Transaction received: {transaction}")
    
    required_fields = ['transaction_id', 'document_id', 'document_type', 'timestamp', 'data', 'crc']
    for field in required_fields:
        if field not in transaction:
            logging.warning(f"[Node {node_identifier}] Missing field: {field}")
            return jsonify({'vote': 'no', 'reason': f'Missing field: {field}'}), 400

    calculated_crc = zlib.crc32(transaction['data'].encode('utf-8'))
    if calculated_crc != transaction['crc']:
        logging.warning(f"[Node {node_identifier}] CRC mismatch: calculated {calculated_crc}, received {transaction['crc']}")
        return jsonify({'vote': 'no', 'reason': 'CRC mismatch'}), 400

    logging.info(f"[Node {node_identifier}] Transaction approved")
    return jsonify({'vote': 'yes'}), 200


# Routes for master election
@bp.route('/elect_master', methods=['POST'])
def elect_master():
    blockchain.is_master = True
    return jsonify({'message': 'This node is now the master'}), 200

# Routes for new master notification
@bp.route('/notify_master', methods=['POST'])
def notify_master():
    values = request.get_json()
    if not values or 'master_url' not in values:
        return 'Invalid master URL', 400

    blockchain.master_url = values['master_url']
    return jsonify({'message': 'Master updated'}), 200

# Routes for getting all nodes
@bp.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': list(blockchain.nodes)}), 200

# Routes for getting the master node
@bp.route('/ping', methods=['POST'])
def ping():
    return jsonify({'message': 'pong'}), 200

@bp.route('/blocks/new', methods=['POST'])
def new_block():
    values = request.get_json()
    if not values or 'block' not in values:
        return 'Invalid block data', 400

    block_data = values['block']
    block = Block(
        index=block_data['index'],
        previous_hash=block_data['previous_hash'],
        transactions=block_data['transactions'],
        timestamp=block_data['timestamp']
    )
    block.hash = block_data['hash']

    # Sprawdź poprawność bloku
    if blockchain.is_chain_valid([block]):
        blockchain.chain.append(block)
        logging.info(f"[Port {blockchain.port}] New block added: {block.to_dict()}")

        # Synchronizuj łańcuch z siecią
        # blockchain.synchronize_with_network()

        return jsonify({'message': 'Block added successfully!'}), 201
    else:
        logging.info(f"[Port {blockchain.port}] Block rejected: {block.to_dict()}")
        return jsonify({'message': 'Block rejected!'}), 400




# SEKCJA SYMULACJI BLEDOW
# CRC ERROR
@bp.route('/simulated-crc-error', methods=['POST'])
def simulated_crc_error():
    if blockchain.simulated_crc_error():
        return jsonify({'status': True, 'message': 'CRC error simulation enabled'}), 200
    else:
        return jsonify({'status': False, 'message': 'CRC error simulation disabled'}), 200
    
# SHUTDOWN
@bp.route('/simulated-shutdown', methods=['POST'])
def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    return jsonify({'message': 'Server shutting down...'}), 200