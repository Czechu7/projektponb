from app import create_app
import argparse

parser = argparse.ArgumentParser(description='Blockchain Node')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask app on')
args = parser.parse_args()

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port)
