# AstroLEO: Networking Protocol for Astronomical Imaging with LEO Satellites

AstroLEO is a peer-to-peer networking protocol designed for Low Earth Orbit (LEO) satellite constellations. The system enables synchronized astronomical imaging, efficient inter-satellite communication, and robust data transfer to ground stations. This project aims to facilitate high-resolution imaging of celestial objects, including exoplanets, near-Earth objects, galaxy formations, and supernovae.

---

## Features and Contributors

### Core Functionalities

# AstroLEO: Networking Protocol for Astronomical Imaging with LEO Satellites

AstroLEO is a peer-to-peer networking protocol designed for Low Earth Orbit (LEO) satellite constellations. The system enables synchronized astronomical imaging, efficient inter-satellite communication, and robust data transfer to ground stations. This project aims to facilitate high-resolution imaging of celestial objects, including exoplanets, near-Earth objects, galaxy formations, and supernovae.

---

## Features and Contributors

- **Satellite Node Management**
  - Implements core functionalities of individual satellite nodes, including communication and data processing.
  - **Files Involved:** `app/satellite_node.py`
  - **Contributor:** Harinath Babu & Nishanth Gopinath (Collaborative)

- **Ground Station Integration**
  - Manages communication with ground stations for data upload and download.
  - **Files Involved:** `app/ground_station.py`
  - **Contributor:** Harinath Babu & Nishanth Gopinath (Collaborative)

- **Routing and Path Management**
  - Implements routing algorithms to ensure efficient data transfer between satellites and ground stations.
  - **Files Involved:** `network/route_manager.py`, `network/network_manager.py`
  - **Contributor:** Harinath Babu & Nishanth Gopinath (Collaborative)

- **Data Packet Management**
  - Handles the creation, transmission, and parsing of data packets.
  - **Files Involved:** `network/packet.py`
  - **Contributor:** Harinath Babu

- **Dynamic Network Topology Management**
  - Adjusts the network topology dynamically based on satellite positions.
  - **Files Involved:** `network/network_manager.py`
  - **Contributor:** Nishanth Gopinath

- **Time Synchronization**
  - Ensures consistent timestamps across the satellite constellation for synchronized operations.
  - **Files Involved:** `network/sync_manager.py`
  - **Contributor:** Nishanth Gopinath

- **Encryption and Key Management**
  - Secures communication using encryption protocols and key exchange mechanisms.
  - **Files Involved:** `utils/encryption_utils.py`
  - **Contributor:** Harinath Babu

- **Inter-Satellite Communication**
  - Establishes peer-to-peer communication links between satellites for distributed networking.
  - **Files Involved:** `network/network_manager.py`, `network/packet.py`
  - **Contributor:** Harinath Babu & Nishanth Gopinath (Collaborative)

- **Failure Detection and Recovery**
  - Detects satellite or communication failures and reroutes data or synchronizes remaining nodes to maintain network integrity and performance.
  - **Files Involved:** `network/route_manager.py`, `network/sync_manager.py`
  - **Contributor:** Nishanth Gopinath

- **Image Compression and Transmission**
  - Reduces image sizes for efficient transmission without significant quality loss.
  - **Files Involved:** `network/route_manager.py`, `app/satellite_node.py`
  - **Contributor:** Harinath Babu

- **Simulation Setup and Execution**
  - Includes scripts for launching simulations and running demos to visualize system capabilities.
  - **Files Involved:** `demo.py`, `run_demo.sh`, `main.py`
  - **Contributor:** Harinath Babu

- **Logging and Monitoring**
  - Tracks system performance and logs critical events for debugging and monitoring.
  - **Files Involved:** `utils/logging_utils.py`
  - **Contributor:** Nishanth Gopinath


## Project Structure

### Core Modules
- **`app/`**
  - `config.py`: Configuration settings for satellites and ground stations.
  - `satellite_node.py`: Core functionality of satellite nodes in the network.
  - `ground_station.py`: Interfaces for ground station operations.

- **`network/`**
  - `network_manager.py`: Manages the network topology and inter-satellite communication.
  - `packet.py`: Handles the creation and parsing of data packets.
  - `route_manager.py`: Implements routing algorithms.
  - `sync_manager.py`: Ensures time synchronization across the satellite constellation.

- **`utils/`**
  - `distance_utils.py`: Utilities for calculating inter-satellite distances.
  - `encryption_utils.py`: Implements encryption for secure data transmission.
  - `logging_utils.py`: Provides logging functionality for system events.

### Scripts
- `main.py`: Entry point for running the simulation.
- `launch_nodes.py`: Initializes satellite nodes in the simulation.
- `launch_stations.py`: Configures ground stations.
- `demo.py`: Demonstration script for showcasing protocol capabilities.
- `run_demo.sh`: A shell script to run the demo in a simplified and automated manner.

---

## Requirements

Install dependencies using `pip`:

```bash
pip install -r requirements.txt
```

---

## Usage

### Running the Simulation
1. Launch satellite nodes:
   ```bash
   python launch_nodes.py
   ```
2. Start ground stations:
   ```bash
   python launch_stations.py
   ```
3. Run the main simulation (launch just one satellite node or a ground station):
   ```bash
   python main.py
   ```
4. Use the HTTP endpoints to interact with the servers.

### Demonstration
To see a live demo, execute:
```bash
python demo.py
```

Alternatively, use the automated shell script:
```bash
sh run_demo.sh
```

---
