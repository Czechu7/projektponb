import requests
from flask import Blueprint, jsonify, request
import zlib
from .models.blockchain import Blockchain
import argparse

bp = Blueprint('blockchain', __name__)
blockchain = Blockchain()

@bp.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not values or 'transaction' not in values:
        return 'Invalid transaction data', 400

    transaction = values['transaction']
    transaction['crc'] = zlib.crc32(transaction['data'].encode('utf-8'))
    if blockchain.add_transaction(transaction):
        return jsonify({'message': 'Transaction added successfully!'}), 201
    else:
        return jsonify({'message': 'Transaction rejected!'}), 400

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

@bp.route('/vote', methods=['POST'])
def vote():
    values = request.get_json()
    if not values or 'transaction' not in values:
        return jsonify({'vote': 'no'}), 400

    transaction = values['transaction']
    
    required_fields = ['transaction_id', 'document_id', 'document_type', 'timestamp', 'data', 'signature', 'crc']
    for field in required_fields:
        if field not in transaction:
            return jsonify({'vote': 'no', 'reason': f'Missing field: {field}'}), 400

    calculated_crc = zlib.crc32(transaction['data'].encode('utf-8'))
    if calculated_crc != transaction['crc']:
        return jsonify({'vote': 'no', 'reason': 'CRC mismatch'}), 400

    return jsonify({'vote': 'yes'}), 200
