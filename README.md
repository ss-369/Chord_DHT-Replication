# Chord DHT Replication with Visualization

## Overview
This project implements a **Chord Distributed Hash Table (DHT)**, a scalable and robust peer-to-peer lookup protocol. It includes a graphical user interface (GUI) for easy interaction and visualization of the DHT ring structure, allowing users to simulate node addition, removal, key-value storage, retrieval, and replication.

The implementation supports:
- **Node Joins/Leaves** with consistent hashing.
- **Replication** for reliability.
- **Key-Value Storage and Retrieval** using hash-based lookup.
- **Finger Table Visualization** for efficient lookup paths.

## Features
- **Chord Protocol Implementation**:
  - Node stabilization, finger table setup, and successor/predecessor updates.
  - Robust and fault-tolerant structure using replication.
- **Replication Factor**: Configurable for fault tolerance.
- **Interactive GUI**:
  - Visualize the Chord ring and finger table connections.
  - Add/remove nodes and perform operations on the DHT.
- **Visualization**:
  - Graphical representation of nodes and their connections.
  - Custom edge styles to differentiate between successor links and finger tables.

## Screenshots
| Feature       | Description |
|---------------|-------------|
| ![Ring](#)    | **Chord Ring Visualization**: Nodes and connections between them. |
| ![GUI](#)     | **Interactive GUI**: Controls for adding/removing nodes, storing, and retrieving keys. |

## Installation

### Prerequisites
- **Python 3.8+**
- Libraries:
  - `matplotlib`
  - `networkx`
  - `tkinter`

### Installation Steps
1. Clone the repository:
   ```bash
   git clone git@github.com:ss-369/Chord_DHT-Replication.git
   cd Chord_DHT-Replication
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   *(If `requirements.txt` is not available, manually install: `matplotlib`, `networkx`, `numpy`.)*

3. Run the application:
   ```bash
   python chord_dht_gui_fixed.py
   ```

## Usage

### GUI Controls
- **Add Node**:
  - Add a node to the DHT by entering an optional ID or letting the system generate one.
- **Remove Node**:
  - Remove a specific node by entering its ID.
- **Store Key-Value**:
  - Store a key-value pair in the DHT. The key is hashed to determine its location.
- **Retrieve Key**:
  - Retrieve the value associated with a key.
- **Query Node**:
  - Display a node's successor and predecessor in the DHT.

### Visualization
- Nodes are displayed in a circular layout.
- **Blue Edges**: Successor links.
- **Red Dashed Edges**: Finger table connections.

## Key Concepts

### Chord Protocol
- **Consistent Hashing**:
  - Nodes and keys are mapped to an identifier space (0 to \(2^M - 1\)).
- **Finger Table**:
  - Provides shortcuts for faster lookups in \(O(\log N)\) time.
- **Replication**:
  - Ensures fault tolerance by storing data on multiple nodes.

### Replication Factor
The replication factor \(R\) is configurable. A higher \(R\) increases fault tolerance but consumes more storage.

### GUI Components
1. **Control Panel**:
   - Buttons and text fields for interaction.
2. **Visualization**:
   - Dynamic graph showing the Chord ring and connections.

## File Structure
```
Chord_DHT-Replication/
├── chord_dht_gui_fixed.py      # Main application with GUI
├── README.md                   # Project documentation
├── requirements.txt            # Dependencies
└── assets/                     # Images or other resources
```

## Customization
### Modify Ring Size
The identifier space can be adjusted by changing `M`:
```python
M = 5  # Number of bits (0-31 range)
```

### Replication Factor
Update the replication factor for fault tolerance:
```python
R = 3  # Replication factor
```

### Logging
Enable or adjust logging levels:
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
```

## Contributing
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
This project was inspired by the [Chord DHT protocol](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) and aims to provide an educational tool for understanding its core principles.
