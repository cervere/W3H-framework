import numpy as np
import random

valence = [("food",  'float64'),
           ("water", 'float64')]

motion = [("command", '|S64'), ("Iext", 'float64')]

vttype = [("name",  '|S64'),
           ("valence",  valence),
           ("Iext", 'float64')]

global weights, VT, BG, MMA, PC, OFC

weights = np.asarray([.5] * 4)

VT = np.zeros(4, vttype) # Just the representative feature of each stimulus. For eg : stim1 = ("food" : 8, "water" : 1)

MMA = np.zeros(4, motion) # The motor command that will lead to respective stimulus in VT. For eg : mot1 = {"yaw" : 45, move : 1, "expected" : (x,y)}

PC = (0,0) # gives current location - (x,y)

BG = np.zeros(4)

OFC = np.sort(np.random.rand(8)/5)[-4:] #4 random numbers for a pre-registered preference value

global Insula_hunger, Insula_thirst, Insula_energy
Insula_hunger, Insula_thirst, Insula_energy = 0, 0, 100

ACC = []

#VT[:] = 1

global dh, dth, de
dh, dth, de = 1, 2, 1

def updateInsulaWithTime() :
    global Insula_hunger, Insula_thirst, Insula_energy, dh, dth, de
    Insula_hunger += dh
    Insula_thirst += dth
    Insula_energy -= de

def OneToOne(source, target, weights) :
    for i in range(target.shape[0]):
        target[i] += source[i] * weights[i] + random.uniform(0.1, 1.0)/10

def propagate() :
    OneToOne(VT["Iext"], BG, weights)
    OneToOne(BG, MMA["Iext"], weights)

'''
Let's try making a 2D cortex, assign some neurons to certain actions.
Activate one of them, say one representing action A1 (as in, switch it ON),
Assuming BG knows that A1 needs sub actions A11, A12, A13 to occur in sequence,
BG provides gating input to A11, once it is finished then to A12 and so on upto A13.
Once A13 is done, BG provides gate OFF to A1.
'''

OFC = np.zeros((10,10))
MC = np.zeros((10,10))
ACC = np.zeros((10,10))

actionMap = {
"A1" : {"frere" : "", "fils" : "A11"},
"A11" : {"frere" : "A12", "fils" : ""},
"A12" : {"frere" : "A13", "fils" : "A121"},
"A121" : {"frere" : "A122", "fils" : ""},
"A13" : {"frere" : "", "fils" : ""},
}


def traverse(actionMap, key, prefix) :
    if key != '' :
        print prefix + key
        if key in actionMap :
            traverse(actionMap, actionMap[key]["fils"], prefix+"-")
            traverse(actionMap, actionMap[key]["frere"], prefix)

traverse(actionMap, "A1", "-")

#propagate()
print VT, MMA
