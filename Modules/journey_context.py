#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created: 2019
@author: lucasgodfrey

'get_context' function takes the routing result data as its argument and, basesd
on the active attribute of each routing node, assigns a propagation matrix.

Returns a dictionary of k-level routing nodes with propagation matrices
comprised of finding vectors for each conceptual scale.
'''

def get_context(data):
    '''
     Propagation matrix templates to express context as patterns of activation
     over the net, where:
             finding[0] -> finding value for nk_sk & nk_sk_plus_one out arcs
             finding[1] -> finding value for nk_ar out arcs
             finding[2] -> finding value for sk_sk_minus_one out arcs
             finding[3] -> finding value for ar_feature out arcs
     '''
    # O-D/ transfer
    p_matrix_one = [[1,0,0,0], [1,1,0,0], [1,1,0,1], [1,1,1,1], [1,1,1,1]]
    # turn
    p_matrix_two = [[1,0,0,0], [1,0,0,0], [1,1,0,0], [1,1,1,1], [1,1,1,1]]
    # level-transition/ crossing/ connecting
    p_matrix_three = [[1,0,0,0], [1,0,0,0], [1,0,0,0], [1,1,1,1], [1,1,1,1]]
    # intersection
    p_matrix_four = [[1,0,0,0], [1,0,0,0], [1,0,0,0], [1,0,0,0], [1,1,1,1]]


    # create a dictionary for storing the context findings
    temp_context = {}
    temp_context['journey_context'] = []

    # get the k-level routing nodes from the routing result
    w = data['result']['nk_routing_nodes']

    for i in range(len(w)):
        # create an array to store the list of findings
        context_findings = []
        id = w[i]['id']
        # type=='intersection'
        if w[i]['type']=='intersection':
            if w[i]['active']=='traverse':
                context_findings.append(p_matrix_three)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
            if w[i]['active']=='turn':
                context_findings.append(p_matrix_two)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
        #type=='connecting'
        if w[i]['type']=='connecting':
            if w[i]['active']=='traverse':
                context_findings.append(p_matrix_four)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
            if w[i]['active']=='turn':
                context_findings.append(p_matrix_three)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
        #type=='entrance-exit'
        if w[i]['type']=='entrance-exit':
            if w[i]['active']=='traverse':
                context_findings.append(p_matrix_four)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
            if w[i]['active']=='turn':
                context_findings.append(p_matrix_three)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
        #type=='bus'
        if w[i]['type']=='bus':
            if w[i]['active']=='traverse':
                context_findings.append(p_matrix_three)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
            if w[i]['active']=='transfer':
                context_findings.append(p_matrix_one)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
        #type=='train'
        if w[i]['type']=='train':
            if w[i]['active']=='traverse':
                context_findings.append(p_matrix_three)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })
            if w[i]['active']=='transfer':
                context_findings.append(p_matrix_one)
                temp_context['journey_context'].append({
                        'id': id,
                        'context_findings': context_findings
                        })

    return temp_context

# END
