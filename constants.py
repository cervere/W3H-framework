AGENT_NAME = "OSS 117"

MAXIMUM_STIMULI = 4
MAXIMUM_STIMULI_WITH_IMAGINARY = MAXIMUM_STIMULI + 1
MAXIMUM_POSITIONS = MAXIMUM_STIMULI

'''
COORDINATE CONSTANTS
'''
Y_BASIC_FLOOR = 226
Y_BASIC_ITEM = 227


'''
    VITALS
'''
THIRST_DEFAULT = 2
THIRST_LIMIT = 4
THIRST_FATAL_LIMIT = 15
THIRST_RATE_INC = {"move" : 1, "jump" : 3}
HUNGER_DEFAULT = 1
HUNGER_LIMIT = 3
HUNGER_FATAL_LIMIT = 15
HUNGER_RATE_INC = {"move" : 1, "jump" : 3}
HUNGER_RATE_DEC = {"consume" : 3}

PREFERENCE_VALUES = {"apple" : 6, "cake" : 9, "water_bucket" : 5, "mushroom_stew" : 7}
FOOD_VALUES = {"apple" : 9, "cake" : 7, "water_bucket" : 3, "mushroom_stew" : 4}
WATER_VALUES = {"apple" : 2, "cake" : 1, "water_bucket" : 9, "mushroom_stew" : 7}


POPULATIONS = {"apple" : 0, "cake" : 1, "water_bucket" : 2, "mushroom_stew" : 3, "imaginary" : 4}
HUNGER_ITEMS = ["apple", "cake"]
THIRST_ITEMS = ["water_bucket", "mushroom_stew"]

'''
    ACTIONS
'''
TURN_RIGHT  = "setYaw 45; wait 10; setYaw -45; wait 10; tpx 5.5; setYaw 0; "
TURN_LEFT  = "setYaw -45; wait 10; setYaw 45; wait 10; tpx 5.5; setYaw 0; "
ATTACK = "hotbar.9 1; hotbar.9 0; pitch 1; wait 5; pitch 0; attack 1; wait 5; attack 0; pitch -1; wait 5; pitch 0"
