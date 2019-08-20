#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 2019
@author: lucasgodfrey

Driver code for the SCT_Graph_Application_Research demo - provided for users
without access to ipython (Jupyter) notebooks.
"""


import csv
import json

from geo_graph import Graph, get_coords
from journey_context import get_context
from phase_region import get_vectors_from_wkt, sqr, euclidean_distance, midpoint, get_region_bbox
from causal_net import Variable, Arc, construct_variables, construct_arcs, feature_view_template
from propagation import variable_activation, map_finding_to_arcs, propagate, merge_index

#change to the username and password you have set for your db instance
graph_object = Graph("bolt://localhost:7687", "username", "password")


'''
Code to setup the graph
'''
#
# # ONLY TO BE RUN ONCE
# graph_object.add_vertex_constraints()
#
# # ONLY TO BE RUN ONCE
# graph_object.load_data_from_csv()
#
# # ONLY TO BE RUN ONCE
# geometry_reference = []
#
# with open('/Applications/neo4j-community-3.5.6/import/wkt_ref_test_6.csv','r') as f:
#     reader = csv.reader(f, delimiter=',')
#     reader = list(reader)
#
#     for row in range(len(reader)):
#         id = reader[row][0]
#         wkt_string = reader[row][1]
#         wkt_feature = [id, wkt_string]
#         geometry_reference.append(wkt_feature)
#         graph_object.set_geometry(geometry_reference, row)
#
# # ONLY TO BE RUN ONCE
# graph_object.add_nodes_to_spatial_layer()
#
# # ONLY TO BE RUN ONCE
#
# #create action region subgraphs
# action_region_reference = graph_object.get_action_regions_locations()
#
# for rec in action_region_reference:
#     action_region_target_features = graph_object.action_region_spatial_search(rec[0], rec[1], rec[2])
#     #write the new edges to the database
#     for edge_object in action_region_target_features['ar_feature_edge_list']:
#         #pass in source ID and target ID to the write transaction
#         graph_object.create_action_region_subgraphs(edge_object['ar_source_id'], edge_object['feature_target_id'])



'''
Demonstration
'''
# consume the routing result
with open('/Users/lucasgodfrey/Documents/GitHub/Automated-Map-Content-Selection-/Database/Master_Data/ROUTING_RESULT/routing_result_v3.min.json', 'r+') as f:
    for line in f:
        routing_result_data=json.loads(line)
# print(routing_result_data)

# create an array to store the routing result
routing_result_array = []

# populate the routing result array
for nested_data in routing_result_data['result']['nk_routing_nodes']:
    id = nested_data['id']
    routing_result_array.append(id)

# query the graph, matching on ID to get the WKT strings for each node in the result
for traversed_node in routing_result_data['result']['nk_routing_nodes']:
#   get the id and pass as argument to a query on the graph
    id = traversed_node['id']
#   match on the ID and return the wkt property
    wkt_geometry = graph_object.get_wkt(id)
#   change the geometry property to the wkt string
    traversed_node['geometry'] = wkt_geometry

# print result:
# print(routing_result_data)

# pretty print
# print(json.dumps(routing_result_data, indent=4, sort_keys=True))

subgraph_example = graph_object.return_subgraph_from_routing_result(routing_result_array)
data = subgraph_example

# print result:
# print(data)

#pretty print:
# print(json.dumps(data, indent=4, sort_keys=True))

# get phase region coordinates ready for spatial queries

phase_region_bounding_routing_nodes = []
# add the network node connected to the journey origin
phase_region_bounding_routing_nodes.append(routing_result_data['result']['nk_routing_nodes'][0])

for r in routing_result_data['result']['nk_routing_nodes']:
    t = r['type']
    if (t=='transfer'):
        phase_region_bounding_routing_nodes.append(r)

# add the network node connected to the journey destination
y = len(routing_result_data['result']['nk_routing_nodes'])
y = y - 1
phase_region_bounding_routing_nodes.append(routing_result_data['result']['nk_routing_nodes'][y])

phase_regions = []

for n in range(len(phase_region_bounding_routing_nodes)-1):
    phase_regions.append([phase_region_bounding_routing_nodes[n], phase_region_bounding_routing_nodes[n+1]])

# print result:
# print(phase_regions)

# pretty print
# print(json.dumps(phase_regions, indent=4, sort_keys=True))

# uncomment lines in this cell to output to json for visualisation
# selection_data = {}
# selection_data['regions'] = {}

num_of_regions = len(phase_regions)

#return features for the journey extent (phase 0/ tile 0) using 'BOROUGH_TEXT' as the example
#...low detail feature type
reference_num = num_of_regions - 1
# 'p_0' -> phase 0, i.e. the current journey extent
p_zero_vec_one = get_coords(phase_regions[0][0]['geometry'])
p_zero_vec_two = get_coords(phase_regions[reference_num][1]['geometry'])
p_zero_g_matrix = [[p_zero_vec_one[0], p_zero_vec_one[1]], [p_zero_vec_two[0], p_zero_vec_two[1]]]

p_zero_vecs = get_vectors_from_wkt(p_zero_g_matrix)
p_zero_e_dist = euclidean_distance(p_zero_vecs[0][0], p_zero_vecs[0][1])
p_zero_mid = midpoint(p_zero_vecs[0][0], p_zero_vecs[0][1])
#'vw' -> vectors 'v' and 'w'
p_zero_vw = get_region_bbox(p_zero_e_dist, p_zero_mid)
p_zero_selection = graph_object.phase_zero_spatial_query(p_zero_vw)
count_of_p_zero_features = len(p_zero_selection)
print("phase region 0:",count_of_p_zero_features,"features")

# selection_data['regions']['region_p_zero'] = []
# selection_data['regions']['region_p_zero'].append({'selection': p_zero_selection})

# now run spatial search for the rest of the phase regions
for r in range(num_of_regions):
    vec_one = get_coords(phase_regions[r][0]['geometry'])
    vec_two = get_coords(phase_regions[r][1]['geometry'])
    g_matrix = [[vec_one[0], vec_one[1]],[vec_two[0], vec_two[1]]]

    vecs = get_vectors_from_wkt(g_matrix)
    e_dist = euclidean_distance(vecs[0][0], vecs[0][1])
    mid = midpoint(vecs[0][0], vecs[0][1])
    vw = get_region_bbox(e_dist, mid)

    selection = graph_object.phase_region_spatial_query(vw)

    count_of_features_in_region = len(selection)
    region_num = r + 1
    print("phase region",region_num,":",count_of_features_in_region,"features")
    # write region to dict

#     region_string = str(region_num)
#     region_name = "region " + region_string
#     selection_data['regions'][region_name] = []
#     selection_data['regions'][region_name].append({'selection': selection})


# with open('phase_region_selection.json'.format(n), 'w') as outfile:
#     json.dump(selection_data, outfile)

context = get_context(routing_result_data)

#print result:
# print(context)

#pretty print:
# print(json.dumps(context, indent=4, sort_keys=True))

''' Construct a CN '''
feature_selection = feature_view_template()

arcs = construct_arcs(data)
variables = construct_variables(data)

print("arcs: ", len(arcs))
print("variables: " , len(variables))

# get vertex indexes
for i in range(len(arcs)):
    arcs[i].get_parent_index(variables)
    arcs[i].get_child_index(variables)

for v in variables:
    v.get_out_arcs(arcs)

    if v.variable_type!='feature':
        v_id = v.vertex_object['id']
        v_type = v.variable_type
        feature = { 'id': v_id, 'type': v_type }
        feature_selection['features'].append(feature)

    if v.variable_type=='feature':
        v_id = v.vertex_object['id']
        v_geometry = v.vertex_object['geometry'] #['wkt']
        v_type = v.variable_type
        feature = { 'id': v_id, 'geometry': v_geometry, 'type': v_type }
        feature_selection['features'].append(feature)

# print result:
# print(feature_selection)

#pretty print:
# print(json.dumps(feature_selection, indent=4, sort_keys=True))

''' Run propagation over the CN '''

for s in range(len(context['journey_context'])):
    comp_id = context['journey_context'][s]['id']
    for nk in variables:
        if nk.get_id()==comp_id:
            for conceptual_scale in range(0, 5):
                p_matrix = context['journey_context'][s]['context_findings'][0][conceptual_scale]
                variable_activation(nk, variables, arcs, conceptual_scale, p_matrix, feature_selection, 1)

#print result:
# print(json.dumps(feature_selection['features']))
# print(json.dumps(feature_selection['views']))

# pretty print
print(json.dumps(feature_selection['views'], indent=4, sort_keys=True))
# print(feature_selection['features'][157])

# write output to json for visualisation

# with open('sct_feature_selection_example.json', 'w') as outfile:
#     json.dump(feature_selection, outfile)


# END 
