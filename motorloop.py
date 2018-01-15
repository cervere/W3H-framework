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
        self.grid = np.ones((20,20))
        self.currentSequence = ''
        self.activity = np.zeros((0,0)) + 0.1
        self.state = "IDLE"

    def process(self) :
        if self.state in actionMap :
            return actionMap[self.state]["act"]

class BasalGanglia(object) :
    def __init__(self):
        self.pop = np.zeros(4)
        self.warmup = False
        self.begin = False
        self.MC_gates = np.zeros((20,20))
        self.flagParSeq = []
        self.acting = False

    def process(self, moment, MC) :
        # For simplicity, an initial condition, at t=10ms, we trigger EAT condition
        plot = False
        if not self.warmup :
            plot = True
            plotNum = 222
            state = "IDLE"
            self.warmup = True
            print 'Warming up [BG] : ' + str(moment['globalTime'])
        elif not self.begin :
            plot = True
            plotNum = 224
            state = "EAT"
            self.begin = True
            print 'Beginning at [BG] : ' + str(moment['globalTime'])

        if plot :
            plotActivity(plt, MC.activity, 1, plotNum)

class VisualCortex(object) :
    def __init__(self, MC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.warmup = False
        self.begin = False

    def process(self, moment) :
        plot = True
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
        if not self.warmup :
            self.warmup = True
            plotNum = 221
            print 'Warming up at [VC] : ' + str(moment['globalTime'])
        elif not self.begin :
            plotNum = 223
            plotItems(myX, myZ, obX, obZ, obYaws, 1, 223)
            print 'Beginning at [VC] : ' + str(moment['globalTime'])
            self.begin = True
        else : plot = False
        if plot : plotItems(myX, myZ, obX, obZ, obYaws, 1, plotNum)


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
    def __init__(self, x=0, y=0, z=0, moving=False, turning=False):
        self.x, self.y, self.z = x, y, z
        self.moving = moving
        self.turning = turning

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
"IDLE" : {"next" : "EAT", "frere" : "", "fils" : "EAT", "act" : "", "ens" : [10, 0]},
"EAT" : {"next" : "EXPLORE", "frere" : "IDLE", "fils" : "EXPLORE", "act" : "", "ens" : [10, 4], "OFF" : "IDLE"},
"EXPLORE" : {"next" : "LOCATE", "frere" : "LOCATE", "fils" : "", "act" : "move 1", "ens" : [4, 10], "OFF" : ""},
"LOCATE" : {"next" : "SPOT", "frere" : "REACH", "fils" : "SPOT", "act" : "move 0", "ens" : [4, 10], "OFF" : "EXPLORE"},
"SPOT" : {"next" : "ORIENT", "frere" : "ORIENT", "fils" : "", "act" : "", "ens" : [4, 10], , "OFF" : ""},
"ORIENT" : {"next" : "REACH", "frere" : "", "fils" : "", "act" : "turn ", "ens" : [4, 10], , "OFF" : "LOCATE"},
"REACH" : {"next" : "CONSUME", "frere" : "CONSUME", "fils" : "", "act" : "move 1", "ens" : [4, 10], , "OFF" : ""},
"CONSUME" : {"next" : "IDLE", "frere" : "", "fils" : "", "act" : "wait 10", "ens" : [4, 10], , "OFF" : "EAT"}
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
