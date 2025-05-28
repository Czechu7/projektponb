from app import create_app
from app.bittorrent_peer import BitTorrentPeer
from app.routes import blockchain, torrent_manager
from app.udp_tracker import start_udp_tracker
import argparse
import threading

parser = argparse.ArgumentParser(description='Blockchain Node')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask app on')
parser.add_argument('--udp-tracker-port', type=int, default=6969, help='Port for UDP tracker')
parser.add_argument('--bt-port', type=int, default=6881, help='Port for BitTorrent peer server')
args = parser.parse_args()

app = create_app()

if __name__ == '__main__':
    #start_udp_tracker(args.udp_tracker_port, blockchain)
    bt_peer = BitTorrentPeer(torrent_manager, port=args.bt_port)
    bt_thread = threading.Thread(target=bt_peer.start)
    bt_thread.daemon = True
    bt_thread.start()
    
    print(f"Starting BitTorrent peer on port {args.bt_port}")
    app.run(host='0.0.0.0', port=args.port)
