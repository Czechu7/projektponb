from signalrcore.hub_connection_builder import HubConnectionBuilder
import requests
from flask import Blueprint, jsonify, request
import zlib
import logging
from  .models.blockchain import Blockchain
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FileUploadHub:
    def __init__(self):
        self.hub_connection = HubConnectionBuilder() \
            .with_url("http://localhost:4999/hub") \
            .build()

        self.hub_connection.on_reconnect(self.on_reconnect)  

        self.hub_connection.on("UploadFile", self.receive_file)
        logger.info(f"Otrzymano2: ")
        self.blockchain = Blockchain()


    def on_reconnect(self):
        """reconnect"""
    def debug_receive(*args):
        logger.info(f"Otrzymano2: ")
    def receive_file(self, data):
        """Odbieranie pliku i zapisanie go"""
        logger.info(f"Otrzymano plik: wazne: {self.blockchain.node_address}")

        try:
            file_name, file_data, checksum = data

            transaction = {
                "transaction_id": "9",
                "document_id": "9",
                "document_type": "jpg",
                "timestamp": "15-15-10.10.2024",
                "data": file_data,
                "signature": file_name,
                "crc": zlib.crc32(file_data.encode('utf-8'))
            }

            if self.blockchain.port == 5001:
                response = requests.post(f'http://127.0.0.1:5001/transactions/new', json={'transaction': transaction})
                if response.status_code == 201:
                    logger.info("Transaction added to blockchain.")
                    # time.sleep(1)
                    response = requests.get(f'http://127.0.0.1:5001/mine')
                    # self.blockchain.mine_pending_transactions()
                else:
                    logger.warning("Transaction was not added to blockchain.")
            else:
                logger.info(f"Transakcja odrzucona - nie jest przeznaczona dla tego węzła: {self.blockchain.node_address}")

        except Exception as e:
            logger.error(f"Błąd podczas odbierania pliku: {e}")
