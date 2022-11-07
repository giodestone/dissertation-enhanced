import pickle
from operator import contains
from os import mkdir
import os
from DissertationEnhancedLib.TrainingGraph import TrainingGraph
import networkx as nx
import hashlib


class PathGenerator:

    def __init__(self, training_graph:TrainingGraph, depth_limit:int=40, regenerate_if_exists:bool=False, saved_generated_paths_dir_name:str="Saved Generated Graphs") -> None:
        self.training_graph = training_graph
        self.depth_limit = depth_limit
        self.paths = list()
        self.is_dev_mode = True

        self.__saved_generated_paths_dir_name = saved_generated_paths_dir_name
        self.__regenerate_if_exists = regenerate_if_exists


    def is_saved_on_disk(self) -> bool:
        return os.path.exists(self.__get_file_path_to_generated_path())


    def generate_training_data(self) -> None:

        if self.is_saved_on_disk() and not self.__regenerate_if_exists:
            self.__load_from_disk()
            return

        for node in self.training_graph.graph.nodes:
            self.__add_all_simple_paths_from_node(node)

        self.__save_to_disk()


    def __add_all_simple_paths_from_node(self, node) -> None:
        all_reachable_nodes = nx.single_source_shortest_path(self.training_graph.graph, node, cutoff=self.depth_limit)
        
        # TODO: If the training accuracy is broken, maybe do random.shuffle(all_reachable_nodes) like in previous implementation.

        for index in all_reachable_nodes:
            # do not add paths of len 1.
            path = all_reachable_nodes[index]

            if (len(path) == 1):
                continue;

            self.paths.append(path)

    def __get_file_path_to_generated_path(self) -> str:
        hash_object = hashlib.sha256(self.training_graph.get_query().encode("utf-8"))
        hex_dig = hash_object.hexdigest()
        return self.__saved_generated_paths_dir_name + "/" + hex_dig + ".pickle"


    def __load_from_disk(self) -> None:
        print("Loading Generated Paths from disk...")
        
        with open(self.__get_file_path_to_generated_path()) as f:
            self.paths = pickle.load(f)

        print("Loaded!")
        pass


    def __save_to_disk(self) -> None:
        print("Saving Generated Paths to disk...")

        if not os.path.exists(self.__saved_generated_paths_dir_name + "/"):
            mkdir(self.__saved_generated_paths_dir_name)

        with open(self.__get_file_path_to_generated_path(), 'wb') as f:
            pickle.dump(self.paths, f)

        print("Saved!")
        pass