# AstroLEO: Networking Protocol for Astronomical Imaging with LEO Satellites

AstroLEO is a peer-to-peer networking protocol designed for Low Earth Orbit (LEO) satellite constellations. The system enables synchronized astronomical imaging, efficient inter-satellite communication, and robust data transfer to ground stations. This project aims to facilitate high-resolution imaging of celestial objects, including exoplanets, near-Earth objects, galaxy formations, and supernovae.

---

## Features

- **Synchronized Imaging:** Enables coordinated observations across satellites to form a virtual telescope array.
- **Inter-Satellite Communication:** Provides a peer-to-peer communication framework optimized for LEO constellations.
- **Data Compression and Aggregation:** Minimizes bandwidth usage while ensuring high-quality data transfer.
- **Fault Tolerance:** Includes adaptive fault-handling mechanisms to ensure robust operations in dynamic environments.
- **Ground Station Integration:** Seamlessly integrates with ground stations for data collection and processing.
- **AI-Assisted Imaging:** Utilizes AI for preprocessing and anomaly detection in astronomical images.

---

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

### Tests
- Multiple test cases for verifying imaging, communication, encryption, synchronization, and data transmission.

### Resources
- `ground_stations.json`: Configuration file for ground stations.
- `network_visualization.png`: Visualization of the network topology.

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
3. Run the main simulation:
   ```bash
   python main.py
   ```

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

## Testing

Run unit tests to validate the system:

```bash
pytest
```

---
