import hashlib
import json
import os
import math
import random
import logging
import tempfile
import time


try:
    import bencodepy
except ImportError:
    os.system('pip install bencodepy')
    import bencodepy

logger = logging.getLogger(__name__)

class TorrentFile:
    def __init__(self, file_id, file_name, file_size, chunk_size=1024*512):  
        self.file_id = file_id
        self.file_name = file_name
        self.file_size = file_size
        self.chunk_size = chunk_size
        self.chunks = []
        self.total_chunks = math.ceil(file_size / chunk_size)
        self.nodes = {}  
        self.announce_urls = []  
        self.blockchain = None  
        
        
        
    def get_original_file_data(self):
        """Pobiera oryginalne dane pliku z JSON"""
        json_path = os.path.join("torrents", f"{self.file_id}.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            if 'original_data_base64' in data:
                import base64
                logger.info(f"Loading original file data from JSON for {self.file_id}")
                return base64.b64decode(data['original_data_base64'])
        
        logger.warning(f"No original_data_base64 found for {self.file_id}")
        return None 
        
        

    def add_chunk(self, chunk_id, chunk_hash):
        self.chunks.append({
            'id': chunk_id,
            'hash': chunk_hash
        })

    def assign_chunk_to_node(self, chunk_id, node_address):
        """Przypisz chunk do węzła - użyj pełnego chunk_id"""
        if chunk_id not in self.nodes:
            self.nodes[chunk_id] = []
        if node_address not in self.nodes[chunk_id]:
            self.nodes[chunk_id].append(node_address)

    def to_dict(self):
        return {
            'file_id': self.file_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'chunk_size': self.chunk_size,
            'total_chunks': self.total_chunks,
            'chunks': self.chunks,
            'nodes': self.nodes
        }

    @classmethod
    def from_dict(cls, data):
        torrent = cls(
            file_id=data['file_id'],
            file_name=data['file_name'],
            file_size=data['file_size'],
            chunk_size=data['chunk_size']
        )
        torrent.chunks = data['chunks']
        torrent.nodes = data['nodes']
        torrent.total_chunks = data['total_chunks']
        return torrent

    def save_to_file(self, directory="torrents"):
        """Zapisuje plik .torrent i zwraca ścieżkę pliku oraz info_hash"""
        os.makedirs(directory, exist_ok=True)

    
        file_path = os.path.join(directory, f"{self.file_id}.torrent")

    
        transaction = None
        if hasattr(self, 'blockchain') and self.blockchain:
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if isinstance(tx, dict) and tx.get('transaction_id') == self.file_id:
                        transaction = tx
                        break
                if transaction:
                    break
    
    
        json_data = self.to_dict()
    
        if transaction:
            import base64
            file_data = transaction['data']
            
            
            def is_base64(s):
                """Sprawdź czy string wygląda jak base64"""
                try:
                    if isinstance(s, str):
                        
                        import re
                        if re.match(r'^[A-Za-z0-9+/]*={0,2}$', s):
                            
                            base64.b64decode(s)
                            return True
                    return False
                except:
                    return False
            
            
            if transaction.get('encoding') == 'base64':
                
                json_data['original_data_base64'] = file_data
                logger.info("Using file_data marked as base64")
            elif isinstance(file_data, str) and is_base64(file_data):
                
                json_data['original_data_base64'] = file_data
                logger.info("Detected file_data as base64 format")
            elif isinstance(file_data, str):
                
                file_data_bytes = file_data.encode('utf-8')
                json_data['original_data_base64'] = base64.b64encode(file_data_bytes).decode('ascii')
                logger.info("Encoded text file_data to base64")
            else:
                
                json_data['original_data_base64'] = base64.b64encode(file_data).decode('ascii')
                logger.info("Encoded binary file_data to base64")
        
            logger.info(f"Added original_data_base64 to JSON (length: {len(json_data['original_data_base64'])})")

    
        json_path = os.path.join(directory, f"{self.file_id}.json")
        with open(json_path, 'w') as f:
            json.dump(json_data, f)

    
        logger.info(f"TORRENT DEBUG: file_size = {self.file_size}")
        logger.info(f"TORRENT DEBUG: total_chunks = {self.total_chunks}")
        logger.info(f"TORRENT DEBUG: chunk_size = {self.chunk_size}")
    
    
        pieces = b''
        total_assembled_size = 0
    
        if 'original_data_base64' in json_data:
            
            try:
                original_file_data = base64.b64decode(json_data['original_data_base64'])
                logger.info(f"Successfully decoded original_data_base64: {len(original_file_data)} bytes")
            except Exception as e:
                logger.error(f"Failed to decode original_data_base64: {e}")
                return None, None, None
        
            
            for i in range(0, len(original_file_data), self.chunk_size):
                chunk_data = original_file_data[i:i+self.chunk_size]
                hash_bytes = hashlib.sha1(chunk_data).digest()
                pieces += hash_bytes
                total_assembled_size += len(chunk_data)
                logger.debug(f"Chunk {i//self.chunk_size}: {len(chunk_data)} bytes, SHA-1: {hash_bytes.hex()}")
        
            
            actual_file_size = len(original_file_data)
            if actual_file_size != self.file_size:
                logger.warning(f"Adjusting file_size from {self.file_size} to {actual_file_size}")
                self.file_size = actual_file_size
                total_assembled_size = actual_file_size
            else:
                logger.error("No original_data_base64 found - cannot create torrent")
                return None, None, None

    
        info_dict = {
            b'name': self.file_name.encode('utf-8'),
            b'piece length': self.chunk_size,
            b'pieces': pieces,
            b'length': self.file_size,
        }
    
        logger.info(f"FINAL TORRENT: length={self.file_size}, pieces={len(pieces)//20} chunks")
    
        torrent_dict = {
            b'info': info_dict,
            b'announce': b'http://127.0.0.1:5001/announce'
        }
    
    
        if self.announce_urls:
            announce_list = []
            for url in self.announce_urls:
                announce_list.append([url.encode('utf-8')])
            if announce_list:
                torrent_dict[b'announce-list'] = announce_list

    
        import bencodepy
        with open(file_path, 'wb') as f:
            torrent_data = bencodepy.encode(torrent_dict)
            f.write(torrent_data)

    
        info_bencode = bencodepy.encode(info_dict)
        info_hash_bytes = hashlib.sha1(info_bencode).digest()
        info_hash_hex = info_hash_bytes.hex()

        logger.info(f"Saved torrent file to: {file_path} with info_hash: {info_hash_hex}")

        return file_path, info_hash_bytes, info_hash_hex
        
    @classmethod
    def load_from_file(cls, file_path):
        """Load a torrent from a .torrent file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

    def set_chunk_manager(self, chunk_manager):
        """Ustawia referencję do menedżera chunków"""
        self._chunk_manager = chunk_manager
    
    def _get_chunk_data(self, chunk_id):
        """Pobiera dane chunka z menedżera, jeśli jest dostępny"""
        if hasattr(self, '_chunk_manager') and self._chunk_manager:
            
            
            chunk_index = int(chunk_id.split('_')[-1])  
            return self._chunk_manager._get_chunk_data(self.file_id, chunk_index)
        return None

class TorrentManager:
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.torrents = {}  
        self.chunk_storage = {}  
        self.torrent_dir = "torrents"  
        self.info_hash_to_file_id = {}  
        
        
        os.makedirs(self.torrent_dir, exist_ok=True)
        
    def create_torrent(self, transaction_id, chunk_size=1024*512):
        """Creates a torrent from a file transaction in the blockchain"""
        import bencodepy
        import base64
        
        
        transaction = None
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict) and tx.get('transaction_id') == transaction_id:
                    transaction = tx
                    break
            if transaction:
                break
                
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found in blockchain")
            return None
            
        
        file_data = transaction['data']
        file_name = transaction.get('signature', f"file_{transaction_id}")
        
        
        if transaction.get('encoding') == 'base64':
            try:
                file_data = base64.b64decode(file_data)
                logger.info("Decoded file data from base64")
            except Exception as e:
                logger.error(f"Failed to decode base64 data: {e}")
                return None
        elif isinstance(file_data, str):
            file_data = file_data.encode('utf-8')

        
        
        file_size = len(file_data)
        logger.info(f"Creating torrent for file: {file_name}, size: {file_size} bytes")
        
        
        torrent = TorrentFile(
            file_id=transaction_id,
            file_name=file_name,
            file_size=file_size,
            chunk_size=chunk_size
        )
        
        
        torrent.blockchain = self.blockchain
        torrent.set_chunk_manager(self)
        
        
        chunks = []
        for i in range(0, file_size, chunk_size):
            chunk_data = file_data[i:i+chunk_size]
            chunk_index = i//chunk_size
            chunk_id = f"{transaction_id}_{chunk_index}"  
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()

            
            self.chunk_storage[chunk_id] = chunk_data
            
            
            torrent.add_chunk(chunk_id, chunk_hash)  
            
            chunks.append({
                'id': chunk_id,
                'index': chunk_index,
                'hash': chunk_hash,
                'data': chunk_data  
            })
        
        
        self.distribute_chunks(torrent, chunks)
        
        
        
        
        
        
        
        
        self.torrents[transaction_id] = torrent
        
        
        torrent_file_path, info_hash_bytes, info_hash_hex = torrent.save_to_file(self.torrent_dir)
        
        
        self.info_hash_to_file_id[info_hash_hex] = transaction_id
        self.info_hash_to_file_id[info_hash_bytes] = transaction_id
        
        import urllib.parse
        url_encoded_info_hash = urllib.parse.quote(info_hash_bytes)
        self.info_hash_to_file_id[url_encoded_info_hash] = transaction_id
        
        logger.info(f"Created torrent with file_id {transaction_id}, info_hash: {info_hash_hex}")

        return torrent, torrent_file_path
        
    def distribute_chunks(self, torrent, chunks):
        """Distribute chunks to available nodes"""
        nodes = list(self.blockchain.nodes)
        if not nodes:
            logger.warning("No nodes available for chunk distribution")
            return
        
        redundancy = min(3, len(nodes))
        for chunk in chunks:
            selected_nodes = random.sample(nodes, redundancy)
            for node in selected_nodes:
                
                torrent.assign_chunk_to_node(chunk['id'], node)  
                
                try:
                    import requests
                    import base64
                    
                    
                    if isinstance(chunk['data'], bytes):
                        chunk_data_base64 = base64.b64encode(chunk['data']).decode('ascii')
                    else:
                        chunk_data_binary = chunk['data'].encode('utf-8') if isinstance(chunk['data'], str) else chunk['data']
                        chunk_data_base64 = base64.b64encode(chunk_data_binary).decode('ascii')
                    
                    requests.post(
                        f"http://{node}/torrent/store_chunk",
                        json={
                            'file_id': torrent.file_id,
                            'chunk_id': chunk['id'],
                            'chunk_index': chunk['index'],
                            'chunk_data': chunk_data_base64,
                            'chunk_hash': chunk['hash'],
                            'is_base64': True  
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send chunk to node {node}: {e}")
                    
    def get_torrent(self, file_id):
        """Get torrent metadata by file ID"""
        return self.torrents.get(file_id)
        
    def get_chunk(self, file_id, chunk_index):
        """Get a chunk from local storage"""
        chunk_id = f"{file_id}_{chunk_index}"
        chunk_data = self.chunk_storage.get(chunk_id)
        
        if chunk_data is None:
            logger.warning(f"Chunk {chunk_id} not found in storage")
            return None
            
        
        if isinstance(chunk_data, str):
            chunk_data = chunk_data.encode('utf-8')
            
        logger.debug(f"Retrieved chunk {chunk_id}: {len(chunk_data)} bytes")
        return chunk_data
    
    def store_chunk(self, file_id, chunk_index, chunk_data, chunk_hash, is_base64=False):
        """Store a chunk in local storage"""
        chunk_id = f"{file_id}_{chunk_index}"
        
        
        if is_base64 or isinstance(chunk_data, str):
            try:
                import base64
                
                chunk_data_binary = base64.b64decode(chunk_data)
                chunk_data = chunk_data_binary
                logger.debug("Decoded chunk data from base64")
            except:
                
                if isinstance(chunk_data, str):
                    chunk_data = chunk_data.encode('utf-8')
    
    
        calc_hash = hashlib.sha256(chunk_data).hexdigest()
        if calc_hash != chunk_hash:
            logger.error(f"Chunk hash mismatch: {calc_hash} != {chunk_hash}")
            return False
            
        
        self.chunk_storage[chunk_id] = chunk_data
        return True
    
    def _get_chunk_data(self, file_id, chunk_index):
        """Pomocnicza metoda do uzyskiwania danych chunka dla haszowania"""
        chunk_id = f"{file_id}_{chunk_index}"
        return self.chunk_storage.get(chunk_id)

    def get_file_id_by_info_hash(self, info_hash):
        """Get file_id by info_hash"""
        return self.info_hash_to_file_id.get(info_hash)

    def get_torrent_by_info_hash(self, info_hash):
        """Get torrent by info_hash"""
        file_id = self.get_file_id_by_info_hash(info_hash)
        if file_id:
            return self.get_torrent(file_id)
        return None

    def debug_info_hash(self, file_path):
        """Debug utility to calculate info_hash from existing .torrent file"""
        import bencodepy
        with open(file_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
    
        info_dict = torrent_data.get(b'info', {})
        info_bencode = bencodepy.encode(info_dict)
        info_hash = hashlib.sha1(info_bencode).digest()
        info_hash_hex = info_hash.hex()
    
        logger.info(f"Debug: .torrent file {file_path} has info_hash: {info_hash_hex}")
        return info_hash_hex

    
    def initialize_info_hash_mapping(self):
        """Inicjalizuje mapowanie info_hash -> file_id z istniejących plików .torrent"""
        if os.path.exists(self.torrent_dir):
            for file in os.listdir(self.torrent_dir):
                if file.endswith('.torrent'):
                    file_path = os.path.join(self.torrent_dir, file)
                    file_id = file.replace('.torrent', '')
                    info_hash_hex = self.debug_info_hash(file_path)
                
                    
                    self.info_hash_to_file_id[info_hash_hex] = file_id
                
                    
                    info_hash_bytes = bytes.fromhex(info_hash_hex)
                    self.info_hash_to_file_id[info_hash_bytes] = file_id
                
                    logger.info(f"Added mapping from existing torrent: {info_hash_hex} -> {file_id}")

    def get_original_file_data(self):
        """Pobiera oryginalne dane pliku z JSON"""
        json_path = os.path.join("torrents", f"{self.file_id}.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            if 'original_data_base64' in data:
                import base64
                logger.info(f"Loading original file data from JSON for {self.file_id}")
                return base64.b64decode(data['original_data_base64'])
        
        logger.warning(f"No original_data_base64 found for {self.file_id}")
        return None