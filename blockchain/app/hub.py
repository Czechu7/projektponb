
from signalrcore.hub_connection_builder import HubConnectionBuilder
import requests
from flask import Blueprint, jsonify, request
import zlib
import logging
from  .models.blockchain import Blockchain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FileUploadHub:
    def __init__(self):
        self.hub_connection = HubConnectionBuilder() \
            .with_url("http://localhost:8081/hub") \
            .build()

        self.hub_connection.on_reconnect(self.on_reconnect)  

        self.hub_connection.on("UploadFile", self.receive_file)
        logger.info(f"Otrzymano2: {self.receive_file}")
        self.blockchain = Blockchain()


    def on_reconnect(self):
        """reconnect"""
    def debug_receive(*args):
        logger.info(f"Otrzymano2: ", args)
    def receive_file(self, data):
        """Odbieranie pliku i zapisanie go"""
        try:
            file_name, checksum = data
            logger.info(f"Otrzymano plik: {file_name}, checksum = {checksum}")

           
            transaction = {
                "data": file_name,  
                "checksum": checksum,
                "crc": zlib.crc32(file_name.encode('utf-8'))
            }

            
            added = self.blockchain.add_transaction(transaction)
            if added:
                logger.info(f"Transaction {transaction} added to blockchain.")
            else:
                logger.warning(f"Transaction {transaction} was not added to blockchain.")

        except Exception as e:
            logger.error(f"Błąd podczas odbierania pliku: {e}")
    #to cos tam dziala
    # def receive_file(self, data):
    #     """Odbieranie pliku i zapisanie go"""
    #     file_name, checksum = data
    #     logger.info(f"Otrzymano plik: {file_name}, checksum = {checksum}")


#to nie
        # file_path = os.path.join(UPLOAD_FOLDER, file_name)
        # with open(file_path, "wb") as f:
        #     f.write(file_bytes)  # Zapisz dane byte[]

        # logger.info(f"File {file_name} saved at {file_path}")

        # file_hash = hashlib.sha256(file_bytes).hexdigest()
        # logger.debug(f"File hash: {file_hash}")

        # transaction = {
        #     "file_name": file_name,
        #     "file_hash": file_hash,
        #     "timestamp": time.time(),
        #     "crc": zlib.crc32(file_name.encode('utf-8'))
        # }

        # Jeśli masz blockchain zdefiniowany, to tutaj dodasz transakcję.
        # if blockchain.add_transaction(transaction):
        #     logger.info(f"Transaction for {file_name} added successfully to blockchain")
        # else:
        #     logger.warning(f"Failed to add transaction for {file_name} to blockchain")
