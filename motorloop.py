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

OFC = np.sort(np.random.rand(8)/5)[-4:] #4 random numbers with a pre-registered preference value



#VT[:] = 1

def OneToOne(source, target, weights) :
    for i in range(target.shape[0]):
        target[i] += source[i] * weights[i] + random.uniform(0.1, 1.0)/10

def propagate() :
    OneToOne(VT["Iext"], BG, weights)
    OneToOne(BG, MMA["Iext"], weights)

#propagate()
print VT, MMA
