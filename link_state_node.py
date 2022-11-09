import collections
import heapq
import json
import sys
import heapq as heap

from simulator.node import Node


class Edges:
    def __init__(self, latency: int, seq_num: int):
        self.latency = latency
        self.seq_num = seq_num
class Nodes:
    def __init__(self, nodes_id: int):
        self.nodes_id = nodes_id
        # key: neighbor, value: cost
        self.neighbors = {}
        self.dist = sys.maxsize
    def addNeighbors(self, neighbor_id:int, latency:int):
        # if neighbor_id not in self.neighbors.keys():
        self.neighbors[neighbor_id] = latency
    def __lt__(self, nodes_two):
        return self.dist < nodes_two.dist
class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.edges = {}
        self.nodes = {}

    # Return a string
    def __str__(self):
        message = {}
        for edge, value in self.edges.items():
            cur = tuple(edge)
            newEdges = str(cur)
            if cur[0] == self.id:
                newEdges = str((cur[1], cur[0]))
            message[newEdges] = {
                                    "latency": value.latency,
                                    "seq_num": value.seq_num
                                }
        return json.dumps(message)

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        self.edges[frozenset((self.id, neighbor))] = Edges(latency, self.get_time())
        self.send_to_neighbors(str(self))
    # Fill in this function
    def process_incoming_routing_message(self, m):
        should_update = False
        new_edges = json.loads(m)
        for cur_key, value in new_edges.items():
            key_array = cur_key[1:-1].split(',')
            key_array_pair = (int(key_array[0]), int(key_array[1]))
            key = tuple(key_array_pair)
            if self.check_edge(source=key[0], destination=key[1], new_edge=Edges(int(value["latency"]), int(value["seq_num"]))):
                should_update = True
        if should_update:
            self.send_to_neighbors(str(self))
    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        prev, dist = self.dijkstra()
        cur_vertice = destination
        next_hop = None
        while cur_vertice != self.id:
            next_hop = cur_vertice
            if cur_vertice not in prev.keys() or prev[cur_vertice] is None:
                return -1
            cur_vertice = prev[cur_vertice]
        return next_hop

    def check_edge(self, source: int, destination: int, new_edge: Edges) -> bool:
        if (frozenset((source, destination)) in self.edges and new_edge.seq_num >
                self.edges[frozenset((source, destination))].seq_num) or frozenset((
                source, destination)) not in self.edges:
            self.edges[frozenset((source, destination))] = Edges(new_edge.latency, new_edge.seq_num)
            return True
        return False

    # build nodes
    def dijkstra_preprocessing(self):
        self.nodes = {}
        for frozen_edge, val in self.edges.items():

            if val.latency < 0:
                continue
            frozen_edge = tuple(frozen_edge)
            edge_source = frozen_edge[0]
            edge_destination = frozen_edge[1]
            if edge_source not in self.nodes.keys():
                self.nodes[edge_source] = Nodes(edge_source)
            if edge_destination not in self.nodes.keys():
                self.nodes[edge_destination] = Nodes(edge_destination)
            self.nodes[edge_destination].addNeighbors(edge_source, val.latency)
            self.nodes[edge_source].addNeighbors(edge_destination, val.latency)
    def dijkstra(self):
        self.dijkstra_preprocessing()
        visited = set()
        prev = {}
        pq = []
        dist = collections.defaultdict(lambda: sys.maxsize)
        dist[self.id] = 0
        self.nodes[self.id].dist = 0
        heapq.heappush(pq, self.nodes[self.id])

        while pq:
            cur_node = heapq.heappop(pq)
            if cur_node.nodes_id in visited:
                continue
            visited.add(cur_node.nodes_id)

            for id, latency in cur_node.neighbors.items():
                if id in visited:
                    continue
                newLatency = dist[cur_node.nodes_id] + latency
                if dist[id] > newLatency:
                    prev[id] = cur_node.nodes_id
                    dist[id] = newLatency
                    new_node = Nodes(id)
                    new_node.neighbors = self.nodes[id].neighbors
                    new_node.dist = newLatency
                    heapq.heappush(pq, new_node)

        return prev, dist
