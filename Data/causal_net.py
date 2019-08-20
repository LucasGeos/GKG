#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 2019
@author: lucasgodfrey

Causal net module for demonstrating the creation of a cn instance from a
subgraph of geographic features.
"""

class Variable(object):
    '''
    Class to represent a variable in a causal net, where each variable is
    constructed from vertices in an underlying graph.
    '''
    def __init__(self, vertex_object, index_position, variable_type):
        self.vertex_object = vertex_object
        self.index_position = index_position
        self.variable_type = variable_type
        self.out_arcs = []

    def get_id(self):
        ''' Return the variable's id '''
        return self.vertex_object['id']

    def get_out_arcs(self, arcs):
        '''
        Get the index position of out arcs for this variable from the overall
        list of arcs
        '''
        for i in range(len(arcs)):
            if self.index_position==arcs[i].variable_indexes[0]:
                self.out_arcs.append(i)
        return self.out_arcs



class Arc(object):
    '''
    Class to represent an arc in a causal net, where each arc is constructed
    from edges in an underlying graph.
    '''
    def __init__(self, edge_object, edges, arc_type):
        '''
        '''
        self.edge_object = edge_object
        self.edges = edges
        self.arc_type = arc_type
        self.variable_indexes = []

    def get_parent_index(self, variables):
        '''
        '''
        for i in range(len(variables)):
            if (self.edge_object['parent']==variables[i].get_id()):
                self.variable_indexes.append(i)

    def get_child_index(self, variables):
        '''
        '''
        for i in range(len(variables)):
            if (self.edge_object['child']==variables[i].get_id()):
                self.variable_indexes.append(i)


def construct_variables(data):
    '''
    Takes a dictionary representation of a graph of geographic features as input
    (a subgraph result from a query on a database) and returns a list of
    variable object instances for each feature.
    '''
    variables = []

    # get the subgraph feature data
    nk_vertices = data['vertices']['NK']
    sk_vertices = data['vertices']['SK']
    ar_vertices = data['vertices']['AR']
    sk_plus_one_vertices = data['vertices']['SK_PLUS_ONE']
    sk_minus_one_vertices = data['vertices']['SK_MINUS_ONE']
    feature_vertices = data['vertices']['FEATURES']

    ''' Create variables '''
    # sepereate list of nk
    nk_variables = []

    for i in range(len(nk_vertices)):
        v = Variable(nk_vertices[i], i, "nk")
        nk_variables.append(v)

    for i in range(len(nk_vertices)):
        v = Variable(nk_vertices[i], i, "nk")
        variables.append(v)
        temp_index = i + 1

    for i in range(len(sk_vertices)):
        v = Variable(sk_vertices[i], temp_index+i, "sk")
        variables.append(v)
        temp_index_2 = temp_index + i + 1

    for i in range(len(ar_vertices)):
        v = Variable(ar_vertices[i], temp_index_2+i, "ar")
        variables.append(v)
        temp_index_3 = temp_index_2 + i + 1


    for i in range(len(sk_plus_one_vertices)):
        v = Variable(sk_plus_one_vertices[i], temp_index_3+i, "sk_plus_one")
        variables.append(v)
        temp_index_4 = temp_index_3 + i + 1

    for i in range(len(sk_minus_one_vertices)):
        v = Variable(sk_minus_one_vertices[i], temp_index_4+i, "sk_minus_one")
        variables.append(v)
        temp_index_5 = temp_index_4 + i + 1

    for i in range(len(feature_vertices)):
        v = Variable(feature_vertices[i], temp_index_5+i, "feature")
        variables.append(v)

    return variables


def construct_arcs(data):
    ''' Return a list of arc objects '''
    arcs = []

    ''' Create arcs '''
    nk_sk_edges = data['edges']['NK_SK_BOUNDS']
    #
    for i in range(len(nk_sk_edges)):
        arc = Arc(nk_sk_edges[i], nk_sk_edges, "nk_sk")
        arcs.append(arc)

    nk_ar_edges=data['edges']['NK_AR_ACTIVATES']
    #
    for i in range(len(nk_ar_edges)):
        arc = Arc(nk_ar_edges[i], nk_ar_edges, "nk_ar")
        arcs.append(arc)

    nk_sk_plus_one_edges=data['edges']['NK_SK_PLUS_ONE_BOUNDS']
    #
    for i in range(len(nk_sk_plus_one_edges)):
        arc = Arc(nk_sk_plus_one_edges[i], nk_sk_plus_one_edges, "nk_sk_plus_one")
        arcs.append(arc)

    sk_sk_minus_one_edges = data['edges']['SK_SK_MINUS_ONE_IN_REGION']
    #
    for i in range(len(sk_sk_minus_one_edges)):
        arc = Arc(sk_sk_minus_one_edges[i], sk_sk_minus_one_edges,"sk_sk_minus_one")
        arcs.append(arc)

    ar_feature_edges = data['edges']['CONTAINS_FEATURE']
    #
    for i in range(len(ar_feature_edges)):
        arc = Arc(ar_feature_edges[i], ar_feature_edges, "ar_feature")
        arcs.append(arc)

    return arcs


def feature_view_template():
    '''
    Return a template dictionary to store the features and the views in the
    current journey context
    '''
    feature_selection = {}

    feature_selection['features'] = []
    feature_selection['views'] = []
    # 5 scales to represent each conceptual scale
    scale_1 = {}
    scale_2 = {}
    scale_3 = {}
    scale_4 = {}
    scale_5 = {}
    # add the conceptual scale dictionaries to the views array object
    feature_selection['views'].append(scale_1)
    feature_selection['views'].append(scale_2)
    feature_selection['views'].append(scale_3)
    feature_selection['views'].append(scale_4)
    feature_selection['views'].append(scale_5)
    # add an array object to each scale to hold feature index values
    feature_selection['views'][0]['scale_1'] = []
    feature_selection['views'][1]['scale_2'] = []
    feature_selection['views'][2]['scale_3'] = []
    feature_selection['views'][3]['scale_4'] = []
    feature_selection['views'][4]['scale_5'] = []
    # create the dictionaries to hold each type of feature at each scale
    SK = {}
    SK_PLUS_ONE = {}
    SK_MINUS_ONE = {}
    FEATURES = {}

    SK2 = {}
    SK_PLUS_ONE2 = {}
    SK_MINUS_ONE2 = {}
    FEATURES2 = {}

    SK3 = {}
    SK_PLUS_ONE3 = {}
    SK_MINUS_ONE3 = {}
    FEATURES3 = {}

    SK4 = {}
    SK_PLUS_ONE4 = {}
    SK_MINUS_ONE4 = {}
    FEATURES4 = {}

    SK5 = {}
    SK_PLUS_ONE5 = {}
    SK_MINUS_ONE5 = {}
    FEATURES5 = {}

    feature_selection['views'][0]['scale_1'].append(SK)
    feature_selection['views'][0]['scale_1'].append(SK_PLUS_ONE)
    feature_selection['views'][0]['scale_1'].append(SK_MINUS_ONE)
    feature_selection['views'][0]['scale_1'].append(FEATURES)

    feature_selection['views'][0]['scale_1'][0]['SK'] = []
    feature_selection['views'][0]['scale_1'][0]['SK_PLUS_ONE'] = []
    feature_selection['views'][0]['scale_1'][0]['SK_MINUS_ONE'] = []
    feature_selection['views'][0]['scale_1'][0]['FEATURES'] = []

    feature_selection['views'][1]['scale_2'].append(SK2)
    feature_selection['views'][1]['scale_2'].append(SK_PLUS_ONE2)
    feature_selection['views'][1]['scale_2'].append(SK_MINUS_ONE2)
    feature_selection['views'][1]['scale_2'].append(FEATURES2)

    feature_selection['views'][1]['scale_2'][0]['SK'] = []
    feature_selection['views'][1]['scale_2'][0]['SK_PLUS_ONE'] = []
    feature_selection['views'][1]['scale_2'][0]['SK_MINUS_ONE'] = []
    feature_selection['views'][1]['scale_2'][0]['FEATURES'] = []

    feature_selection['views'][2]['scale_3'].append(SK3)
    feature_selection['views'][2]['scale_3'].append(SK_PLUS_ONE3)
    feature_selection['views'][2]['scale_3'].append(SK_MINUS_ONE3)
    feature_selection['views'][2]['scale_3'].append(FEATURES3)

    feature_selection['views'][2]['scale_3'][0]['SK'] = []
    feature_selection['views'][2]['scale_3'][0]['SK_PLUS_ONE'] = []
    feature_selection['views'][2]['scale_3'][0]['SK_MINUS_ONE'] = []
    feature_selection['views'][2]['scale_3'][0]['FEATURES'] = []

    feature_selection['views'][3]['scale_4'].append(SK4)
    feature_selection['views'][3]['scale_4'].append(SK_PLUS_ONE4)
    feature_selection['views'][3]['scale_4'].append(SK_MINUS_ONE4)
    feature_selection['views'][3]['scale_4'].append(FEATURES4)

    feature_selection['views'][3]['scale_4'][0]['SK'] = []
    feature_selection['views'][3]['scale_4'][0]['SK_PLUS_ONE'] = []
    feature_selection['views'][3]['scale_4'][0]['SK_MINUS_ONE'] = []
    feature_selection['views'][3]['scale_4'][0]['FEATURES'] = []

    feature_selection['views'][4]['scale_5'].append(SK5)
    feature_selection['views'][4]['scale_5'].append(SK_PLUS_ONE5)
    feature_selection['views'][4]['scale_5'].append(SK_MINUS_ONE5)
    feature_selection['views'][4]['scale_5'].append(FEATURES5)

    feature_selection['views'][4]['scale_5'][0]['SK'] = []
    feature_selection['views'][4]['scale_5'][0]['SK_PLUS_ONE'] = []
    feature_selection['views'][4]['scale_5'][0]['SK_MINUS_ONE'] = []
    feature_selection['views'][4]['scale_5'][0]['FEATURES'] = []

    return feature_selection


# END
