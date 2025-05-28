import socket
import threading
import logging
import struct
import hashlib
import os
from .models.torrent import TorrentManager

logger = logging.getLogger(__name__)

class BitTorrentPeer:
    def __init__(self, torrent_manager, port=6881):
        self.torrent_manager = torrent_manager
        self.port = port
        self.running = False
        self.peers = {}
        self.sock = None
        
    def start(self):
        """Uruchamia serwer BitTorrent peer"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.listen(5)
            self.running = True
            
            logger.info(f"BitTorrent peer listening on port {self.port}")
            
            while self.running:
                try:
                    client_sock, address = self.sock.accept()
                    threading.Thread(target=self.handle_connection, args=(client_sock, address)).start()
                except Exception as e:
                    logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            logger.error(f"Error starting BitTorrent peer: {e}")
            if self.sock:
                self.sock.close()
                
    def handle_connection(self, sock, address):
        """Obsługuje połączenie BitTorrent"""
        logger.info(f"New connection from {address}")
        
        try:
            
            data = sock.recv(68)  
            if len(data) < 68:
                logger.error("Incomplete handshake received")
                sock.close()
                return
                
            
            pstrlen = data[0]
            if pstrlen != 19:  
                logger.error(f"Invalid handshake protocol string length: {pstrlen}")
                sock.close()
                return
                
            
            info_hash = data[28:48]  
            info_hash_hex = info_hash.hex()  
            
            
            logger.info(f"Looking for info_hash: {info_hash_hex}")
            logger.info(f"Known info_hashes: {list(self.torrent_manager.info_hash_to_file_id.keys())}")
            
            
            file_id = self.torrent_manager.info_hash_to_file_id.get(info_hash_hex)
            if not file_id:
                file_id = self.torrent_manager.info_hash_to_file_id.get(info_hash)
                
            if not file_id:
                logger.error(f"No torrent found for info_hash: {info_hash_hex}")
                sock.close()
                return
                
            
            peer_id = b'-BC0001-' + os.urandom(12)  
            response = bytes([pstrlen]) + b'BitTorrent protocol' + b'\x00' * 8 + info_hash + peer_id
            sock.sendall(response)
            
            
            self.handle_bittorrent_messages(sock, file_id, info_hash_hex)
            
        except Exception as e:
            logger.error(f"Error handling BitTorrent connection: {e}")
        finally:
            sock.close()
            
    def handle_bittorrent_messages(self, sock, file_id, info_hash):
        """Obsługuje wiadomości BitTorrent po handshake"""
        torrent = self.torrent_manager.get_torrent(file_id)
        if not torrent:
            logger.error(f"Torrent not found for file_id: {file_id}")
            return
        
        
        pieces = bytearray((torrent.total_chunks + 7) // 8)
        have_pieces = 0
        for i in range(torrent.total_chunks):
            chunk = self.torrent_manager.get_chunk(file_id, i)
            if chunk:
                pieces[i // 8] |= (1 << (7 - (i % 8)))
                have_pieces += 1
        
        
        if have_pieces > 0:
            logger.info(f"Sending bitfield with {have_pieces}/{torrent.total_chunks} pieces")
            msg = struct.pack(">IB", len(pieces) + 1, 5) + pieces
            sock.sendall(msg)
        else:
            logger.warning("No pieces available to share!")
            
        while True:
            try:
                
                length_prefix = sock.recv(4)
                if not length_prefix or len(length_prefix) < 4:
                    logger.info("Connection closed or incomplete data")
                    break
                    
                length = struct.unpack(">I", length_prefix)[0]
                
                
                if length == 0:
                    logger.debug("Received keep-alive")
                    continue
                    
                
                message = sock.recv(length)
                if not message:
                    logger.info("Connection closed during message read")
                    break
                    
                msg_id = message[0]
                logger.debug(f"Received message type: {msg_id}, length: {length}")
                
                
                if msg_id == 0:  
                    logger.debug("Received choke")
                elif msg_id == 1:  
                    logger.debug("Received unchoke")
                elif msg_id == 2:  
                    
                    logger.info("Received interested, sending unchoke")
                    sock.sendall(struct.pack(">IB", 1, 1))  
                elif msg_id == 3:  
                    logger.debug("Received not interested")
                elif msg_id == 4:  
                    logger.debug("Received have")
                elif msg_id == 5:  
                    logger.debug("Received bitfield")
                elif msg_id == 6:  
                    if len(message) >= 13:  
                        index, begin, req_length = struct.unpack(">III", message[1:13])
                        logger.info(f"Received request for piece {index}, offset {begin}, length {req_length}")
                        
                        
                        chunk = self.torrent_manager.get_chunk(file_id, index)
                        if chunk:
                            
                            if isinstance(chunk, str):
                                chunk = chunk.encode('utf-8')
                                
                            
                            if begin < len(chunk) and begin + req_length <= len(chunk):
                                piece_data = chunk[begin:begin+req_length]
                                
                                
                                logger.info(f"Sending piece {index}, offset {begin}, length {len(piece_data)}")
                                
                                
                                msg = struct.pack(">IBII", len(piece_data) + 9, 7, index, begin) + piece_data
                                sock.sendall(msg)
                            else:
                                logger.error(f"Invalid request range: begin={begin}, length={req_length}, chunk size={len(chunk)}")
                        else:
                            logger.error(f"Requested chunk {index} not found")
                            
                elif msg_id == 7:  
                    logger.debug("Received piece")
                elif msg_id == 8:  
                    logger.debug("Received cancel")
                else:
                    logger.warning(f"Unknown message type: {msg_id}")
            
            except Exception as e:
                logger.error(f"Error processing BitTorrent message: {e}")
                break
                
    def stop(self):
        """Zatrzymuje serwer BitTorrent peer"""
        self.running = False
        if self.sock:
            self.sock.close()