# Chord DHT GUI Simulation

A graphical simulation of the Chord Distributed Hash Table (DHT) using Python, Tkinter, NetworkX, and Matplotlib. This application allows users to interactively add and remove nodes, store and retrieve key-value pairs, and visualize the Chord ring and finger tables in real-time.

## Features

- **Add Nodes**: Insert new nodes into the Chord ring with optional custom identifiers.
- **Remove Nodes**: Dynamically remove existing nodes from the ring.
- **Store Key-Value Pairs**: Distribute and replicate key-value pairs across the DHT.
- **Retrieve Keys**: Fetch values associated with specific keys from the DHT.
- **Query Nodes**: View the successor and predecessor of any node in the ring.
- **Real-Time Visualization**: Interactive graphical representation of the Chord ring and finger tables.

## Requirements

- Python 3.x
- Tkinter
- Matplotlib
- NetworkX
- NumPy

## Installation



**Install Dependencies**

   Ensure you have the required Python libraries installed. You can install them using `pip`:

   ```bash
   pip install matplotlib networkx numpy
   ```

   *Note: Tkinter is usually included with standard Python installations. If not, refer to your operating system's instructions to install Tkinter.*

## Usage

Run the `chord_dht_gui.py` script using Python:

```bash
python chord_dht_gui.py
```

### GUI Components

- **Add Node**
  - **Node ID (optional)**: Enter a specific identifier for the new node. If left blank, a random ID is assigned.
  - **Add Node Button**: Adds the node to the Chord ring.

- **Remove Node**
  - **Node ID**: Enter the identifier of the node you wish to remove.
  - **Remove Node Button**: Removes the specified node from the ring.

- **Store Key-Value**
  - **Key**: Enter the key to store.
  - **Value**: Enter the corresponding value.
  - **Store Button**: Stores the key-value pair in the DHT with replication.

- **Retrieve Key**
  - **Key**: Enter the key you want to retrieve.
  - **Retrieve Button**: Fetches the value associated with the key from the DHT.

- **Query Node**
  - **Node ID**: Enter the identifier of the node you want to query.
  - **Find Successor & Predecessor Button**: Displays the successor and predecessor of the specified node.

- **Status Display**
  - Shows real-time logs and status messages related to DHT operations.

- **Visualization Panel**
  - Displays the Chord ring and finger tables, updating in real-time as nodes are added or removed.

## Configuration

- **Identifier Space**
  - The identifier space is defined by `M = 5`, allowing node IDs from `0` to `31`.

- **Replication Factor**
  - The replication factor is set to `R = 3`, meaning each key-value pair is stored on three consecutive nodes in the ring for redundancy.

## Logging

The application uses Python's `logging` module to provide detailed information about DHT operations. Logs are displayed in the Status section of the GUI.

