import sys

from app.satellite_node import initialize_node
from app.satellite_node import app as satellite_app
from app.ground_station import initialize_station
from app.ground_station import app as ground_app

def main():
    if len(sys.argv) < 5:
        print("Usage: python main.py <node_id> <x> <y> <z> <type(0/1)>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    position = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    node_type = int(sys.argv[5])
    
    if (node_type == 0):
        initialize_node(node_id, position)
        satellite_app.run(host='0.0.0.0', port=5000 + node_id)
    if (node_type == 1):
        initialize_station(node_id, position)
        ground_app.run(host='0.0.0.0', port=6000 + node_id)

if __name__ == "__main__":
    main()
