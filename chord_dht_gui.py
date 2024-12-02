# chord_dht_gui_fixed.py

import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for embedding in Tkinter

import hashlib
import threading
import time
import random
import sys
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.lines import Line2D

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# Constants
M = 5  # Number of bits in the identifier space (0 to 31)
R = 3 # Replication factor (Adjusted to 2 for reliability in small rings)


def hash_key(key):
    """Generate a hash for the given key and map it to the identifier space."""
    h = int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2 ** M)
    print(h)
    return h


def in_interval(start, end, id_, inclusive_start=False, inclusive_end=False):
    """Check if id_ is in interval (start, end) on the ring modulo 2^M."""
    if start == end:
        # The interval is the entire ring
        return True
    elif start < end:
        if inclusive_start and inclusive_end:
            return start <= id_ <= end
        elif inclusive_start:
            return start <= id_ < end
        elif inclusive_end:
            return start < id_ <= end
        else:
            return start < id_ < end
    else:
        # The interval wraps around
        if inclusive_start and inclusive_end:
            return id_ >= start or id_ <= end
        elif inclusive_start:
            return id_ >= start or id_ < end
        elif inclusive_end:
            return id_ > start or id_ <= end
        else:
            return id_ > start or id_ < end


class Node:
    def __init__(self, identifier, dht):
        self.id = identifier
        self.dht = dht
        self.finger = [None] * M
        self.successor = self
        self.predecessor = None
        self.data = {}
        self.lock = threading.Lock()
        self.alive = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while self.alive:
            time.sleep(1)
            self.stabilize()
            self.fix_fingers()
            self.check_predecessor()

    def find_successor(self, id_):
        pred = self.find_predecessor(id_)
        return pred.successor

    def find_predecessor(self, id_):
        n = self
        while not in_interval(n.id, n.successor.id, id_, inclusive_end=True):
            n = n.closest_preceding_finger(id_)
            if n == self:
                break  # Avoid infinite loop
        return n

    def closest_preceding_finger(self, id_):
        for i in reversed(range(M)):
            finger = self.finger[i]
            if finger and finger.alive and in_interval(self.id, id_, finger.id):
                return finger
        return self

    def stabilize(self):
        x = self.successor.predecessor
        if x and x.alive and in_interval(self.id, self.successor.id, x.id):
            self.successor = x
            logging.info(f"Node {self.id}: Successor updated to Node {x.id}")
        self.successor.notify(self)

    def notify(self, n):
        if self.predecessor is None or in_interval(self.predecessor.id, self.id, n.id):
            self.predecessor = n
            logging.info(f"Node {self.id}: Predecessor updated to Node {n.id}")
            # Transfer data to new predecessor if necessary
            with self.lock:
                keys_to_transfer = [
                    k for k in self.data
                    if in_interval(self.predecessor.id, self.id, hash_key(k), inclusive_end=True)
                ]
                for k in keys_to_transfer:
                    n.store(k, self.data[k])
                    del self.data[k]
                    logging.info(f"Node {self.id}: Transferred key '{k}' to Node {n.id}")

    def fix_fingers(self):
        for i in range(M):
            start = (self.id + 2 ** i) % (2 ** M)
            self.finger[i] = self.find_successor(start)
            logging.debug(f"Node {self.id}: Finger[{i}] set to Node {self.finger[i].id}")

    def check_predecessor(self):
        if self.predecessor and not self.predecessor.alive:
            logging.info(f"Node {self.id}: Predecessor Node {self.predecessor.id} is dead.")
            self.predecessor = None

    def join(self, known_node):
        if known_node:
            self.init_finger_table(known_node)
            self.update_others()
            self.move_keys()
        else:
            for i in range(M):
                self.finger[i] = self
            self.successor = self
            self.predecessor = self
            logging.info(f"Node {self.id}: Joined as the only node in the DHT.")

    def init_finger_table(self, known_node):
        self.finger[0] = known_node.find_successor((self.id + 1) % (2 ** M))
        self.successor = self.finger[0]
        self.predecessor = self.successor.predecessor
        if self.successor.predecessor and self.successor.predecessor != self:
            self.successor.predecessor = self
            logging.info(f"Node {self.id}: Updated Node {self.successor.id}'s predecessor to Node {self.id}")
        logging.info(f"Node {self.id}: Initialized finger[0] to Node {self.finger[0].id}")
        for i in range(M - 1):
            start = (self.id + 2 ** (i + 1)) % (2 ** M)
            if in_interval(self.id, self.finger[i].id, start, inclusive_start=True):
                self.finger[i + 1] = self.finger[i]
            else:
                self.finger[i + 1] = known_node.find_successor(start)
            logging.info(f"Node {self.id}: Initialized finger[{i + 1}] to Node {self.finger[i + 1].id}")

    def update_others(self):
        for i in range(M):
            pred_id = (self.id - 2 ** i) % (2 ** M)
            p = self.find_predecessor(pred_id)
            if p != self:
                p.update_finger_table(self, i)

    def update_finger_table(self, s, i):
        if in_interval(self.id, self.finger[i].id, s.id, inclusive_end=True):
            self.finger[i] = s
            logging.info(f"Node {self.id}: Finger[{i}] updated to Node {s.id}")
            p = self.predecessor
            if p and p != self:
                p.update_finger_table(s, i)

    def move_keys(self):
        with self.successor.lock:
            keys_to_move = [
                k for k in self.successor.data
                if in_interval(self.id, self.successor.id, hash_key(k), inclusive_end=True)
            ]
            for k in keys_to_move:
                self.data[k] = self.successor.data[k]
                del self.successor.data[k]
                logging.info(f"Node {self.id}: Moved key '{k}' from Node {self.successor.id}")

    def store(self, key, value):
        with self.lock:
            self.data[key] = value
            logging.info(f"Node {self.id}: Stored key '{key}' with value '{value}'")

    def retrieve(self, key):
        with self.lock:
            return self.data.get(key, None)

    def leave(self):
        self.alive = False
        # Transfer keys to successor
        with self.lock:
            for k, v in self.data.items():
                self.successor.store(k, v)
                logging.info(f"Node {self.id}: Transferred key '{k}' to Node {self.successor.id}")
        # Update predecessor and successor
        if self.predecessor and self.predecessor != self:
            self.predecessor.successor = self.successor
            logging.info(f"Node {self.id}: Updated predecessor Node {self.predecessor.id}'s successor to Node {self.successor.id}")
        if self.successor and self.successor != self:
            self.successor.predecessor = self.predecessor
            logging.info(f"Node {self.id}: Updated successor Node {self.successor.id}'s predecessor to Node {self.predecessor.id}")


