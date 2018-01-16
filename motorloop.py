import random
from methods import *

valence = [("food",  'float64'),
           ("water", 'float64')]

targettype = [("yaw", 'float64'), ("pos", 'float64', 2)]

motion = [("command", targettype), ("Iext", 'float64')]

vttype = [("name",  '|S64'),
           ("valence",  valence),
           ("Iext", 'float64')]

global weights #, VT, BG, MMA,
global PC, OFC

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
        self.state = ""
        self.requestState = "IDLE"
        self.nextAction = ""

    def process(self) :
        if self.state in actionMap :
            self.nextAction = actionMap[self.state]["act"]
            self.requestState = actionMap[self.state]["next"]

class BasalGanglia(object) :
    def __init__(self):
        self.pop = np.zeros(4)
        self.warmup = False
        self.begin = False
        self.MC_gates = np.zeros((20,20))

    def process(self, moment, VC, PPC, MC) :
        print "state requested ", MC.requestState, ' from ', MC.state
        PPC.checks(MC)
        PPC.status()
        if not PPC.targetOn or VC.BGOverride :
            if MC.requestState in actionMap :
                #Gate ON in MC
                grantedState = MC.requestState
                MC.state = grantedState
                print 'granted ', MC.requestState
                ens = actionMap[grantedState]["ens"]
                self.MC_gates[ens[0], ens[1]] = 1
                off = actionMap[grantedState]["OFF"]
                if off != "" and off in actionMap :
                    offens = actionMap[off]["ens"]
                    self.MC_gates[ens[0], ens[1]] = 0
                MC.activity = MC.grid * self.MC_gates + np.random.normal(.1, .01, 1)
                plotActivity(plt, MC.activity, 1, actionMap[grantedState]["plotNum"], grantedState)
                if grantedState == "DECIDE" : self.decide(VC, MC)

    def decide(self, VC, MC) :
        MMA = MC.pop
        propagate(VC.pop, self.pop, MMA)
        k = np.argmax(MMA["Iext"])
        print MMA[k]["command"]
        deltaTurn = MMA[k]["command"]["yaw"]
        actionMap["ORIENT"]["act"] = 'turn '+ str(float(deltaTurn)/180.)
        actionMap["REACH"]["target"] = MMA[k]["command"]["pos"]




class VisualCortex(object) :
    def __init__(self, MC, PPC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.PPC = PPC
        self.warmup = False
        self.begin = False
        self.BGOverride = False

    def process(self, moment) :
        myLoc = moment['state']['location']['position']
        self.PPC.x, self.PPC.y, self.PPC.z = myLoc["x"], myLoc["y"], myLoc["z"]
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
            obYaws.append(it["yaw"])
            VT = self.pop
            VT[i]["name"] = str(it["name"])
            VT[i]["valence"]["food"] = FOOD_VALUES[it["name"]]
            VT[i]["valence"]["water"] = WATER_VALUES[it["name"]]
            VT[i]["Iext"] = 1.
            MMA["command"][i]["yaw"] = it["yaw"]
            MMA["command"][i]["pos"] = np.array([it["x"], it["z"]])
            i += 1
        print self.MC.state, obX , obZ, obYaws, obName
        print 'before Found'

        if self.MC.state == "EXPLORE" and i > 0:
            print 'Found items while trying to locate'
            self.BGOverride = True
            #plotItems(myX, myZ, obX, obZ, obYaws, 2, 223)
        print 'after found'

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
    def __init__(self):
        self.x, self.y, self.z = (0. ,0. ,0.)
        self.pos = np.array([self.x, self.z])
        self.yaw = 0.
        self.moving = False
        self.turning = False
        self.waiting = False
        self.targetPos = np.array([None, None]) # Only (x, z)
        self.targetYaw = None
        self.targetOn = False
        self.waitCount = 0

    def checks(self, MC) :
        if self.targetOn and self.turning and self.targetYaw is not None :
            if np.abs(self.targetYaw - self.yaw) < 2 :
                self.turning = False
                self.targetYaw = None
        if self.targetOn and self.moving and self.targetPos.all():
            if np.linalg.norm(self.targetPos - self.pos) < 0.5  :
                self.moving = False
                self.targetPos = np.array([None, None])
        if self.targetOn and self.waiting and self.waitCount == 0 :
            self.waiting = False
        self.update()

    def update(self) :
        self.targetOn = self.moving or self.turning or self.waiting

    def status(self) :
        print 'target', self.targetOn, 'moving', self.moving, 'waiting ', self.waiting, 'turning ', self.turning



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
"IDLE" : {"next" : "EAT", "frere" : "", "fils" : "EAT", "act" : "", "ens" : [10, 0], "OFF" : "", "plotNum" : 181},
"EAT" : {"next" : "EXPLORE", "frere" : "IDLE", "fils" : "EXPLORE", "act" : "wait 1", "ens" : [10, 2], "OFF" : "IDLE", "plotNum" : 182},
"EXPLORE" : {"next" : "LOCATE", "frere" : "LOCATE", "fils" : "", "act" : "move .75", "ens" : [4, 10], "OFF" : "", "plotNum" : 183},
"LOCATE" : {"next" : "DECIDE", "frere" : "REACH", "fils" : "DECIDE", "act" : "move 0; wait 5", "ens" : [4, 10], "OFF" : "EXPLORE", "plotNum" : 184},
"DECIDE" : {"next" : "ORIENT", "frere" : "ORIENT", "fils" : "", "act" : "wait 5", "ens" : [4, 10], "OFF" : "", "plotNum" : 185},
"ORIENT" : {"next" : "REACH", "frere" : "", "fils" : "", "act" : "turn ", "ens" : [4, 10], "OFF" : "LOCATE", "plotNum" : 186},
"REACH" : {"next" : "CONSUME", "frere" : "CONSUME", "fils" : "", "act" : "move 1", "ens" : [4, 10], "OFF" : "", "plotNum" : 187, "target" : []},
"CONSUME" : {"next" : "IDLE", "frere" : "", "fils" : "", "act" : "move 0; wait 10", "ens" : [4, 10], "OFF" : "EAT", "plotNum" : 188}
}


def traverse(actionMap, key, prefix) :
    if key != '' :
        print prefix + key
        if key in actionMap :
            print actionMap[key]["ens"]
            traverse(actionMap, actionMap[key]["fils"], prefix+"-")
            traverse(actionMap, actionMap[key]["frere"], prefix)

#traverse(actionMap, "EAT", "-")

#propagate()
#print VT, MMA
