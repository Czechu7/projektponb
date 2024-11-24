import requests
from flask import Blueprint, jsonify, request
from .models.blockchain import Blockchain

bp = Blueprint('blockchain', __name__)
blockchain = Blockchain()

@bp.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not values or 'transaction' not in values:
        return 'Invalid transaction data', 400

    transaction = values['transaction']
    blockchain.add_transaction(transaction)
    return jsonify({'message': 'Transaction added successfully!'}), 201

@bp.route('/mine', methods=['GET'])
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

@bp.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None or not isinstance(nodes, list):
        return "Invalid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({'message': 'Nodes added successfully!', 'total_nodes': list(blockchain.nodes)})

@bp.route('/nodes/resolve', methods=['GET'])
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
