import sys
from flask import Flask
from app.satellite_node import initialize_node
from app.routes import routes

app = Flask(__name__)
app.register_blueprint(routes)

def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <node_id> <x> <y> <z>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    position = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    initialize_node(node_id, position)
    
    # Run the Flask app on the calculated port based on node_id
    app.run(host='0.0.0.0', port=5000 + node_id)

if __name__ == "__main__":
    main()
