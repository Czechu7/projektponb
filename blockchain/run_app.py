from app import create_app
from app.signalr_client import SignalRClient
import argparse
import socket
import threading
import time
import requests
import random
from flask import Flask, request, jsonify

# Globalna lista węzłów
NODES = [5001, 5002, 5003, 5004, 5005, 5006]

parser = argparse.ArgumentParser(description='Blockchain Node')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask app on')
parser.add_argument('--main', action='store_true', help='Specify if this node is the main server')
args = parser.parse_args()

app = create_app()
leader_votes = 0
is_leader = False
leader_node = None

@app.route('/vote', methods=['POST'])
def vote():
    global leader_votes, leader_node
    data = request.get_json()
    if data.get('vote') == 'leader':
        leader_votes += 1
        leader_node = data.get('node')
        return jsonify({'status': 'ACK'}), 200
    return jsonify({'status': 'NACK'}), 400

@app.route('/leader', methods=['GET'])
def get_leader():
    return jsonify({'leader': leader_node}), 200

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
            print(f"Connected to main server at port 6001")
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
    global is_leader, leader_votes, leader_node
    leader_votes = 0
    leader_node = args.port
    print(f"Initiating leader election for node {args.port}.")
    
    for node_port in NODES:
        try:
            response = requests.post(f'http://127.0.0.1:{node_port}/vote', json={'vote': 'leader', 'node': args.port})
            if response.status_code == 200 and response.json().get('status') == 'ACK':
                print(f"Node {node_port} acknowledged leader election.")
        except:
            continue
    
    # Jeśli ten węzeł otrzymał najwięcej głosów, staje się głównym serwerem
    if leader_votes >= len(NODES) // 2 + 1:
        print(f"Node {args.port} is becoming the main server.")
        is_leader = True
        print(f"I am the master node running on port {args.port}.")
        start_server()
    else:
        print(f"Node {args.port} did not receive enough votes. Checking for the elected leader.")
        check_elected_leader()

def check_elected_leader():
    global leader_node, is_leader
    leader_node = None
    for node_port in NODES:
        try:
            response = requests.get(f'http://127.0.0.1:{node_port}/leader')
            if response.status_code == 200:
                leader_node = response.json().get('leader')
                if leader_node:
                    print(f"Node {node_port} reports leader as {leader_node}.")
                    break
        except:
            continue

    if leader_node:
        print(f"Node {args.port} is connected to leader at port {leader_node}.")
        monitor_leader()
    else:
        print(f"Node {args.port} could not determine the leader. Initiating new leader election.")
        initiate_leader_election()

def monitor_leader():
    global leader_node
    while True:
        try:
            response = requests.get(f'http://127.0.0.1:{leader_node}/leader')
            if response.status_code != 200:
                raise Exception("Leader not responding")
            time.sleep(10)
        except:
            print(f"Leader at port {leader_node} is not responding. Initiating new leader election.")
            initiate_leader_election()
            break

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