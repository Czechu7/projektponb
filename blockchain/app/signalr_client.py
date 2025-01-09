from signalrcore.hub_connection_builder import HubConnectionBuilder
import json
import logging

class SignalRClient:
    def __init__(self, hub_url):
        self.hub_connection = HubConnectionBuilder()\
            .with_url(hub_url)\
            .configure_logging(logging.DEBUG)\
            .build()

    def start(self):
        self.hub_connection.on_open(self.on_open)
        self.hub_connection.on_close(self.on_close)
        self.hub_connection.on("ReceiveTransaction", self.receive_transaction)
        self.hub_connection.on("ConsensusResolved", self.consensus_resolved)
        self.hub_connection.on("ReceiveChain", self.receive_chain)

        self.hub_connection.start()

    def stop(self):
        self.hub_connection.stop()

    def send_transaction(self, transaction):
        self.hub_connection.send("SendTransaction", [transaction])

    def resolve_consensus(self):
        self.hub_connection.send("ResolveConsensus", [])

    def send_chain(self, chain):
        self.hub_connection.send("SendChain", [chain])

    def receive_transaction(self, message):
        print(f"Received transaction: {message}")

    def consensus_resolved(self, message):
        print("Consensus resolved:", message)

    def receive_chain(self, message):
        print("Received chain:", message)

    def on_open(self):
        print("Connection opened!")

    def on_close(self):
        print("Connection closed!")

if __name__ == "__main__":
    hub_url = "http://localhost:5000/blockchainHub"
    client = SignalRClient(hub_url)
    client.start()

    transaction = {
        "transaction_id": 1,
        "document_id": 101,
        "data": "example transaction data",
        "crc": 1234567890
    }
    client.send_transaction(transaction)
