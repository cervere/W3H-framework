import numpy as np
import random

valence = [("food",  float),
           ("water", float)]

motion = [("command", str), ("Iext", float)]

vttype = [("name",  str),
           ("valence",  valence),
           ("Iext", float)]

global weights, VT, BG, MMA, PC

weights = np.asarray([.5] * 4)

VT = np.zeros(4, vttype) # Just the representative feature of each stimulus. For eg : stim1 = ("food" : 8, "water" : 1)

MMA = np.zeros(4, motion) # The motor command that will lead to respective stimulus in VT. For eg : mot1 = {"yaw" : 45, move : 1, "expected" : (x,y)}

PC = (0,0) # gives current location - (x,y)

BG = np.zeros(4)

#VT[:] = 1

def OneToOne(source, target, weights) :
    for i in range(target.shape[0]):
        target[i] += source[i] * weights[i] + random.uniform(0.1, 1.0)/10

def propagate() :
    OneToOne(VT["Iext"], BG, weights)
    OneToOne(BG, MMA["Iext"], weights)

#propagate()
print VT, MMA