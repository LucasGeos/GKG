#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 2019
@author: lucasgodfrey

Functions for demonstrating the propagation of context over the net as a basis
for automatically constructing data to support a context-dependent
interactive multiscale information space, i.e. the presenece of features in the
overall selection, and the peristence of those features across spatial scales
(zoom interactions).
"""

def variable_activation(variable, variables, arcs, scheme_index,
    propagation_scheme, selection_dict, counter):
    '''
    Main function to run propagation over the net, starting at k-level routing
    node variables ('NK') using the propagation scheme for the current
    conceptual scale.

    The scheme index is the conceptual scale, and the propagation scheme is the
    finding for the parent NK variable for the activation trace at that scale.
    '''
    # get the variable's out arcs
    activated_variables = []
    out_arcs = variable.out_arcs
    print('newly activated variable id:', variable.get_id())
    print('newly activated variable type: ', variable.variable_type)
    print('newly activated variable out arcs: ', out_arcs)
    # return a list of out arcs that are in paths in the current trace
    print('finding: ',propagation_scheme)
    p_scheme_mapping = map_finding_to_arcs(propagation_scheme, arcs, out_arcs, counter)
    # return activated child variables on the filtered set of out arcs
    activated_variables = propagate(variables, arcs, p_scheme_mapping)
    # merge the variables with the current index based on feature type,
    # ...and add the indexes to the view space data
    for av in activated_variables:
        print("activated variable: ", av.get_id())

    merge_index(scheme_index, activated_variables, selection_dict)

    count = counter + 1
    # for each newly activated variable, recursively call variable_activation
    if len(activated_variables)==0:
        print('count of activated variables:', len(activated_variables))

    if len(activated_variables) > 0:
        for v in activated_variables:
            if v.variable_type != 'nk':
                variable_activation(v, variables, arcs, scheme_index,
                    propagation_scheme, selection_dict, count)


def map_finding_to_arcs(propagation_scheme, arcs, out_arcs, counter):
    '''
    Return a list of out arcs that are in paths in the current trace, using the
    counter as a way of expressing the reduction in the length of the finding
    at each level of Variable depth in the net (max topological distance of
    two in this case).
    '''
    active_paths = []

    if counter==1:
        if propagation_scheme[0]==1:
            for a in out_arcs:
                if arcs[a].arc_type=='nk_sk':
                    active_paths.append(a)
                if arcs[a].arc_type=='nk_sk_plus_one':
                    active_paths.append(a)

        if propagation_scheme[1]==1:
            for a in out_arcs:
                if arcs[a].arc_type=='nk_ar':
                    active_paths.append(a)

    if counter==2:
        if propagation_scheme[2]==1:
            for a in out_arcs:
                if arcs[a].arc_type=='sk_sk_minus_one':
                    active_paths.append(a)

        if propagation_scheme[3]==1:
            for a in out_arcs:
                if arcs[a].arc_type=='ar_feature':
                    active_paths.append(a)

    return active_paths


def propagate(variables, arcs, active_out_arcs):
    '''
    Return activated child variables on the filtered set of out arcs
    '''
    activated_variables = []
    print(active_out_arcs)

    for a in active_out_arcs:
        print("arc: ", a)
        av = arcs[a].variable_indexes
        for v in av:
            print("variable: ", v)
            activated_variables.append(variables[v])

    return activated_variables


def merge_index(scheme_index, activated_variables, selection_dict):
    '''
    Merge to ensure that if a feature is activated at a given conceptual scale,
    its variable index value is present for the correct feature type at that
    scale, but that it is unique at that scale (i.e. appears either 0 times or
    appears once)
    '''
    global array_pos

    if scheme_index==0:
        scale = 'scale_1'
        array_pos = 0
    elif scheme_index==1:
        scale =  'scale_2'
        array_pos = 1
    elif scheme_index==2:
        scale = 'scale_3'
        array_pos = 2
    elif scheme_index==3:
        scale = 'scale_4'
        array_pos = 3
    elif scheme_index==4:
        scale = 'scale_5'
        array_pos = 4

    for v in activated_variables:
        ''' persistence of features expressed across conceptual scales '''
        # sk
        if v.variable_type=='sk':
            c1 = selection_dict['views'][array_pos][scale][0]['SK']
            if len(c1)==0:
                # append to the feature index
                c1.append(v.index_position)
                ind = v.index_position
            else:
                if v.index_position not in c1:
                    c1.append(v.index_position)

        # sk_plus_one
        if v.variable_type=='sk_plus_one':
            c2 = selection_dict['views'][array_pos][scale][0]['SK_PLUS_ONE']
            if len(c2)==0:
                # append to the feature index
                c2.append(v.index_position)
                ind = v.index_position
            else:
                if v.index_position not in c2:
                    c2.append(v.index_position)

        # sk_minus_one
        if v.variable_type=='sk_minus_one':
            c3 = selection_dict['views'][array_pos][scale][0]['SK_MINUS_ONE']
            if len(c3)==0:
                # append to the feature index
                c3.append(v.index_position)
                ind = v.index_position

            else:
                if v.index_position not in c3:
                    c3.append(v.index_position)

        # feature
        if v.variable_type=='feature':
            c4 = selection_dict['views'][array_pos][scale][0]['FEATURES']
            if len(c4)==0:
                # append to the feature index
                c4.append(v.index_position)
                ind = v.index_position

            else:
                if v.index_position not in c4:
                    c4.append(v.index_position)


# END
