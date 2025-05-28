import requests
from flask import Blueprint, jsonify, request, after_this_request, send_file  
import zlib
from .models.blockchain import Blockchain
import argparse
import os
import signal
import logging
from .models.torrent import TorrentManager
import base64
import bencodepy

bp = Blueprint('blockchain', __name__)
blockchain = Blockchain()


torrent_manager = TorrentManager(blockchain)


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
        'hash': blockchain.get_latest_block().hash,
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




@bp.route('/register_in_network', methods=['POST'])
def register_in_newtork():
    values = request.get_json()
    node = values.get('node')
    blockchain.register_node_in_network(node)

        

    return jsonify({'message': 'Nodes added successfully!', 'total_nodes': list(blockchain.nodes)})


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


@bp.route('/sync', methods=['POST'])
def sync():
    
    
    

    
    if blockchain.synchronize_with_network():
        return jsonify({'message': 'Blockchain synchronized with the longest chain from the network'}), 200
    else:
        return jsonify({'message': 'No longer chain found, keeping the current chain'}), 400



@bp.route('/vote', methods=['POST'])
def vote():
    node_identifier = request.remote_addr
    values = request.get_json()
    if not values or 'transaction' not in values:
        logging.info(f"[Node {node_identifier}] Invalid transaction data received")
        return jsonify({'vote': 'no'}), 400

    transaction = values['transaction']
    
    logging.info(f"[Node {node_identifier}] Transaction received:")
    
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



@bp.route('/elect_master', methods=['POST'])
def elect_master():
    blockchain.is_master = True
    return jsonify({'message': 'This node is now the master'}), 200


@bp.route('/notify_master', methods=['POST'])
def notify_master():
    values = request.get_json()
    if not values or 'master_url' not in values:
        return 'Invalid master URL', 400

    blockchain.master_url = values['master_url']
    return jsonify({'message': 'Master updated'}), 200


@bp.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': list(blockchain.nodes)}), 200


@bp.route('/ping', methods=['POST'])
def ping():
    return jsonify({'message': 'pong'}), 200





@bp.route('/simulated-crc-error', methods=['POST'])
def simulated_crc_error():
    if blockchain.simulated_crc_error():
        return jsonify({'status': True, 'message': 'CRC error simulation enabled'}), 200
    else:
        return jsonify({'status': False, 'message': 'CRC error simulation disabled'}), 200

@bp.route('/simulated-hash', methods=['POST'])
def simulated_hash_error():
    if blockchain.corrupt_random_block():
        return jsonify({'status': True, 'message': 'Hash error simulation enabled'}), 200
    else:
        return jsonify({'status': False, 'message': 'Hash error simulation disabled'}), 200
    
@bp.route('/simulated-hash-fix', methods=['POST'])
def simulated_hash_fix_error():
    if blockchain.is_chain_valid():
        return jsonify({'status': True, 'message': 'Hash fix error simulation enabled'}), 200
    else:
        return jsonify({'status': False, 'message': 'Hash fix error simulation disabled'}), 200

@bp.route('/simulated-shutdown', methods=['POST'])
def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    return jsonify({'message': 'Server shutting down...'}), 200


@bp.route('/torrent/create/<transaction_id>', methods=['GET'])
def create_torrent(transaction_id):
    result = torrent_manager.create_torrent(transaction_id)
    if result:
        torrent, torrent_file_path = result
        return jsonify({
            'message': 'Torrent created successfully',
            'torrent': torrent.to_dict(),
            'torrent_file_path': torrent_file_path
        }), 200
    else:
        return jsonify({'message': 'Failed to create torrent'}), 400


@bp.route('/torrent/<file_id>', methods=['GET'])
def get_torrent(file_id):
    torrent = torrent_manager.get_torrent(file_id)
    if torrent:
        return jsonify(torrent.to_dict()), 200
    else:
        return jsonify({'message': 'Torrent not found'}), 404


@bp.route('/torrent/store_chunk', methods=['POST'])
def store_chunk():
    data = request.get_json()
    
    
    required = ['file_id', 'chunk_index', 'chunk_data', 'chunk_hash']
    if not all(k in data for k in required):
        return jsonify({'message': 'Missing required fields'}), 400
        
    
    is_base64 = data.get('is_base64', False)
    
    
    success = torrent_manager.store_chunk(
        data['file_id'], 
        data['chunk_index'], 
        data['chunk_data'],
        data['chunk_hash'],
        is_base64
    )
    
    if success:
        return jsonify({'message': 'Chunk stored successfully'}), 201
    else:
        return jsonify({'message': 'Failed to store chunk (hash mismatch)'}), 400


@bp.route('/torrent/chunk/<file_id>/<int:chunk_index>', methods=['GET'])
def get_chunk(file_id, chunk_index):
    chunk = torrent_manager.get_chunk(file_id, chunk_index)
    if chunk:
        if isinstance(chunk, bytes):
            chunk = base64.b64encode(chunk).decode('utf-8')
        return jsonify({
            'file_id': file_id,
            'chunk_index': chunk_index,
            'chunk_data': chunk
        }), 200
    else:
        return jsonify({'message': 'Chunk not found'}), 404


