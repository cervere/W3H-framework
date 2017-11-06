'''
    VITALS
'''
THIRST_DEFAULT = 10
THIRST_LIMIT = 20
THIRST_RATE_INC = {"move" : 1, "jump" : 3}
HUNGER_DEFAULT = 10
HUNGER_LIMIT = 20
HUNGER_RATE_INC = {"move" : 1, "jump" : 3}
HUNGER_RATE_DEC = {"consume" : 3}


'''
    ACTIONS
'''
TURN_RIGHT  = "setYaw 45; wait 10; setYaw -45; wait 10; tpx 5.5; setYaw 0; "
TURN_LEFT  = "setYaw -45; wait 10; setYaw 45; wait 10; tpx 5.5; setYaw 0; "
ATTACK = "hotbar.9 1; hotbar.9 0; pitch 1; wait 5; pitch 0; attack 1; wait 5; attack 0; pitch -1; wait 5; pitch 0"
