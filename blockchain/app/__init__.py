from flask import Flask
from .routes import bp
import asyncio
from threading import Thread
from .models.node_monitor import NodeMonitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    file_upload_hub = FileUploadHub()

    def start_node_monitor():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            node_monitor = NodeMonitor("http://localhost:4999")
            loop.run_until_complete(node_monitor.start_monitoring())
            loop.run_forever()
        except Exception as e:
            logger.error(f"Failed to start NodeMonitor: {e}")
    
    monitor_thread = Thread(target=start_node_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return app