@bp.route('/torrent/download/<file_id>', methods=['GET'])
def download_file_torrent(file_id):
    torrent = torrent_manager.get_torrent(file_id)
    if not torrent:
        return jsonify({'message': 'Torrent not found'}), 404
        
    
    assembled_file = b''
    for i in range(torrent.total_chunks):
        
        chunk = torrent_manager.get_chunk(file_id, i)
        
        
        if not chunk and i in torrent.nodes:
            for node in torrent.nodes[i]:
                try:
                    response = requests.get(f"http://{node}/torrent/chunk/{file_id}/{i}")
                    if response.status_code == 200:
                        chunk_data = response.json()['chunk_data']
                        
                        torrent_manager.store_chunk(
                            file_id, 
                            i, 
                            chunk_data,
                            next((c['hash'] for c in torrent.chunks if c['id'] == i), None)
                        )
                        chunk = chunk_data
                        break
                except Exception as e:
                    
                    continue
        
        if not chunk:
            return jsonify({'message': f'Chunk {i} not found in network'}), 404
            
        
        if isinstance(chunk, str):
            chunk = chunk.encode('utf-8')
        assembled_file += chunk
    
    
    from flask import send_file
    import tempfile
    import os
    
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(assembled_file)
    temp.close()
    
    @after_this_request
    def remove_file(response):
        os.unlink(temp.name)
        return response
        
    return send_file(
        temp.name,
        as_attachment=True,
        download_name=torrent.file_name,
        mimetype='application/octet-stream'
    )


@bp.route('/torrent/file/<file_id>', methods=['GET'])
def download_torrent_file(file_id):
    torrent_path = os.path.join(torrent_manager.torrent_dir, f"{file_id}.torrent")
    
    if not os.path.exists(torrent_path):
        return jsonify({'message': 'Torrent file not found'}), 404
        
    return send_file(
        torrent_path,
        as_attachment=True,
        download_name=f"{file_id}.torrent",
        mimetype='application/x-bittorrent'
    )


@bp.route('/announce', methods=['GET'])
def tracker_announce():
    info_hash = request.args.get('info_hash')
    peer_id = request.args.get('peer_id')
    port = request.args.get('port')
    
    if not info_hash or not peer_id or not port:
        return 'Missing required parameters', 400
    
    
    client_ip = request.remote_addr
    
    
    response_dict = {
        b'interval': 1800,
        b'min interval': 900,
        b'complete': len(blockchain.nodes),
        b'incomplete': 0
    }
    
    
    peers_list = []
    for node in blockchain.nodes:
        try:
            if ':' in node:
                host, node_port = node.split(':')
                
                peers_list.append({
                    b'ip': host.encode('utf-8'),
                    
                    b'port': 6881,  
                    b'peer id': b'blockchain_peer_' + host.encode('utf-8')
                })
        except Exception as e:
            continue
    
    
    peers_list.append({
        b'ip': request.host.split(':')[0].encode('utf-8'),
        b'port': 6881,  
        b'peer id': b'blockchain_self_' + request.host.split(':')[0].encode('utf-8')
    })
    
    response_dict[b'peers'] = peers_list
    
    try:
        encoded_response = bencodepy.encode(response_dict)
        return encoded_response, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        
        return 'Internal server error', 500
    
    
@bp.route('/piece/<int:piece_index>', methods=['GET'])
def get_piece(piece_index):
    """Endpoint dla klientów BitTorrent do pobierania kawałków pliku"""
    
    info_hash = request.args.get('info_hash')
    
    if not info_hash:
        return 'Missing info_hash parameter', 400
        
    
    if not all(c in '0123456789abcdefABCDEF' for c in info_hash):
        info_hash = info_hash.encode('latin1').hex()
    
    
    file_id = torrent_manager.info_hash_to_file_id.get(info_hash)
    
    if file_id:
        chunk = torrent_manager.get_chunk(file_id, piece_index)
        if chunk:
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            return chunk, 200, {'Content-Type': 'application/octet-stream'}
    else:
        
        for file_id, torrent in torrent_manager.torrents.items():
            chunk = torrent_manager.get_chunk(file_id, piece_index)
            if chunk:
                if isinstance(chunk, str):
                    chunk = chunk.encode('utf-8')
                return chunk, 200, {'Content-Type': 'application/octet-stream'}
    
    return 'Piece not found', 404


@bp.route('/have/<int:piece_index>', methods=['GET'])
def have_piece(piece_index):
    """Sprawdza czy node ma dany kawałek"""
    info_hash = request.args.get('info_hash')
    
    for file_id, torrent in torrent_manager.torrents.items():
        chunk = torrent_manager.get_chunk(file_id, piece_index)
        if chunk:
            return jsonify({'have': True}), 200
    
    return jsonify({'have': False}), 200