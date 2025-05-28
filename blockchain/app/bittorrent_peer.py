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
        
        
        original_file_data = torrent.get_original_file_data()
        if not original_file_data:
            logger.error(f"No original file data found for {file_id}")
            return
        
        
        actual_chunks = (len(original_file_data) + torrent.chunk_size - 1) // torrent.chunk_size
        logger.info(f"Using original file data: {len(original_file_data)} bytes, {actual_chunks} chunks")
        
        
        pieces = bytearray((actual_chunks + 7) // 8)
        for i in range(actual_chunks):
            pieces[i // 8] |= (1 << (7 - (i % 8)))
        
        logger.info(f"Sending bitfield with {actual_chunks}/{actual_chunks} pieces")
        msg = struct.pack(">IB", len(pieces) + 1, 5) + pieces
        
        try:
            sock.sendall(msg)
        except Exception as e:
            logger.error(f"Failed to send bitfield: {e}")
            return
        
        
        for i in range(actual_chunks):
            try:
                have_msg = struct.pack(">IBI", 5, 4, i)
                sock.sendall(have_msg)
                logger.debug(f"Sent HAVE message for piece {i}")
            except Exception as e:
                logger.error(f"Failed to send HAVE for piece {i}: {e}")
                return
        
        
        while True:
            try:
                
                sock.settimeout(30.0)  
                
                
                length_prefix = sock.recv(4)
                if not length_prefix or len(length_prefix) < 4:
                    logger.info("Connection closed or incomplete data")
                    break
                    
                length = struct.unpack(">I", length_prefix)[0]
                
                
                if length == 0:
                    logger.debug("Received keep-alive")
                    continue
                
                
                if length > 1024*1024:  
                    logger.error(f"Message too large: {length} bytes")
                    break
                
                
                message = sock.recv(length)
                if not message or len(message) != length:
                    logger.info("Connection closed during message read or incomplete message")
                    break
                    
                msg_id = message[0]
                logger.debug(f"Received message type: {msg_id}, length: {length}")
                
                
                if msg_id == 0:  
                    logger.debug("Received choke")
                elif msg_id == 1:  
                    logger.debug("Received unchoke")
                elif msg_id == 2:  
                    logger.info("Received interested, sending unchoke")
                    try:
                        sock.sendall(struct.pack(">IB", 1, 1))  
                    except Exception as e:
                        logger.error(f"Failed to send unchoke: {e}")
                        break
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
                        
                        
                        if index >= actual_chunks:
                            logger.error(f"Invalid piece index {index}, max is {actual_chunks-1}")
                            continue
                        
                        
                        piece_start = index * torrent.chunk_size
                        piece_end = min(piece_start + torrent.chunk_size, len(original_file_data))
                        
                        if piece_start < len(original_file_data):
                            
                            piece_data = original_file_data[piece_start:piece_end]
                            
                            
                            if begin < len(piece_data) and begin + req_length <= len(piece_data):
                                requested_data = piece_data[begin:begin+req_length]
                                
                                logger.info(f"Sending piece {index}, offset {begin}, length {len(requested_data)} bytes")
                                
                                
                                try:
                                    msg = struct.pack(">IBII", len(requested_data) + 9, 7, index, begin) + requested_data
                                    sock.sendall(msg)
                                    logger.debug(f"Successfully sent piece {index}")
                                except Exception as e:
                                    logger.error(f"Failed to send piece {index}: {e}")
                                    break
                            else:
                                logger.error(f"Invalid request range: begin={begin}, length={req_length}, piece size={len(piece_data)}")
                        else:
                            logger.error(f"Requested piece {index} beyond file size")
                            
                elif msg_id == 7:  
                    logger.debug("Received piece")
                elif msg_id == 8:  
                    logger.debug("Received cancel")
                else:
                    logger.warning(f"Unknown message type: {msg_id}")
                
            except socket.timeout:
                logger.warning("Socket timeout - sending keep-alive")
                try:
                    sock.sendall(struct.pack(">I", 0))  
                except:
                    logger.error("Failed to send keep-alive")
                    break
            except ConnectionResetError:
                logger.info("Connection reset by peer")
                break
            except Exception as e:
                logger.error(f"Error processing BitTorrent message: {e}")
                break
                
    def stop(self):
        """Zatrzymuje serwer BitTorrent peer"""
        self.running = False
        if self.sock:
            self.sock.close()