class DHT:
    def __init__(self):
        self.nodes = {}
        self.lock = threading.Lock()

    def add_node(self, node_id=None):
        with self.lock:
            if node_id is None:
                node_id = random.randint(0, 2 ** M - 1)
                while node_id in self.nodes:
                    node_id = random.randint(0, 2 ** M - 1)
            new_node = Node(node_id, self)
            if not self.nodes:
                new_node.join(None)
            else:
                known_node = random.choice(list(self.nodes.values()))
                new_node.join(known_node)
            self.nodes[node_id] = new_node
            logging.info(f"DHT: Node {node_id} added to the DHT.")
            return new_node

    def remove_node(self, node_id):
        with self.lock:
            node = self.nodes.get(node_id)
            if node:
                node.leave()
                del self.nodes[node_id]
                logging.info(f"DHT: Node {node_id} removed from the DHT.")
            else:
                logging.warning(f"DHT: Node {node_id} not found.")

    def store(self, key, value):
        with self.lock:
            replicas = min(R, len(self.nodes))
        if replicas == 0:
            logging.warning("DHT: No nodes in the DHT.")
            return False
        node = random.choice(list(self.nodes.values()))
        succ = node.find_successor(hash_key(key))
        succ.store(key, value)
        # Replication
        replica = succ.successor
        replicas_added = 1
        while replicas_added < replicas:
            if replica == succ:
                break
            replica.store(key, value)
            replicas_added += 1
            replica = replica.successor
        logging.info(f"DHT: Key '{key}' stored in the DHT with value '{value}'.")
        return True

    def retrieve(self, key):
        with self.lock:
            replicas = min(R, len(self.nodes))
        if replicas == 0:
            logging.warning("DHT: No nodes in the DHT.")
            return None
        node = random.choice(list(self.nodes.values()))
        succ = node.find_successor(hash_key(key))
        for _ in range(replicas):
            value = succ.retrieve(key)
            if value is not None:
                logging.info(f"DHT: Retrieved key '{key}' from Node {succ.id} with value '{value}'.")
                return value
            succ = succ.successor
            if succ == node.find_successor(hash_key(key)):
                break
        logging.warning(f"DHT: Key '{key}' not found in any replicas.")
        return None

    def get_ring(self):
        """Returns a list of node IDs sorted in the ring order."""
        with self.lock:
            if not self.nodes:
                return []
            sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.id)
            return [node.id for node in sorted_nodes]

    def get_finger_table(self, node_id):
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [finger.id for finger in node.finger if finger]


