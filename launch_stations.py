import subprocess
import time
import random
import json
import os

from app.config import NUM_GROUND_STATIONS, GROUND_STATION_POSITIONS_FILE


def generate_ground_station_positions(num_stations):
    """
    Generate random positions for ground stations and save them to a file.
    """
    positions = {station_id: (round(random.uniform(0, 10), 2),
                              round(random.uniform(0, 10), 2),
                              round(random.uniform(0, 10), 2))
                 for station_id in range(1, num_stations + 1)}
    with open(GROUND_STATION_POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)
    return positions

def launch_ground_stations(num_stations=NUM_GROUND_STATIONS):
    """
    Launch multiple ground stations as separate processes.
    """
    positions = generate_ground_station_positions(num_stations)
    os.makedirs("logs", exist_ok=True)
    processes = []

    try:
        for station_id, position in positions.items():
            x, y, z = position
            cmd = ["python", "main.py", str(station_id), str(x), str(y), str(z), str(1)]
            log_file_path = f"logs/ground_station_{station_id}.log"
            with open(log_file_path, "w") as log_file:
                process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
                processes.append(process)
            
            print(f"Launching Ground Station {station_id} at position {position}")
            time.sleep(0.5)
            
        time.sleep(1)

        # Keep the script running to monitor processes
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"Error launching ground stations: {e}")
    finally:
        for process in processes:
            process.terminate()
        print("All ground stations terminated.")

if __name__ == "__main__":
    launch_ground_stations()
