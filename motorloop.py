import random
from methods import *

valence = [("food",  'float64'),
           ("water", 'float64')]

motion = [("command", '|S64'), ("Iext", 'float64')]

vttype = [("name",  '|S64'),
           ("valence",  valence),
           ("Iext", 'float64')]

global weights #, VT, BG, MMA,
global PC, OFC

EAT = [4, 10]

weights = np.asarray([.5] * 4)

#VT = np.zeros(4, vttype) # Just the representative feature of each stimulus. For eg : stim1 = ("food" : 8, "water" : 1)

#MMA = np.zeros(4, motion) # The motor command that will lead to respective stimulus in VT. For eg : mot1 = {"yaw" : 45, move : 1, "expected" : (x,y)}

PC = (0,0) # gives current location - (x,y)

OFC = np.sort(np.random.rand(8)/5)[-4:] #4 random numbers for a pre-registered preference value

class MotorCortex(object) :
    def __init__(self):
        self.pop = np.zeros(4, motion)
        self.grid = np.zeros((20,20)) + 0.1
        self.gateActive = False
        self.activeGate = [-1, -1]

class BasalGanglia(object) :
    def __init__(self):
        self.pop = np.zeros(4)
        self.begin = False

    def process(self, moment, MC) :
        # For simplicity, an initial condition, at t=10ms, we trigger EAT condition
        if moment['globalTime'] == 25 :
            eatens = actionMap["EAT"]["ens"]
            MC.grid[eatens[0], eatens[1]] = 1
            MC.gateActive = True
            MC.activeGate = actionMap["EAT"]["ens"]
        if not self.begin :
            plotActivity(plt, MC.grid, 1, 122)
            self.begin = True
            print 'Beginning at [BG] : ' + str(moment['globalTime'])

class VisualCortex(object) :
    def __init__(self, MC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.begin = False

    def process(self, moment) :
        myLoc = moment['state']['location']['position']
        myX, myZ = myLoc["x"], myLoc["z"]
        obX , obZ, obYaws, obName = [], [], [], []
        for it in moment['observation']['viscinity'] :
            obX.append(it["x"])
            obZ.append(it["z"])
            obName.append(it["name"])
        i = 0
        MMA = self.MC.pop
        for it in moment['observation']['appear'] :
            obX.append(it["x"])
            obZ.append(it["z"])
            obName.append(it["name"])
            obYaws.append(it["yaw"])
            VT = self.pop
            VT[i]["name"] = str(it["name"])
            VT[i]["valence"]["food"] = FOOD_VALUES[it["name"]]
            VT[i]["valence"]["water"] = WATER_VALUES[it["name"]]
            VT[i]["Iext"] = 1.
            MMA["command"][i] = str(it["yaw"]) #"turn " + str(it["yaw"]) + "; move 1; wait 3; tpx " + str(it["x"]) + "; "
            i += 1
        if not self.begin :
            plotItems(myX, myZ, obX, obZ, obYaws, 1, 121)
            self.begin = True
            print 'Beginning at [VC] : ' + str(moment['globalTime'])



class Insula(object):
    def __init__(self, hunger=0, thirst=0, energy=100):
        self.hunger = hunger
        self.thirst = thirst
        self.energy = energy

    def timeEffect(self) :
        self.hunger += 1
        self.thirst += 1
        self.energy -= 1

    def status(self) :
        print 'Hunger : %4.2f, Thirst : %4.2f, Energy : %4.2f' % (self.hunger, self.thirst, self.energy)

class PrimarySomatoSensoryCortex(object) :
    def __init__(self, x=0, y=0, z=0, moving=False):
        self.x, self.y, self.z = x, y, z
        self.moving = moving

class AnteriorCingulateCortex(object) :

    '''
        Refer the hunger and thirst values from Insula 1
        Learn the expense rate as per movement and time
        Estimate for each stimulus, the rough cost of action
    '''
    def __init__(self, insula):
        self.insula = insula

    def getCurrentHunger() :
        return self.insula
    def status(self) :
        print 'From ACC : Hunger : %4.2f, Thirst : %4.2f' % (self.insula.hunger, self.insula.thirst)

def OneToOne(source, target, weights) :
    for i in range(target.shape[0]):
        target[i] += source[i] * weights[i] + random.uniform(0.1, 1.0)/10

def propagate(VT, BG, MMA) :
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
ACC = np.zeros((10,10))

actionMap = {
"A1" : {"frere" : "A2", "fils" : "A11"},
"A11" : {"frere" : "A12", "fils" : ""},
"A12" : {"frere" : "A13", "fils" : "A121"},
"A121" : {"frere" : "A122", "fils" : ""},
"A13" : {"frere" : "", "fils" : ""},
}

'''
For ex :
1) Eat
    11) Search (Explore)
        111) Walk until something in appear
        112) Stop - return (x,y)
    12) Locate
        121) Get Location
        122) Orient - return success of turning towards (x,y)
    13) Reach
        131) Plan to Reach
        132) Move - return success of being at (x,y)
    14) Consume
        141) Some time to eat and in the end notify ACC that you ate.
    15) Wait to see if satisfied.
        151) return success that hunger is satisfied
'''
actionMap = {
"EAT" : {"frere" : "", "fils" : "EXPLORE", "act" : "", "ens" : [4, 10]},
"EXPLORE" : {"frere" : "LOCATE", "fils" : "", "act" : "move 1", "ens" : [4, 10]},
"A12" : {"frere" : "A13", "fils" : "A121", "act" : "", "ens" : [4, 10]},
"A121" : {"frere" : "A122", "fils" : "", "act" : "", "ens" : [4, 10]},
"A13" : {"frere" : "", "fils" : "", "act" : "", "ens" : [4, 10]},
}


def traverse(actionMap, key, prefix) :
    if key != '' :
        print prefix + key
        if key in actionMap :
            print actionMap[key]["ens"]
            traverse(actionMap, actionMap[key]["fils"], prefix+"-")
            traverse(actionMap, actionMap[key]["frere"], prefix)

traverse(actionMap, "EAT", "-")

#propagate()
#print VT, MMA
