#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 2019
@author: lucasgodfrey

Module containing a class for creating graph objects that support read and
write transactions to a neo4j instance.

Write transactions:
- load demo graph vertices and edges from csv data (features and edge lists)
- create spatial index on feature vertices
- create action region subgraphs using spatial.closest to demonstrate how the
underlying architecture could be constructed in practice.

Read transactions:
- return a subgraph for a given journey context based on a list of traversed
    k-level routing nodes
- return sets of features based on spatial queries for phase regions derived
    from the k-level routing nodes
"""

# link to the neo4j python driver and import the GraphDatabase object
from neo4j import GraphDatabase

import decimal
import re
'''
decimal module import, regex import, get_floats and get_coords for dealing with
floats in wkt strings
'''
def get_floats(geometry_as_string):
    for item in re.split(' |\(|\)', geometry_as_string):
        try:
            yield decimal.Decimal(item)
        except decimal.InvalidOperation:
            pass

def get_coords(wkt_string):
    coords = []
    v_list = list(get_floats(wkt_string))
    v_lon = float(v_list[0])
    v_lat = float(v_list[1])
    coords.append(v_lon)
    coords.append(v_lat)

    return coords


class Graph(object):
    '''
    Class for creating a graph object that supports read and write transactions
    over a bolt connection to an instance of Neo4j community server
    '''

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()


    def add_vertex_constraints(self):
        '''
        Transaction to run the 'add_constraints' function
        '''
        with self._driver.session() as session:
            session.write_transaction(self.add_constraints)

    @staticmethod
    def add_constraints(tx):
        '''
        Ensure features loaded as graph vertices are unique based on their
        id property
        '''
        tx.run("CREATE CONSTRAINT ON (v:NK) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:SK) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:AR) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:SK_PLUS_ONE) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:SK_MINUS_ONE) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:OSM_POINTS) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:VML_POINTS) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:OSM_LOW_DETAIL) ASSERT v.id IS UNIQUE;")
        tx.run("CREATE CONSTRAINT ON (v:BOROUGH_TEXT) ASSERT v.id IS UNIQUE;")

        return None


    def load_data_from_csv(self):
        '''
        Load vertices and edges into graph
        '''
        with self._driver.session() as session:
            session.write_transaction(self.csv_load)

    @staticmethod
    def csv_load(tx):
        '''
        Load example vertices and edges for the routing network representation
        using csv edge lists
        '''
        # NK_SK_BOUNDS
        tx.run("LOAD CSV WITH HEADERS FROM 'file:///nk_sk_edges.csv' AS line MERGE (nk:NK {id: TOINT(line.`parent`)}) MERGE (sk:SK {id: TOINT(line.`child`)}) MERGE (nk)-[:NK_SK_BOUNDS {edge_id: TOINT(line.`edge_id`)}]->(sk)")
        # NK_AR_ACTIVATES
        tx.run("LOAD CSV WITH HEADERS FROM 'file:///nk_ar_edges.csv' AS line MERGE (nk:NK {id: TOINT(line.`parent`)}) MERGE (ar:AR {id: TOINT(line.`child`)}) MERGE (nk)-[:NK_AR_ACTIVATES {edge_id: TOINT(line.`edge_id`)}]->(ar)")
        # NK_SK_PLUS_ONE_BOUNDS
        tx.run("LOAD CSV WITH HEADERS FROM 'file:///nk_sk_plus_one_edges.csv' AS line MERGE (nk:NK {id: TOINT(line.`parent`)}) MERGE (sk_plus:SK_PLUS_ONE {id: TOINT(line.`child`)}) MERGE (nk)-[:NK_SK_PLUS_ONE_BOUNDS {edge_id: TOINT(line.`edge_id`)}]->(sk_plus)")
        # SK_MINUS_ONE_SK_IN_REGION
        tx.run("LOAD CSV WITH HEADERS FROM 'file:///sk_sk_minus_one_edges.csv' AS line MERGE (sk:SK {id: TOINT(line.`parent`)}) MERGE (sk_minus:SK_MINUS_ONE {id: TOINT(line.`child`)}) MERGE (sk)-[:SK_SK_MINUS_ONE_IN_REGION {edge_id: TOINT(line.`edge_id`)}]->(sk_minus)")
        '''
        Load disconnected feature vertices for spatial query demo and action region subgraph construction example
        '''
        # OSM_POINTS
        tx.run("LOAD CSV FROM 'file:///osm_points_example_data_v29.csv' AS line CREATE (:OSM_POINTS { wkt: line[0], id: line[1]})")
        # VML_POINTS (Building text)
        tx.run("LOAD CSV FROM 'file:///vml_building_text.csv' AS line CREATE (:VML_POINTS { wkt: line[0], id: line[1]})")
        # OSM_POINTS (low detail)
        tx.run("LOAD CSV FROM 'file:///osm_name_filtered_v3.csv' AS line CREATE (:OSM_LOW_DETAIL { wkt: line[0], id: line[1]})")
        # BOROUGH_TEXT (example low detail features for demonstration)
        tx.run("LOAD CSV FROM 'file:///borough_text.csv' AS line CREATE (:BOROUGH_TEXT { wkt: line[0], id: line[1]})")

        return None


    def set_geometry(self, geometry_reference, i):
        '''
        Workaround to ensure routing nodes have a geometry property in the demo
        '''
        with self._driver.session() as session:
            session.write_transaction(self.set_wkt_property, geometry_reference, i)

    @staticmethod
    def set_wkt_property(tx, geometry_reference, i):
        '''
        Set wkt geometry based on reference data
        '''
        id_raw = geometry_reference[i][1]
        id_string = id_raw.lstrip()
        id = int(id_string)
        wkt_string = geometry_reference[i][0]
        tx.run("MATCH (n) WHERE n.id=$id SET n.wkt=$wkt_string RETURN n.id, n.wkt", id=id, wkt_string=wkt_string)

        return None


    def get_wkt(self, id):
        '''
        Get the vertex geometry property
        '''
        with self._driver.session() as session:
            res = session.read_transaction(self.get_vertex_wkt_string, id)
            return res

    @staticmethod
    def get_vertex_wkt_string(tx, id):
        '''
        Return wkt string
        '''
        # print(id)
        result = tx.run("MATCH (n) WHERE n.id=$id RETURN n", id=id)
        g = result.graph()
        n = g.nodes

        for r in n:
            global wkt_geometry_string
            wkt_geometry_string = r.get('wkt')

        return wkt_geometry_string



    def add_nodes_to_spatial_layer(self):
        '''
        Graph transaction to run the 'add_nodes_example' function
        '''
        with self._driver.session() as session:
            session.write_transaction(self.add_nodes_example)

    @staticmethod
    def add_nodes_example(tx):
        '''
        Add demo graph vertices with WKT geoemtries to a spatial index
        '''
        tx.run("CALL spatial.addWKTLayer('layer', 'wkt')")
        tx.run("CALL spatial.layers()")

        tx.run("MATCH (n:OSM_POINTS) WHERE NOT (n)-[:RTREE_REFERENCE]-() WITH COLLECT(n) AS nodes CALL spatial.addNodes('layer', nodes) YIELD count RETURN count")
        tx.run("MATCH (n:OSM_LOW_DETAIL) WHERE NOT (n)-[:RTREE_REFERENCE]-() WITH COLLECT(n) AS nodes CALL spatial.addNodes('layer', nodes) YIELD count RETURN count")
        tx.run("MATCH (n:VML_POINTS) WHERE NOT (n)-[:RTREE_REFERENCE]-() WITH COLLECT(n) AS nodes CALL spatial.addNodes('layer', nodes) YIELD count RETURN count")
        tx.run("MATCH (n:NK) WHERE NOT (n)-[:RTREE_REFERENCE]-() WITH COLLECT(n) AS nodes CALL spatial.addNodes('layer', nodes) YIELD count RETURN count")
        tx.run("MATCH (n:BOROUGH_TEXT) WHERE NOT (n)-[:RTREE_REFERENCE]-() WITH COLLECT(n) AS nodes CALL spatial.addNodes('layer', nodes) YIELD count RETURN count")

        return None


    '''
    Create action region subgraphs
    '''

    '''
    This method returns all action region vertex IDs and the location of the
    underlying NK routing node.
    '''
    def get_action_regions_locations(self):
        with self._driver.session() as session:
            ar_result = session.read_transaction(self.get_ar_reference)
            return ar_result

    @staticmethod
    def get_ar_reference(tx):
        '''
        This function is a workaround because graph vertex geometry properties
        need to be wkt strings but the spatial.closest method from the neo
        spatial plugin requires the coordinates as floats.
        '''
        action_region_vertex_result = tx.run("MATCH edge=(i)-[:NK_AR_ACTIVATES]->(j) RETURN COLLECT ({nk: i, ar: j})")
        records=action_region_vertex_result.records()
        r_list = list(records)
        results = r_list[0][0]
        action_regions_and_locations = []

        for i in range(len(results)):
            query_result = []
            ar_id = results[i]['ar']['id']
            temp_geometry = results[i]['nk']['wkt']
            p = list(get_floats(temp_geometry))
            lon_dec = p[0]
            lat_dec = p[1]
            lon_fl = float(lon_dec)
            lat_fl = float(lat_dec)
            query_result.append(ar_id)
            query_result.append(lon_fl)
            query_result.append(lat_fl)
            action_regions_and_locations.append(query_result)

        return action_regions_and_locations


    def action_region_spatial_search(self, ar_id, lon, lat):
        ''' Search for features in action regions '''
        with self._driver.session() as session:
            target_features = session.read_transaction(self.feature_search, ar_id, lon, lat)
            return target_features

    @staticmethod
    def feature_search(tx, ar_id, lon, lat):
        ''' 0.0002 as distance argument - return features excluding type NK '''
        feature_search_result = tx.run("CALL spatial.closest('layer', {lat: $lat, lon: $lon}, 0.0002) YIELD node WHERE NOT (node:NK) RETURN COLLECT({ar_id: $ar_id, feature: node})", lat=lat, lon=lon, ar_id=ar_id)
        records = feature_search_result.records()
        r_list = list(records)
        results = r_list[0][0]

        action_regions_and_features = {}
        action_regions_and_features['ar_feature_edge_list'] = []

        for i in range(len(results)):
            ar_reference_id = results[i]['ar_id']
            feature_id = results[i]['feature']['id']

            action_regions_and_features['ar_feature_edge_list'].append({
                    'ar_source_id': ar_reference_id,
                    'feature_target_id': feature_id
                    })

        return action_regions_and_features


    def create_action_region_subgraphs(self, source_id, target_id):
        '''
        Construct subgraphs of features based on the result of the feature
        search
        '''
        with self._driver.session() as session:
            session.write_transaction(self.construct_action_regions, source_id, target_id)

    @staticmethod
    def construct_action_regions(tx, source_id, target_id):
        ''' Create new edges in the graph '''
        tx.run("MATCH (ar:AR { id: $source_id }), (feature { id: $target_id }) MERGE (ar)-[edge:CONTAINS_FEATURE]->(feature) RETURN ar, type(edge), feature", source_id=source_id, target_id=target_id)

        return None


    def phase_zero_spatial_query(self, p_zero_region):
        ''' Return features for the journey extent '''
        with self._driver.session() as session:
            selection = session.read_transaction(self.p_zero_spatial_query_example, p_zero_region)
            return selection

    @staticmethod
    def p_zero_spatial_query_example(tx, p_zero_region):
        '''
        Return features in phase 0 determined by the region's bounding box
        from coordinaes in a matrix of the form: [[x_1, y_1],[x_2, y_2]]

        BOROUGH_TEXT used as example low detail data
        '''
        lower_left_lon = p_zero_region[0][0]
        lower_left_lat = p_zero_region[0][1]
        top_right_lon = p_zero_region[1][0]
        top_right_lat = p_zero_region[1][1]

        result = tx.run("CALL spatial.bbox('layer',{lon: $ll_lon, lat: $ll_lat }, {lon: $tr_lon, lat: $tr_lat}) YIELD node WHERE (node:BOROUGH_TEXT) RETURN COLLECT(node)", ll_lon=lower_left_lon, ll_lat=lower_left_lat, tr_lon=top_right_lon, tr_lat=top_right_lat)

        g = result.graph()
        n = g.nodes
        spatial_selection = []

        for graph_vertex in n:
            selected = {}
            selected_id = graph_vertex.get('id')
            selected_geometry = graph_vertex.get('wkt')
            labels = graph_vertex.labels
            vertex_type = list(labels)[0]
            geometry =  get_coords(selected_geometry)
            spatial_selection.append({
                'type': vertex_type,
                'id': selected_id,
                'geometry': geometry
            })

        return spatial_selection


    def phase_region_spatial_query(self, region):
        ''' Core phase region spatial query '''
        with self._driver.session() as session:
            selection = session.read_transaction(self.spatial_query_example, region)
            return selection

    @staticmethod
    def spatial_query_example(tx, region):
        '''
        Return features in a phase region determined by the region's
        bounding box from coordinaes in a matrix of the form:
        [[x_1, y_1],[x_2, y_2]]
        '''
        lower_left_lon = region[0][0]
        lower_left_lat = region[0][1]
        top_right_lon = region[1][0]
        top_right_lat = region[1][1]

        result = tx.run("CALL spatial.bbox('layer',{lon: $ll_lon, lat: $ll_lat }, {lon: $tr_lon, lat: $tr_lat}) YIELD node WHERE (node:VML_POINTS) RETURN COLLECT(node)", ll_lon=lower_left_lon, ll_lat=lower_left_lat, tr_lon=top_right_lon, tr_lat=top_right_lat)

        g = result.graph()
        n = g.nodes
        spatial_selection = []

        for graph_vertex in n:
            selected = {}
            selected_id = graph_vertex.get('id')
            selected_geometry = graph_vertex.get('wkt')
            labels = graph_vertex.labels
            vertex_type = list(labels)[0]
            geometry =  get_coords(selected_geometry)
            spatial_selection.append({
                'type': vertex_type,
                'id': selected_id,
                'geometry': geometry
            })

        return spatial_selection


    def return_subgraph_from_routing_result(self, route):
        '''
        Return subgraph by matching on IDs from an array of nodes. Format of
        subgraph is a dictionary containing vertices and edges, ready to be
        consumed by functions that construct Variable and Arc objects in
        preparation for message propagation.
        '''
        with self._driver.session() as session:
            a = session.read_transaction(self.return_subgraph, route)
            return a

    @staticmethod
    def return_subgraph(tx, route):
        '''
        Use the routing result to match on a set of graph vertices, traverse
        the graph by matching on path patterns based on topological distance,
        and return the subgraph in a dictionary of vertices and edges.

        This data forms the basis of the Variables and Arcs in the CN
        construction functions.
        '''

        subgraph_data = {}

        subgraph_data['vertices'] = {}

        subgraph_data['vertices']['NK'] = []
        subgraph_data['vertices']['SK'] = []
        subgraph_data['vertices']['AR'] = []
        subgraph_data['vertices']['SK_PLUS_ONE'] = []
        subgraph_data['vertices']['SK_MINUS_ONE'] = []
        subgraph_data['vertices']['FEATURES'] = []

        subgraph_data['edges'] = {}

        subgraph_data['edges']['NK_SK_BOUNDS'] = []
        subgraph_data['edges']['NK_AR_ACTIVATES'] = []
        subgraph_data['edges']['CONTAINS_FEATURE'] = []
        subgraph_data['edges']['SK_SK_MINUS_ONE_IN_REGION'] = []
        subgraph_data['edges']['NK_SK_PLUS_ONE_BOUNDS'] = []

        '''
        Graph pattern one, based on topological distance of '1' from nodes in
        the routing result
        '''
        pattern_one_nk_vertices = tx.run("WITH $route AS arr MATCH pattern_one=(i)-[]->(j) WHERE i.id IN arr RETURN COLLECT(DISTINCT(i))", route=route)
        pattern_one_child_vertices = tx.run("WITH $route AS arr MATCH pattern_one=(i)-[]->(j) WHERE i.id IN arr RETURN COLLECT(DISTINCT(j))", route=route)
        pattern_one_paths = tx.run("WITH $route AS arr MATCH pattern_one=(i)-[]->(j) WHERE i.id IN arr RETURN relationships(pattern_one), i, j", route=route)
        '''
        Graph pattern two, based on topological distance of '2' from nodes in
        the routing result
        '''
        pattern_two_children_of_children_vertices = tx.run("WITH $route AS arr MATCH pattern_two=(i)-[]->(j)-[]->(k) WHERE i.id IN arr RETURN COLLECT(DISTINCT(k))", route=route)
        pattern_two_paths = tx.run("WITH $route AS arr MATCH pattern_two=(i)-[]->(j)-[]->(k) WHERE i.id IN arr RETURN relationships(pattern_two), i, j, k", route=route)


        ''' consume vertices and add to the subgraph '''

        #get data from results using types built into the neo python driver
        res_one = pattern_one_nk_vertices.graph()
        res_two = pattern_one_child_vertices.graph()
        res_three = pattern_two_children_of_children_vertices.graph()

        res_one_vertices = res_one.nodes
        res_two_vertices = res_two.nodes
        res_three_vertices = res_three.nodes

        for record in res_one_vertices:
            v_id = record['id']
            subgraph_data['vertices']['NK'].append({'id': v_id})

        for record in res_two_vertices:
            v_id = record['id']
            v_labels = record.labels
            l = list(v_labels)[0]

            if l == 'SK':
                subgraph_data['vertices']['SK'].append({'id': v_id})


            if l == 'AR':
                subgraph_data['vertices']['AR'].append({'id': v_id})


            if l == 'SK_PLUS_ONE':
                subgraph_data['vertices']['SK_PLUS_ONE'].append({'id': v_id})


        for record in res_three_vertices:
            v_id = record['id']
            v_labels = record.labels
            l = list(v_labels)[0]

            if l == 'SK_MINUS_ONE':
                subgraph_data['vertices']['SK_MINUS_ONE'].append({'id': v_id})

            if l == 'OSM_POINTS':
                # get the geometry property for features in the demo
                type = "OSM_POINTS"
                v_geometry = get_coords(record['wkt'])
                subgraph_data['vertices']['FEATURES'].append({'id': v_id, 'geometry': v_geometry, 'type': type})

            if l == 'OSM_LOW DETAIL':
                # get the geometry property for features in the demo
                type = "OSM_LOW_DETAIL"
                v_geometry = get_coords(record['wkt'])
                subgraph_data['vertices']['FEATURES'].append({'id': v_id, 'geometry': v_geometry, 'type': type})

            if l == 'VML_POINTS':
                # get the geometry property for features in the demo
                type = "VML_POINTS"
                v_geometry = get_coords(record['wkt'])
                subgraph_data['vertices']['FEATURES'].append({'id': v_id, 'geometry': v_geometry, 'type': type})


        ''' consume edges and add to the subgraph'''

        res_four = pattern_one_paths.graph()
        res_four_edges = res_four.relationships

        for r in res_four_edges:
            rel_type = r.type

            if rel_type == 'NK_SK_BOUNDS':
                # note that 'start_node' and 'end_node' are from the neo
                # python driver
                start_id = r.start_node['id']
                end_id = r.end_node['id']
                edge_id = r.get('edge_id')
                subgraph_data['edges']['NK_SK_BOUNDS'].append({
                        'edge_id': edge_id,
                        'parent': start_id,
                        'child': end_id
                        })


            if rel_type == 'NK_AR_ACTIVATES':
                start_id = r.start_node['id']
                end_id = r.end_node['id']
                edge_id = r.get('edge_id')
                subgraph_data['edges']['NK_AR_ACTIVATES'].append({
                        'edge_id': edge_id,
                        'parent': start_id,
                        'child': end_id
                        })

            if rel_type == 'NK_SK_PLUS_ONE_BOUNDS':
                start_id = r.start_node['id']
                end_id = r.end_node['id']
                edge_id = r.get('edge_id')
                subgraph_data['edges']['NK_SK_PLUS_ONE_BOUNDS'].append({
                        'edge_id': edge_id,
                        'parent': start_id,
                        'child': end_id
                        })


        res_five = pattern_two_paths.graph()
        res_five_edges = res_five.relationships

        for r in res_five_edges:
            rel_type = r.type

            if rel_type == 'SK_SK_MINUS_ONE_IN_REGION':
                start_id = r.start_node['id']
                end_id = r.end_node['id']
                edge_id = r.get('edge_id')
                subgraph_data['edges']['SK_SK_MINUS_ONE_IN_REGION'].append({
                        'edge_id': edge_id,
                        'parent': start_id,
                        'child': end_id
                        })

            if rel_type == 'CONTAINS_FEATURE':
                start_id = r.start_node['id']
                end_id = r.end_node['id']
                edge_id = r.id
                subgraph_data['edges']['CONTAINS_FEATURE'].append({
                        'edge_id': edge_id,
                        'parent': start_id,
                        'child': end_id
                        })


        # return the subgraph data expressed as a dictionary
        return subgraph_data

# END