class ChordVisualizer:
    def __init__(self, parent_frame, dht):
        self.dht = dht
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.G = nx.DiGraph()
        self.pos = {}
        self.ani = FuncAnimation(self.fig, self.update, interval=1000, save_count=50)

    def update(self, frame):
        self.G.clear()
        ring = self.dht.get_ring()
        if not ring:
            self.ax.clear()
            self.ax.set_title("Chord DHT Ring (No Nodes)")
            self.ax.axis('off')
            self.canvas.draw()
            return
        # Position nodes in a circle
        self.pos = {}
        angle_step = 360 / len(ring)
        radius = 10
        for idx, node_id in enumerate(ring):
            angle = angle_step * idx
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            self.pos[node_id] = (x, y)
            self.G.add_node(node_id)
        # Add edges for successors (ring)
        for node_id in ring:
            node = self.dht.nodes[node_id]
            succ = node.successor
            if succ and succ.alive:
                succ_id = succ.id
                if succ_id != node_id and succ_id in self.pos:
                    self.G.add_edge(node_id, succ_id, color='blue', style='solid')
        # Add edges for finger tables
        for node_id in ring:
            finger_table = self.dht.get_finger_table(node_id)
            for finger_id in finger_table:
                if finger_id != node_id and finger_id in self.pos:
                    self.G.add_edge(node_id, finger_id, color='red', style='dashed')
        # Draw the graph
        self.ax.clear()
        edges = self.G.edges(data=True)
        colors = [edge[2]['color'] for edge in edges]
        styles = [edge[2]['style'] for edge in edges]

        # Separate edges by style for different drawing
        solid_edges = [edge for edge in edges if edge[2]['style'] == 'solid']
        dashed_edges = [edge for edge in edges if edge[2]['style'] == 'dashed']

        # Draw solid edges (successors)
        if solid_edges:
            nx.draw_networkx_edges(
                self.G, self.pos, edgelist=solid_edges,
                edge_color='blue', arrows=True,
                arrowstyle='-|>', arrowsize=30, connectionstyle='arc3,rad=0.1',
                width=2
            )
        # Draw dashed edges (finger tables)
        if dashed_edges:
            nx.draw_networkx_edges(
                self.G, self.pos, edgelist=dashed_edges,
                edge_color='red', style='dashed', arrows=True,
                arrowstyle='-|>', arrowsize=25, connectionstyle='arc3,rad=0.2',
                width=2
            )
        # Draw nodes
        nx.draw_networkx_nodes(
            self.G, self.pos,
            node_color='lightblue', node_size=1000, edgecolors='black', linewidths=1.5
        )
        # Draw labels
        nx.draw_networkx_labels(
            self.G, self.pos,
            font_size=12, font_weight='bold'
        )
        # Create custom legend
        legend_elements = [
            Line2D([0], [0], color='blue', lw=2, label='Successor', linestyle='solid'),
            Line2D([0], [0], color='red', lw=2, label='Finger Table', linestyle='dashed')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')

        self.ax.set_title("Chord DHT Ring")
        self.ax.axis('off')
        self.canvas.draw()


class ChordDHTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chord DHT Simulation")
        self.dht = DHT()

        # Setup GUI layout
        self.setup_gui()

    def setup_gui(self):
        # Frames
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        visualization_frame = ttk.Frame(self.root, padding="10")
        visualization_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Control Widgets
        # Add Node
        add_node_label = ttk.Label(control_frame, text="Add Node", font=('Helvetica', 10, 'bold'))
        add_node_label.pack(pady=5)

        add_node_id_label = ttk.Label(control_frame, text="Node ID (optional):")
        add_node_id_label.pack()
        self.add_node_id_entry = ttk.Entry(control_frame)
        self.add_node_id_entry.pack(pady=5)
        add_node_button = ttk.Button(control_frame, text="Add Node", command=self.add_node)
        add_node_button.pack(pady=5)

        # Remove Node
        remove_node_label = ttk.Label(control_frame, text="Remove Node", font=('Helvetica', 10, 'bold'))
        remove_node_label.pack(pady=10)

        remove_node_id_label = ttk.Label(control_frame, text="Node ID:")
        remove_node_id_label.pack()
        self.remove_node_id_entry = ttk.Entry(control_frame)
        self.remove_node_id_entry.pack(pady=5)
        remove_node_button = ttk.Button(control_frame, text="Remove Node", command=self.remove_node)
        remove_node_button.pack(pady=5)

        # Store Key-Value
        store_kv_label = ttk.Label(control_frame, text="Store Key-Value", font=('Helvetica', 10, 'bold'))
        store_kv_label.pack(pady=10)

        store_key_label = ttk.Label(control_frame, text="Key:")
        store_key_label.pack()
        self.store_key_entry = ttk.Entry(control_frame)
        self.store_key_entry.pack(pady=5)

        store_value_label = ttk.Label(control_frame, text="Value:")
        store_value_label.pack()
        self.store_value_entry = ttk.Entry(control_frame)
        self.store_value_entry.pack(pady=5)

        store_button = ttk.Button(control_frame, text="Store", command=self.store_key)
        store_button.pack(pady=5)

        # Retrieve Key
        retrieve_kv_label = ttk.Label(control_frame, text="Retrieve Key", font=('Helvetica', 10, 'bold'))
        retrieve_kv_label.pack(pady=10)

        retrieve_key_label = ttk.Label(control_frame, text="Key:")
        retrieve_key_label.pack()
        self.retrieve_key_entry = ttk.Entry(control_frame)
        self.retrieve_key_entry.pack(pady=5)
        retrieve_button = ttk.Button(control_frame, text="Retrieve", command=self.retrieve_key)
        retrieve_button.pack(pady=5)

        # Query Node Successor and Predecessor
        query_node_label = ttk.Label(control_frame, text="Query Node", font=('Helvetica', 10, 'bold'))
        query_node_label.pack(pady=10)

        query_node_id_label = ttk.Label(control_frame, text="Node ID:")
        query_node_id_label.pack()
        self.query_node_id_entry = ttk.Entry(control_frame)
        self.query_node_id_entry.pack(pady=5)
        query_node_button = ttk.Button(control_frame, text="Find Successor & Predecessor", command=self.query_node)
        query_node_button.pack(pady=5)

        # Successor and Predecessor Display
        self.query_result_label = ttk.Label(control_frame, text="", foreground="blue")
        self.query_result_label.pack(pady=5)

        # Status Display
        status_label = ttk.Label(control_frame, text="Status", font=('Helvetica', 10, 'bold'))
        status_label.pack(pady=10)

        self.status_text = tk.Text(control_frame, height=15, width=30, state='disabled')
        self.status_text.pack(pady=5)

        # Visualization
        self.visualizer = ChordVisualizer(visualization_frame, self.dht)

        # Start a thread to update status
        self.update_status_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.update_status_thread.start()

    def add_node(self):
        node_id_str = self.add_node_id_entry.get().strip()
        if node_id_str:
            try:
                node_id = int(node_id_str)
                if node_id < 0 or node_id >= 2 ** M:
                    messagebox.showerror("Error", f"Node ID must be between 0 and {2 ** M -1}.")
                    return
                with self.dht.lock:
                    if node_id in self.dht.nodes:
                        messagebox.showerror("Error", f"Node ID {node_id} already exists.")
                        return
                self.dht.add_node(node_id)
                self.log_status(f"Added node {node_id}.")
            except ValueError:
                messagebox.showerror("Error", "Node ID must be an integer.")
                return
        else:
            new_node = self.dht.add_node()
            self.log_status(f"Added a node with ID {new_node.id}.")

        self.add_node_id_entry.delete(0, tk.END)

    def remove_node(self):
        node_id_str = self.remove_node_id_entry.get().strip()
        if not node_id_str:
            messagebox.showerror("Error", "Please enter a Node ID to remove.")
            return
        try:
            node_id = int(node_id_str)
            with self.dht.lock:
                if node_id not in self.dht.nodes:
                    messagebox.showerror("Error", f"Node ID {node_id} does not exist.")
                    return
            self.dht.remove_node(node_id)
            self.log_status(f"Removed node {node_id}.")
        except ValueError:
            messagebox.showerror("Error", "Node ID must be an integer.")
            return
        self.remove_node_id_entry.delete(0, tk.END)

    def store_key(self):
        key = self.store_key_entry.get().strip()
        value = self.store_value_entry.get().strip()
        if not key or not value:
            messagebox.showerror("Error", "Please enter both key and value.")
            return
        success = self.dht.store(key, value)
        if success:
            self.log_status(f"Stored key '{key}' with value '{value}'.")
        else:
            self.log_status("Failed to store key-value pair.")
        self.store_key_entry.delete(0, tk.END)
        self.store_value_entry.delete(0, tk.END)

    def retrieve_key(self):
        key = self.retrieve_key_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter a key to retrieve.")
            return
        value = self.dht.retrieve(key)
        if value is not None:
            self.log_status(f"Retrieved key '{key}': {value}")
            messagebox.showinfo("Retrieve", f"Key '{key}' has value '{value}'.")
        else:
            self.log_status(f"Key '{key}' not found.")
            messagebox.showinfo("Retrieve", f"Key '{key}' not found.")
        self.retrieve_key_entry.delete(0, tk.END)

    def query_node(self):
        node_id_str = self.query_node_id_entry.get().strip()
        if not node_id_str:
            messagebox.showerror("Error", "Please enter a Node ID to query.")
            return
        try:
            node_id = int(node_id_str)
            with self.dht.lock:
                if node_id not in self.dht.nodes:
                    messagebox.showerror("Error", f"Node ID {node_id} does not exist.")
                    self.query_result_label.config(text="")
                    return
                node = self.dht.nodes[node_id]
                successor = node.successor.id if node.successor else "None"
                predecessor = node.predecessor.id if node.predecessor else "None"
            result_text = f"Node {node_id}:\nSuccessor: {successor}\nPredecessor: {predecessor}"
            self.query_result_label.config(text=result_text)
            self.log_status(f"Queried Node {node_id}: Successor={successor}, Predecessor={predecessor}")
        except ValueError:
            messagebox.showerror("Error", "Node ID must be an integer.")
            self.query_result_label.config(text="")
            return
        self.query_node_id_entry.delete(0, tk.END)

    def log_status(self, message):
        self.status_text.configure(state='normal')
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.configure(state='disabled')

    def update_status_loop(self):
        while True:
            # Periodically update status or handle logs if needed
            time.sleep(1)
            # For this implementation, status updates are handled immediately
            # via log_status method
            pass


def main():
    root = tk.Tk()
    app = ChordDHTApp(root)
    root.mainloop()


if __name__ == "__main__":
    print(f"Matplotlib is using the '{matplotlib.get_backend()}' backend.")
    main()
