import copy
import json
import math

from simulator.node import Node


class Distance_Vector:
    def __init__(self, cost: int, path: list):
        self.cost = cost
        self.path = path

    def __eq__(self, another):
        return self.cost == another.cost and self.path == another.path


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vectors_self = {}
        self.distance_vectors_neighbor = {}
        self.sequence_number = 0
        self.neighbor_link_cost = {}
        self.neighbor_sequence_numbers = {}

    def __str__(self): #done
        message = {}
        message["self_sequence_number"] = self.sequence_number
        self.sequence_number += 1
        for dst, val in self.distance_vectors_self.items():
            dict = {}
            dict["path"] = val.path
            dict["cost"] = val.cost
            message[dst] = dict
        return json.dumps(message)

    def link_has_been_updated(self, neighbor, latency):
        if latency == -1:
            self.delete_link(neighbor)
        else:
            self.neighbor_link_cost[neighbor] = latency
        self.update_dvs()

    def delete_link(self,neighbor: int):
        self.neighbor_link_cost.pop(neighbor)
        self.distance_vectors_neighbor.pop(neighbor)
        self.distance_vectors_self.pop(neighbor)

    def update_dvs(self):
        old_dvs = copy.deepcopy(self.distance_vectors_self)
        self.distance_vectors_self = {}
        self.update_self_neighbour()
        for source, dvs in self.distance_vectors_neighbor.items():
            for destination, dv in dvs.items():
                if source in self.neighbor_link_cost:
                    new_cost = self.neighbor_link_cost[source] + dv.cost
                    if destination not in self.distance_vectors_self:
                        self.update_cost(destination,dv,new_cost)
                    if destination in self.distance_vectors_self and new_cost < self.distance_vectors_self[destination].cost:
                        self.update_cost(destination, dv, new_cost)
        if self.distance_vectors_self != old_dvs: #eq
            self.send_to_neighbors(str(self))

    def update_self_neighbour(self):
        for neighbor, link_cost in self.neighbor_link_cost.items():
            path = [self.id, neighbor]
            self.distance_vectors_self[neighbor] = Distance_Vector(link_cost, path)

    def update_cost(self, dst:int, dv:Distance_Vector, newcost:int):
        new_path = [self.id] + copy.deepcopy(dv.path)
        self.distance_vectors_self[dst] = Distance_Vector(newcost, new_path)
    # Fill in this function



    def process_incoming_routing_message(self, m):
        distance_vector_neighbor_message,sequence_number = self.processJson(m)
        flag = False
        id1 = next(iter(distance_vector_neighbor_message))
        id2 = "path"
        neighbor = int(distance_vector_neighbor_message[id1][id2][0])
        to_delete = []
        if neighbor not in self.distance_vectors_neighbor:
            self.distance_vectors_neighbor[neighbor] = {}
        if neighbor in self.neighbor_sequence_numbers:
            if sequence_number < self.neighbor_sequence_numbers[neighbor]:
                return
        for dst, value in self.distance_vectors_neighbor[neighbor].items():
            if(str(dst) not in distance_vector_neighbor_message):
                to_delete.append(dst)
        for dst_str, value in distance_vector_neighbor_message.items():
            dst = int(dst_str)
            link = Distance_Vector(value['cost'], value['path'])

            looped = (self.id in link.path)
            if(not ((dst not in self.distance_vectors_neighbor[neighbor]) and looped)):
                flag = True
            if (dst in self.distance_vectors_neighbor[neighbor]):
                if(looped):
                    self.distance_vectors_neighbor[neighbor].pop(dst) #distance_vectors_neighbor is the dict of dict
                else:
                    self.distance_vectors_neighbor[neighbor][dst] = link
            else:
                if(not looped):
                    self.distance_vectors_neighbor[neighbor][dst] = link


        if(len(to_delete) > 0):
            flag = True
        for dst in to_delete:
            self.distance_vectors_neighbor[neighbor].pop(dst)
        self.neighbor_sequence_numbers[neighbor] = sequence_number
        if flag:
            self.update_dvs()

    def processJson(self,m):
        distance_vector_neighbor_message = json.loads(m)
        sequence_number = distance_vector_neighbor_message["self_sequence_number"]
        distance_vector_neighbor_message.pop('self_sequence_number')
        return distance_vector_neighbor_message,sequence_number

    def get_next_hop(self, destination):
        if destination in self.distance_vectors_self:
            return self.distance_vectors_self[destination].path[1]
        return -1