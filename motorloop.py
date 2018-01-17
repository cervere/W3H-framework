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
        self.activity = np.zeros((20,20)) + 0.1
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
        self._plotCount = 0
    def process(self, moment, VC, PPC, MC) :
        print "state requested ", MC.requestState, ' from ', MC.state
        PPC.checks()
        #PPC.status()
        if not PPC.targetOn or VC.BGOverride :
            if MC.requestState in actionMap :
                #Gate ON in MC
                grantedState = MC.requestState
                MC.state = grantedState
                print 'granted ', MC.requestState
                ens = actionMap[grantedState]["ens"]
                self.MC_gates[ens[0], ens[1]] = 1
                offs = actionMap[grantedState]["OFF"].split(",")
                for off in offs :
                    print 'offing ', off
                    if off != "" and off in actionMap :
                        offens = actionMap[off]["ens"]
                        self.MC_gates[ens[0], ens[1]] = 0
                MC.activity = MC.grid * self.MC_gates + np.random.normal(.1, .01, 1)
                print 'MCC : ', MC.activity
                VC._plotCount += 1
                plotActivity(MC.activity, VC._plotCount, grantedState, actionMap[grantedState]["color"])
                if grantedState == "DECIDE" : self.decide(VC, PPC, MC)

    def decide(self, VC, PPC, MC) :
        MMA = MC.pop
        propagate(VC.pop, self.pop, MMA)
        k = np.argmax(MMA["Iext"])
        print MMA[k]["command"]
        PPC.targetYaw = MMA[k]["command"]["yaw"]
        actionMap["ORIENT"]["act"] = 'turn '+ str(float(PPC.targetYaw)/180.) + '; PPCWait 1; turn 0'
        PPC.targetPos = MMA[k]["command"]["pos"]
        PPC.targetYaw = getYawDelta(PPC.targetPos[0], PPC.targetPos[1], PPC.x, PPC.z, PPC.yaw)
        print 'PPC targetYaw ', PPC.targetYaw, 'currDelta ', getYawDelta(PPC.targetPos[0], PPC.targetPos[1], PPC.x, PPC.z, PPC.yaw), PPC.x, PPC.z
        #actionMap["REACH"]["target"] = MMA[k]["command"]["pos"]




class VisualCortex(object) :
    def __init__(self, MC, PPC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.PPC = PPC
        self.warmup = False
        self.begin = False
        self.BGOverride = False
        self._plotCount = 0

    def process(self, moment) :
        myLoc = moment['state']['location']['position']
        myDir = moment['state']['location']['orientation']
        self.PPC.x, self.PPC.y, self.PPC.z = myLoc["x"], myLoc["y"], myLoc["z"]
        self.PPC.pos = np.array([myLoc["x"], myLoc["z"]])
        self.PPC.yaw = myDir["yaw"]
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
            MMA["command"][i]["yaw"] = it["yaw"]
            MMA["command"][i]["pos"] = np.array([it["x"], it["z"]])
            i += 1

        if self.MC.state == "EXPLORE" and i > 0:
            print 'Found items while trying to locate ', obName, obYaws, self.PPC.x, self.PPC.z
            self.BGOverride = True
            self._plotCount += 1
            plotItems(myX, myZ, obX, obZ, obYaws, self._plotCount, 111)

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
        self.x, self.y, self.z = 0. ,0. ,0.
        self.pos = np.array([self.x, self.z])
        self.yaw = 0.
        self.moving = False
        self.turning = False
        self.waiting = False
        self.targetPos = np.array([None, None]) # Only (x, z)
        self.targetYaw = None
        self.targetOn = False
        self.waitCount = 0
        self.waitSignal = False

    def checks(self) :
        if self.targetOn and self.turning and self.targetYaw is not None :
            print 'target yaw ', self.targetYaw, 'current ', self.yaw
            if np.abs(self.targetYaw - self.yaw) < 1.5 :
                self.waitSignal = False
                #self.turning = False
                self.targetYaw = None
        if self.targetOn and self.moving and self.targetPos.all():
            print 'target pos ', self.targetPos, 'current ', self.pos
            if np.abs(self.targetPos[0] - self.pos[0]) < 0.5 or np.abs(self.targetPos[1] - self.pos[1]) < 0.5 or np.linalg.norm(self.targetPos - self.pos) < .75 :
                self.waitSignal = False
                #self.moving = False
                self.targetPos = np.array([None, None])
        if self.targetOn and self.waiting and self.waitCount == 0 :
            self.waitSignal = False
            #self.waiting = False
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
"IDLE" : {"next" : "EAT", "frere" : "", "fils" : "EAT", "act" : "", "ens" : [0, 8], "OFF" : "CONSUME,EAT", "color" :  "r"},
"EAT" : {"next" : "EXPLORE", "frere" : "HAPPY", "fils" : "EXPLORE", "act" : "wait 1", "ens" : [0, 10], "OFF" : "IDLE", "color" :  "r"},
"EXPLORE" : {"next" : "LOCATE", "frere" : "LOCATE", "fils" : "", "act" : "move .75", "ens" : [3, 6], "OFF" : "", "color" :  "g"},
"LOCATE" : {"next" : "DECIDE", "frere" : "REACH", "fils" : "DECIDE", "act" : "move 0; wait 5", "ens" : [5, 9], "OFF" : "EXPLORE", "color" :  "g"},
"DECIDE" : {"next" : "ORIENT", "frere" : "ORIENT", "fils" : "", "act" : "wait 5", "ens" : [8, 8], "OFF" : "", "color" :  "b"},
"ORIENT" : {"next" : "REACH", "frere" : "", "fils" : "", "act" : "turn ", "ens" : [8, 10], "OFF" : "DECIDE", "color" :  "b"},
"REACH" : {"next" : "CONSUME", "frere" : "CONSUME", "fils" : "", "act" : "move .75; PPCWait 1; move 0", "ens" : [5, 13], "OFF" : "ORIENT,LOCATE", "color" :  "g"},
"CONSUME" : {"next" : "HAPPY", "frere" : "", "fils" : "", "act" : "wait 10;", "ens" : [6, 16], "OFF" : "REACH,EAT", "color" :  "g"}
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
