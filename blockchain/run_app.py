from app import create_app
import argparse
import socket
import threading
import time

parser = argparse.ArgumentParser(description='Blockchain Node')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask app on')
parser.add_argument('--main', action='store_true', help='Specify if this node is the main server')
args = parser.parse_args()

app = create_app()

def handle_client_connection(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message:
                print(f"Received message: {message}")
                # Handle received message
            else:
                break
        except:
            break
    client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', args.port + 1000))
    server_socket.listen(5)
    print(f"Server listening on port {args.port + 1000}")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()

def connect_to_main_server():
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('127.0.0.1', 6001))
            print("Connected to main server")
            while True:
                # Send status or other messages to the main server
                client_socket.send(f"Node {args.port} status: active".encode())
                time.sleep(10)
        except:
            retry_count += 1
            print(f"Failed to connect to main server, retrying... ({retry_count}/{max_retries})")
            time.sleep(5)
    
    # Jeśli nie udało się połączyć 3 razy, przejmij rolę głównego serwera
    print("Failed to connect to main server 3 times. Initiating leader election.")
    initiate_leader_election()

def initiate_leader_election():
    nodes = [5001, 5002, 5003, 5004, 5005, 5006]  # Lista portów innych węzłów
    for node_port in nodes:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('127.0.0.1', node_port + 1000))
            client_socket.send(f"LeaderElection:{args.port}".encode())
            response = client_socket.recv(1024).decode()
            if response == "ACK":
                print(f"Node {node_port} acknowledged leader election.")
                return
        except:
            continue
    
    # Jeśli żaden węzeł nie odpowiedział, ten węzeł staje się głównym serwerem
    print(f"Node {args.port} is becoming the main server.")
    start_server()

if __name__ == '__main__':
    if args.port == 5001:
        print("Running as the main server.")
        server_thread = threading.Thread(target=start_server)
        server_thread.start()
    else:
        print("Running as a client node.")
        client_thread = threading.Thread(target=connect_to_main_server)
        client_thread.start()

    app.run(host='0.0.0.0', port=args.port, threaded=True)
