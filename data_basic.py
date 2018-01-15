import json
from pprint import pprint
from constants import *
import numpy as np

ITEM_Z_POINTS = (np.arange(3)+1)*15 - np.random.random_integers(5, 8, 1)
ITEM_X_POINTS = np.sort(np.concatenate((np.random.random_integers(-8, -1, 2), np.random.random_integers(1, 8, 2))))

CAKE_POINTS, APPLE_POINTS, WATER_BUCKET_POINTS, MUSHROOM_STEW_POINTS = "[", "[", "[", "["
for z in ITEM_Z_POINTS :
    np.random.shuffle(ITEM_X_POINTS)
    CAKE_POINTS += '"(' + str(ITEM_X_POINTS[0]) + "," + str(Y_BASIC_FLOOR) + "," + str(z) + ')",'
    APPLE_POINTS += '"(' + str(ITEM_X_POINTS[1]) + "," + str(Y_BASIC_FLOOR) + "," + str(z) + ')",'
    WATER_BUCKET_POINTS += '"(' + str(ITEM_X_POINTS[2]) + "," + str(Y_BASIC_FLOOR) + "," + str(z) + ')",'
    MUSHROOM_STEW_POINTS += '"(' + str(ITEM_X_POINTS[3]) + "," + str(Y_BASIC_FLOOR) + "," + str(z) + ')",'

CAKE_POINTS = CAKE_POINTS[:-1] + "]"
APPLE_POINTS = APPLE_POINTS[:-1] + "]"
WATER_BUCKET_POINTS = WATER_BUCKET_POINTS[:-1] + "]"
MUSHROOM_STEW_POINTS = MUSHROOM_STEW_POINTS[:-1] + "]"


LAVA_POINTS = '''
        [
            "(5,226,9)", "(5,226,14)", "(5,226,19)",
            "(5,226,29)", "(5,226,39)"
        ]
        '''

STAINED_GLASS_PANE_POINTS = '''
        [
            "(5,226,9)", "(5,226,14)", "(5,226,19)",
            "(5,226,29)", "(5,226,39)"
        ]
        '''
GRAVEL_POINTS = '''
        ["(5,226,50)"]
        '''


blocks_basic = json.loads('''
{
"config" : [
        {
            "type" : "lava",
            "active" : "False",
            "points" :
            '''
            + LAVA_POINTS +
            '''
        },
        {
            "type" : "stained_glass_pane",
            "active" : "False",
            "points" :
            '''
            + STAINED_GLASS_PANE_POINTS +
            '''
        },
        {
            "type" : "gravel",
            "active" : "False",
            "points" :
            '''
            + GRAVEL_POINTS +
            '''
        },
        {
            "type" : "cobblestone",
            "active" : "False",
            "points" : [
                        "(5,226,35)", "(5,226,15)", "(5,226,-5)",
                        "(5,226,-25)", "(5,226,-45)"
                        ]
        }
    ]
}
''')

floor_basic = json.loads('''
{
"config" : [
        {
            "type" : "sandstone",
            "points" : ["{(-50,226,0):(50,226,50)}"]
        },
        {
            "type" : "lapis_block",
            "points" : [
                "{(0,226,0):(0,226,50)}"
            ]
        },
        {
            "type" : "stone",
            "active" : "False",
            "points" : [
                "{(5,227,-33):(5,227,-33)}",
                "{(5,227,-13):(5,227,-13)}",
                "{(5,227,3):(5,227,3)}",
                "{(5,227,23):(5,227,23)}",
                "{(5,227,43):(5,227,43)}"
            ]
        }
    ]
}
''')

CAKE_POINTS = '["(2, 226, 10)"]'#, "(-4, 226, 10)"]'
APPLE_POINTS = '["(4, 226, 10)"]'#, "(-8, 226, 10)"]'
MUSHROOM_STEW_POINTS = '["(-3, 226, 10)"]'#, "(-2, 226, 10)"]'
WATER_BUCKET_POINTS = '["(-5, 226, 10)"]'#, "(-6, 226, 10)"]'
items_basic = json.loads('''
{
"config" : [
        {
            "type" : "cake",
            "active" : "True",
            "points" :
            '''
            + CAKE_POINTS +
            '''
        },
        {
            "type" : "apple",
            "points" :
            '''
            + APPLE_POINTS +
            '''
        },
        {
            "type" : "water_bucket",
            "active" : "True",
            "points" :
            '''
            + WATER_BUCKET_POINTS +
            '''
        },
        {
            "type" : "mushroom_stew",
            "active" : "True",
            "points" :
            '''
            + MUSHROOM_STEW_POINTS +
            '''
        }
    ]
}
''')
