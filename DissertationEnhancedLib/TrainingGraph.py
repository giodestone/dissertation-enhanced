from ast import Tuple
from math import asin, atan2, ceil, cos, degrees, radians, sin, sqrt
from sqlite3 import ProgrammingError
from turtle import position
from xml.dom.minidom import Element
import progressbar;
import networkx as nx
import OSMPythonTools as osm
import OSMPythonTools.api as osm_api
import OSMPythonTools.element as osm_elements
from OSMPythonTools.overpass import Overpass
import DissertationEnhancedLib.CustomExceptions
from DissertationEnhancedLib.Distance import Distance
from DissertationEnhancedLib.GeographicCoords import GeographicCoords
import matplotlib.pyplot as plt
import os.path
from os import mkdir
import hashlib

class TrainingGraph:
    def __init__(self, query:str=None, regenerate_if_exists:bool=False, saved_graphs_dir_name:str="Saved Training Graphs"):
        if query is None or len(query) is 0:
            raise DissertationEnhancedLib.CustomExceptions.QueryInvalidException()
        if saved_graphs_dir_name is None or len(saved_graphs_dir_name) is 0:
            raise DissertationEnhancedLib.CustomExceptions.InvalidStringArgumentException()

        self.graph = nx.Graph()
        self.__query = query
        self.max_dist_between_nodes_meters = 100
        self.__saved_graph_dir_name = saved_graphs_dir_name
        
        if (self.is_saved_on_disk() and not regenerate_if_exists):
            self.__load_from_disk()
        else:
            self.__generate_training_graph()
            self.__save_to_disk()
        pass


    def is_saved_on_disk(self) -> bool:
        return os.path.exists(self.__get_file_path_to_graph())


    def get_query(self) -> str:
        """Get the query which the TrainingGraph was generated with."""

        return self.__query


    def show_graph(self, node_size=3, edge_width=1, show_labels=True, font_size=7, should_display=True, save_to_disk=False, file_name=None):
        """Show the graph on screen in a window.

        Args:
            graph (nx.Graph): Graph to display.
            node_size (int, optional): Size of node circles. Defaults to 3.
            edge_width (float, optional): Width of the line that represents the edges. Defaults to 1.
            show_labels (bool, optional): Whether to the node_id's. Defaults to True.
            font_size (int, optional): Size of the label font. `show_labels` must be `True` for them to display. Defaults to 7.
            should_display (bool, optional): Whether a window should be displayed. Defaults to True.
            save_to_disk (bool, optional): Whether to save the graph to disk. Defaults to False.
            file_name (str, optional): Name of the file. Must be defined if `save_to_disk` is `True`. Defaults to None.
        """
        
        # Build pos dict.
        pos_dict = dict()
        for nodeID in self.graph.nodes:
            if len(self.graph.nodes[nodeID]) == 0:
                pass
            else:
                pos = self.graph.nodes[nodeID]['position'] # If the position is empty or invalid, nx.draw will give error!"
                pos_dict[nodeID] = pos

        nx.draw(self.graph, pos=pos_dict, with_labels=show_labels, node_size=node_size, width=edge_width, font_size=font_size)
        
        if save_to_disk:
            if file_name is None:
                raise Exception("File name is not set.")
            plt.savefig(file_name, dpi=500)

        if should_display:
            plt.show()

        plt.clf()


    def __get_file_path_to_graph(self) -> str:
        hash_object = hashlib.sha256(self.__query.encode("utf-8"))
        hex_dig = hash_object.hexdigest()
        return self.__saved_graph_dir_name + "/" + hex_dig + ".pickle"


    def __load_from_disk(self):
        print("Loading TrainingGraph from disk...")
        self.graph = nx.read_gpickle(self.__get_file_path_to_graph())
        print("Done!")
        pass


    def __save_to_disk(self):
        print("Saving TrainingGraph to disk...")

        if not os.path.exists(self.__saved_graph_dir_name + "/"):
            mkdir(self.__saved_graph_dir_name)

        nx.write_gpickle(self.graph, self.__get_file_path_to_graph())
        print("Done!")
        pass


    def __generate_training_graph(self):
        osm_overpass = Overpass()

        ways_from_query = osm_overpass.query(self.__query)

        if (ways_from_query.ways() is None or ways_from_query.countWays() == 0):
            raise DissertationEnhancedLib.CustomExceptions.NoWaysFoundException("There were no ways found using this query.");

        print("SUCCESS: Got {0} ways. If this step is taking a while then API is being queried. Converting them to a graph format...".format(ways_from_query.countWays()))

        bar = progressbar.ProgressBar(widgets=['Processing Ways... ', progressbar.Timer(), '  ', progressbar.AdaptiveETA(), ' ', progressbar.Bar(), ' ', progressbar.Percentage()], max_value=ways_from_query.countWays()) 
        bar.start()
        ways_processed = 0
        for way in ways_from_query.ways():
            bar.update(ways_processed)
            self.__add_way_to_graph(way, bar)
            ways_processed += 1

        pass


    def __add_way_to_graph(self, highway:osm_elements.Element, bar:progressbar.ProgressBar):
        for i in range(1, len(highway.nodes())):
            way_node_a = highway.nodes()[i - 1]
            way_node_b = highway.nodes()[i]
            distance = self.__calculate_distance_between_coords(GeographicCoords(way_node_a.lon(), way_node_a.lat()), GeographicCoords(way_node_b.lon(), way_node_b.lat()))


            if (self.__is_node_dist_too_big(distance)):
                self.__split_nodes_into_multiples(way_node_a, way_node_b, distance, bar)
                pass
            else:
                self.graph.add_node(str(way_node_a.id()), position=(way_node_a.lon(), way_node_b.lat()))
                self.graph.add_node(str(way_node_b.id()), position=(way_node_b.lon(), way_node_b.lat()))
                self.graph.add_edge(str(way_node_a.id()), str(way_node_b.id()), dist=distance)
                pass
        pass


    def __split_nodes_into_multiples(self, node_a:osm_elements.Element, node_b:osm_elements.Element, dist:Distance, bar:progressbar.ProgressBar):
        self.graph.add_node(str(node_a.id()), position=(node_a.lon(), node_a.lat()))
        num_to_split_into = ceil(dist.xy / self.max_dist_between_nodes_meters)
        advancement_distance = dist.xy / num_to_split_into

        bearing = self.__get_bearing(node_a, node_b)

        prev_node_pos = GeographicCoords(node_a.lon(), node_a.lat());
        prev_node_name = str(node_a.id())

        for i in range(num_to_split_into - 1): # -1 otherwise there would be two end nodes - a 'split' node and node_b!
            new_node_pos = self.__get_destination_point(prev_node_pos, bearing, advancement_distance / 1000.0)
            new_node_name = str(node_a.id()) + '-split-' + str(i)
            
            # Due to how the highway is iterated, part of the roadway would've been split before, this can happen any number of times (especially for big roads).
            while(self.graph.has_node(new_node_name)):
                new_node_name += "-dupe"

            dist_between_prev_new_nodes = self.__calculate_distance_between_coords(prev_node_pos, new_node_pos)
            self.graph.add_node(new_node_name, position=(new_node_pos.lon, new_node_pos.lat))
            self.graph.add_edge(prev_node_name, new_node_name, dist=dist_between_prev_new_nodes) # ID's *must* be str

            prev_node_name = new_node_name
            prev_node_pos = new_node_pos;
            bar.update()

        self.graph.add_node(str(node_b.id()), position=(node_b.lon(), node_b.lat()))
        self.graph.add_edge(prev_node_name, str(node_b.id()), dist=self.__calculate_distance_between_coords(prev_node_pos, GeographicCoords.from_element(node_b)))


    def __calculate_distance_between_coords(self, node_a:GeographicCoords, node_b:GeographicCoords) -> Distance:
        dist_x_from_coords = GeographicCoords(node_a.lon, node_a.lat)
        dist_x_to_coords = GeographicCoords(node_b.lon, node_a.lat)
        dist_x = self.__calculate_absolute_distance_between_coords(dist_x_from_coords, dist_x_to_coords)

        dist_y_from_coords = GeographicCoords(node_a.lon, node_b.lat)
        dist_y_to_coords = GeographicCoords(node_a.lon, node_a.lat)
        dist_y = self.__calculate_absolute_distance_between_coords(dist_y_from_coords, dist_y_to_coords)

        return Distance(dist_x, dist_y, self.__calculate_absolute_distance_between_coords(node_a, node_b))


    def __is_node_dist_too_big(self, distance:Distance) -> bool:
        return distance.xy > self.max_dist_between_nodes_meters


    def __calculate_absolute_distance_between_coords(self, fromPos:GeographicCoords, toPos:GeographicCoords) -> float:
        """Calculates the distance between `from` and `to` and returns the distance in meters.
        Adapted from https://stackoverflow.com/a/19412565

        Returns:
            float: Distance between `from` and `to` in meters.
        """
        R = 6373.0 # earth radius

        lat1 = radians(fromPos.lat)
        lon1 = radians(fromPos.lon)
        lat2 = radians(toPos.lat)
        lon2 = radians(toPos.lon)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance * 1000


    def __get_bearing(self, frm:osm_elements.Element, to:osm_elements.Element) -> float:
        #φ = lat
        #λ = lon
        #Δλ = diff in lon

        lon1 = radians(frm.lon())
        lon2 = radians(to.lon())

        lat1 = radians(frm.lat())
        lat2 = radians(to.lat())

        y = sin(lon2 - lon1) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos (lat2) * cos (lon2 - lon1)
        θ = atan2(y,  x)
        # bearing = (θ * 180.0 / pi + 360.0) % 360
        bearing = degrees(θ)
        
        return bearing


    def __get_destination_point(self, start_coords:GeographicCoords, bearing:float, eucledean_distance:float) -> GeographicCoords:
        """Get the resulting lat, lon coordinates, as advanced by euclidean_distance from start."""
        
        # const φ2 = Math.asin( Math.sin(φ1)*Math.cos(d/R) +
        #                       Math.cos(φ1)*Math.sin(d/R)*Math.cos(brng) );
        # const λ2 = λ1 + Math.atan2(Math.sin(brng)*Math.sin(d/R)*Math.cos(φ1),
        #                            Math.cos(d/R)-Math.sin(φ1)*Math.sin(φ2));

        R = 6373.0 # earth radius

        bearing = radians(bearing) # convert to radians

        lon = radians(start_coords.lon)
        lat = radians(start_coords.lat)

        lonResult = 0.0
        latResult = 0.0

        latResult = asin(sin(lat) * cos(eucledean_distance / R) + cos(lat) * sin(eucledean_distance/R) * cos(bearing))
        lonResult = lon + atan2(sin(bearing) * sin(eucledean_distance/R) * cos(lat), cos(eucledean_distance/R) - sin(lat) * sin(latResult))

        return GeographicCoords(degrees(lonResult), degrees(latResult))

