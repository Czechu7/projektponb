import socket
import struct
import threading
import time
import logging
import hashlib
from .models.blockchain import Blockchain

logger = logging.getLogger(__name__)

class UDPTracker:
    def __init__(self, port=6969, blockchain=None):
        self.port = port
        self.blockchain = blockchain or Blockchain()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.running = False
        
        
        self.CONNECT = 0
        self.ANNOUNCE = 1
        self.SCRAPE = 2
        self.ERROR = 3
        
        
        self.connections = {}  
        
    def start(self):
        """Start the UDP tracker server"""
        self.running = True
        logger.info(f"UDP Tracker started on port {self.port}")
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                threading.Thread(target=self.handle_request, args=(data, addr)).start()
            except Exception as e:
                logger.error(f"UDP Tracker error: {e}")
                
    def stop(self):
        """Stop the UDP tracker server"""
        self.running = False
        self.sock.close()
        
    def handle_request(self, data, addr):
        """Handle incoming UDP requests"""
        try:
            if len(data) < 16:
                return
                
            
            connection_id = struct.unpack('>Q', data[:8])[0]
            action = struct.unpack('>I', data[8:12])[0]
            transaction_id = struct.unpack('>I', data[12:16])[0]
            
            if action == self.CONNECT:
                self.handle_connect(transaction_id, addr)
            elif action == self.ANNOUNCE:
                self.handle_announce(data, transaction_id, addr)
            elif action == self.SCRAPE:
                self.handle_scrape(data, transaction_id, addr)
                
        except Exception as e:
            logger.error(f"Error handling UDP request from {addr}: {e}")
            
    def handle_connect(self, transaction_id, addr):
        """Handle connect request"""
        
        connection_id = int(time.time()) + hash(addr) % 1000000
        self.connections[connection_id] = time.time()
        
        
        response = struct.pack('>IIQ', 
                             self.CONNECT,      
                             transaction_id,    
                             connection_id)     
        
        self.sock.sendto(response, addr)
        logger.debug(f"Connect response sent to {addr}")
        
    def handle_announce(self, data, transaction_id, addr):
        """Handle announce request"""
        try:
            if len(data) < 98:  
                return
                
            
            connection_id = struct.unpack('>Q', data[:8])[0]
            
            
            if connection_id not in self.connections:
                self.send_error(transaction_id, "Invalid connection ID", addr)
                return
                
            
            info_hash = data[16:36]
            peer_id = data[36:56]
            downloaded = struct.unpack('>Q', data[56:64])[0]
            left = struct.unpack('>Q', data[64:72])[0]
            uploaded = struct.unpack('>Q', data[72:80])[0]
            event = struct.unpack('>I', data[80:84])[0]
            ip = struct.unpack('>I', data[84:88])[0]
            key = struct.unpack('>I', data[88:92])[0]
            num_want = struct.unpack('>i', data[92:96])[0]
            port = struct.unpack('>H', data[96:98])[0]
            
            
            peers_data = b''
            peer_count = 0
            
            for node in list(self.blockchain.nodes)[:num_want if num_want > 0 else 50]:
                try:
                    if ':' in node:
                        host, node_port = node.split(':')
                        
                        ip_bytes = socket.inet_aton(host)
                        port_bytes = struct.pack('>H', int(node_port))
                        peers_data += ip_bytes + port_bytes
                        peer_count += 1
                except:
                    continue
            
            
            response = struct.pack('>IIIII',
                                 self.ANNOUNCE,     
                                 transaction_id,    
                                 1800,             
                                 0,                
                                 len(self.blockchain.nodes))  
            
            response += peers_data
            
            self.sock.sendto(response, addr)
            logger.debug(f"Announce response sent to {addr} with {peer_count} peers")
            
        except Exception as e:
            logger.error(f"Error in announce handling: {e}")
            self.send_error(transaction_id, "Announce error", addr)
            
    def handle_scrape(self, data, transaction_id, addr):
        """Handle scrape request"""
        
        response = struct.pack('>II',
                             self.SCRAPE,       
                             transaction_id)    
        
        
        scrape_data = struct.pack('>III', 
                                len(self.blockchain.nodes),  
                                0,                            
                                0)                            
        response += scrape_data
        
        self.sock.sendto(response, addr)
        
    def send_error(self, transaction_id, message, addr):
        """Send error response"""
        message_bytes = message.encode('utf-8')
        response = struct.pack('>II', self.ERROR, transaction_id) + message_bytes
        self.sock.sendto(response, addr)


udp_tracker_instance = None

def start_udp_tracker(port=6969, blockchain=None):
    """Start UDP tracker in a separate thread"""
    global udp_tracker_instance
    
    if udp_tracker_instance is None:
        udp_tracker_instance = UDPTracker(port, blockchain)
        tracker_thread = threading.Thread(target=udp_tracker_instance.start)
        tracker_thread.daemon = True
        tracker_thread.start()
        logger.info(f"UDP Tracker started on port {port}")
    
    return udp_tracker_instance

def stop_udp_tracker():
    """Stop UDP tracker"""
    global udp_tracker_instance
    
    if udp_tracker_instance:
        udp_tracker_instance.stop()
        udp_tracker_instance = None