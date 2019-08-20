#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 2019
@author: lucasgodfrey

phase region module to calculate the bounding boxes of spatial regions as a
basis for spatial queries on a graph database
"""

import numpy as np


def get_vectors_from_wkt(wgs84_region):
    '''
    Ensure that the bounding coordinates are in the form '(v, w)', and correctly
    ordered. This function assumes wgs84_region is a matrix of lat lon values.
    Values are still of type string so are converted here...
    '''
    spatial_region = []
    x_1 = float(wgs84_region[0][0])
    x_2 = float(wgs84_region[1][0])
    y_1 = float(wgs84_region[0][1])
    y_2 = float(wgs84_region[1][1])

    if x_1 < x_2:
        spatial_region.append([[x_1, y_1],[x_2, y_2]])
    else:
        spatial_region.append([[x_2, y_2],[x_1, y_1]])

    # return the bounding coordinates in the form (v, w)
    return spatial_region

def sqr(x):
    s = x * x
    return s


def euclidean_distance(v, w):
    d = np.sqrt(sqr(v[0] - w[0]) + sqr(v[1] - w[1]))
    return d


def midpoint(v, w):
    m_x = (v[0] + w[0]) / 2
    m_y = (v[1] + w[1]) / 2
    m = [m_x, m_y]
    return m


def get_region_bbox(size, midpoint):
    '''
    Return upper right and lower left coordinates as basis for spatial query
    using 'spatial.bbox'
    '''
    lat_upper_right = midpoint[1] - (size / 2)
    # print('lat_upper_right', lat_upper_right)
    lon_upper_right = midpoint[0] + (size / 2)
    # print('lon_upper_right', lon_upper_right)
    lat_lower_left = midpoint[1] + (size / 2)
    # print('lat_lower_left', lat_lower_left)
    lon_lower_left = midpoint[0] - (size / 2)
    # print('lon_lower_left', lon_lower_left)
    vw = [[lon_lower_left, lat_lower_left],[lon_upper_right, lat_upper_right]]

    return vw


# END
