import random
from methods import *

valence = [("food",  'float64'),
           ("water", 'float64')]

targettype = [("yaw", 'float64'), ("pos", 'float64', 2)]

motion = [("command", targettype), ("Iext", 'float64'), ("note", '|S64') ]

vttype = [("name",  '|S64'),
           ("valence",  valence),
           ("Iext", 'float64')]

valuetype = [("actual", "float64"), ("desired", "float64")]

global weights #, VT, BG, MMA,
global PC

weights = np.asarray([.5] * 4)

#VT = np.zeros(4, vttype) # Just the representative feature of each stimulus. For eg : stim1 = ("food" : 8, "water" : 1)

#MMA = np.zeros(4, motion) # The motor command that will lead to respective stimulus in VT. For eg : mot1 = {"yaw" : 45, move : 1, "expected" : (x,y)}

PC = (0,0) # gives current location - (x,y)

class MotorCortex(object) :
    def __init__(self):
        self.pop = np.zeros(4, motion)
        self.grid = np.ones((20,20))
        self.currentSequence = ''
        self.activity = np.zeros((20,20)) + 0.1
        self.state = ""
        self.requestState = "IDLE"
        self.nextAction = ""
        self.values_move = np.zeros(MAXIMUM_POSITIONS, motion)
        self.values_turn = np.zeros(MAXIMUM_POSITIONS, motion)
        self.estimate_move = np.zeros(1, motion)
        self.estimate_turn = np.zeros(1, motion)

    def process(self, agent_host) :
        agent_host.sendCommand('In Motor')
        if self.state in actionMap :
            self.nextAction = actionMap[self.state]["act"]
            self.requestState = actionMap[self.state]["next"]

class AbstractBasalGanglia(object) :
    def __init__ (self, name, strategy=lambda x : np.argmax(x)) :
        self.name = name
        self.strategy = strategy # Selection strategy - could be choose the maximum or some other

    def select(self, source, target) :
        target[self.strategy(source)] = 1


class BasalGanglia(object) :
    def __init__(self):
        self.pop = np.zeros(4)
        self.warmup = False
        self.begin = False
        self.MC_gates = np.zeros((20,20))
        self._plotCount = 0
        self.msg = ""
    def process(self, moment, VC, PPC, MC, ACC) :
        print "state requested ", MC.requestState, ' from ', MC.state
        PPC.checks()
        #PPC.status()
        print PPC.targetOn, VC.BGOverride
        if not PPC.targetOn or VC.BGOverride :
            if MC.requestState in actionMap :
                print 'here'
                #Gate ON in MC
                grantedState = MC.requestState
                MC.state = grantedState
                self.msg = actionMap[grantedState]["msg"]
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
                #VC._plotCount += 1
                #plotActivity(MC.activity, VC._plotCount, grantedState, actionMap[grantedState]["color"])
                if grantedState == "DECIDE" : self.decide(VC, PPC, MC, ACC)

    def decide(self, VC, PPC, MC, ACC) :
        MMA = MC.pop
        propagate(VC.pop, self.pop, MMA)
        print 'Stats from ACC : Hunger ', ACC.getCurrentHunger(), ', Thirst ', ACC.getCurrentThirst()
        k = np.argmax(MMA["Iext"])
        print MMA[k]["command"]
        PPC.targetYaw = MMA[k]["command"]["yaw"]
        actionMap["ORIENT"]["act"] = 'turn '+ str(float(PPC.targetYaw)/180.) + '; PPCWait 1; turn 0'
        PPC.targetPos = MMA[k]["command"]["pos"]
        PPC.targetYaw = getYawDelta(PPC.targetPos[0], PPC.targetPos[1], PPC.x, PPC.z, PPC.yaw)
        print 'PPC targetYaw ', PPC.targetYaw, 'currDelta ', getYawDelta(PPC.targetPos[0], PPC.targetPos[1], PPC.x, PPC.z, PPC.yaw), PPC.x, PPC.z
        #actionMap["REACH"]["target"] = MMA[k]["command"]["pos"]




class VisualCortex(object) :
    def __init__(self, MC, PPC, ACC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.PPC = PPC
        self.ACC = ACC
        self.warmup = False
        self.begin = False
        self.BGOverride = False
        self._plotCount = 0
        self.values = np.zeros(MAXIMUM_STIMULI, valuetype)

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
        self.values["actual"][:] = 0
        self.ACC.hunger_values[:] = 0
        self.ACC.thirst_values[:] = 0
        for re in moment['observation']['reach'] :
            self.ACC.hunger_values[POPULATIONS[re["name"]]] = FOOD_VALUES[re["name"]]
            self.ACC.thirst_values[POPULATIONS[re["name"]]] = WATER_VALUES[re["name"]]
            self.values["actual"][POPULATIONS[re["name"]]] = 1
        for se in moment['observation']['see'] :
            self.ACC.hunger_values[POPULATIONS[se["name"]]] = FOOD_VALUES[se["name"]]
            self.ACC.thirst_values[POPULATIONS[se["name"]]] = WATER_VALUES[se["name"]]
            self.values["actual"][POPULATIONS[se["name"]]] = 1

        for it in moment['observation']['appear'] :
            self.values["actual"][POPULATIONS[it["name"]]] = 1
            self.ACC.hunger_values[POPULATIONS[it["name"]]] = FOOD_VALUES[it["name"]]
            self.ACC.thirst_values[POPULATIONS[it["name"]]] = WATER_VALUES[it["name"]]
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
        self.values["actual"] +=  np.random.uniform(0,.1, self.values["actual"].size)

        if self.MC.state == "EXPLORE" and i > 0:
            print 'Found items while trying to explore ', obName, obYaws, self.PPC.x, self.PPC.z
            self.BGOverride = True
            self._plotCount += 1
            print 'When objects appeared ; Hunger : ', self.ACC.getCurrentHunger(), ', Thirst : ', self.ACC.getCurrentThirst()
            self.ACC.randomcheck()
            #plotItems(myX, myZ, obX, obZ, obYaws, self._plotCount, 111)
        self.values["desired"] = self.ACC.insula_a.values["desired"]

class Insula_A(object):
    def __init__(self, hunger=0, thirst=0, energy=100):
        self.hunger = hunger
        self.thirst = thirst
        self.energy = energy
        self.values = np.zeros(MAXIMUM_STIMULI, valuetype)

    def timeEffect(self) :
        self.hunger += 1
        self.thirst += 1
        self.energy -= 1

    def moveEffect(self) :
        self.hunger += 2
        self.thirst += 3
        self.energy -= 2

    def status(self) :
        print 'Hunger : %4.2f, Thirst : %4.2f, Energy : %4.2f' % (self.hunger, self.thirst, self.energy)

class Insula_O(object):
    def __init__(self):
        self.values = np.zeros(MAXIMUM_STIMULI, valuetype)

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
        '''
        To start with, values (desired & actual), one for each of the possible positions
        prefixed for the stimuli.
        '''
        self.values_move = np.zeros(MAXIMUM_POSITIONS, valuetype)
        self.values_turn = np.zeros(MAXIMUM_POSITIONS, valuetype)
        self.estimate_move = np.zeros(1, valuetype)
        self.estimate_turn = np.zeros(1, valuetype)


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
            print 'nothing'
        self.update()

    def update(self) :
        self.targetOn = self.moving or self.turning or self.waiting

    def status(self) :
        print 'target', self.targetOn, 'moving', self.moving, 'waiting ', self.waiting, 'turning ', self.turning


class OrbitoFrontalCortex(object) :
    '''
    Receives partially observable state information about stimuli from
    extra cortical structures. Receives food and thirst relevance values of each stimulus
    from Insula_O
    '''

    def __init__(self, insula_o) :
        self.insula_o = insula_o
        self.pref_values = np.zeros(MAXIMUM_STIMULI)

class AnteriorCingulateCortex(object) :

    '''
        Refer the hunger and thirst values from Insula 1
        Learn the expense rate as per movement and time
        Estimate for each stimulus, the rough cost of action
    '''
    def __init__(self, insula_a):
        self.insula_a = insula_a
        self.hunger_values = np.zeros(MAXIMUM_STIMULI)
        self.thirst_values = np.zeros(MAXIMUM_STIMULI)

    def getCurrentHunger(self) :
        return self.insula_a.hunger

    def getCurrentThirst(self) :
        return self.insula_a.thirst

    def randomcheck(self) :
        self.insula_a.values["desired"][:] = 0
        if self.getCurrentThirst() > THIRST_LIMIT :
            for item in THIRST_ITEMS :
                self.insula_a.values["desired"][POPULATIONS[item]] = 1
        if self.getCurrentHunger() > HUNGER_LIMIT :
            for item in HUNGER_ITEMS :
                self.insula_a.values["desired"][POPULATIONS[item]] = 1
        self.insula_a.values["desired"] +=  np.random.uniform(0,.1, self.insula_a.values["desired"].size)


    def status(self) :
        print 'From ACC : Hunger : %4.2f, Thirst : %4.2f' % (self.insula_a.hunger, self.insula_a.thirst)

class Connection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source
        self.target = target
        self.weights= weights

    def propagate(self) :
        for i in range(MAXIMUM_STIMULI) :
            self.target[i] = self.weights[i] * self.source[i]

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
"IDLE" : {"next" : "EAT", "frere" : "", "fils" : "EAT", "act" : "", "ens" : [0, 8], "OFF" : "CONSUME,EAT", "color" :  "r", "msg" : "I'm jobless!!"},
"EAT" : {"next" : "EXPLORE", "frere" : "HAPPY", "fils" : "EXPLORE", "act" : "wait 1", "ens" : [0, 10], "OFF" : "IDLE", "color" :  "r", "msg" :  "I feel like eating something"},
"EXPLORE" : {"next" : "LOCATE", "frere" : "LOCATE", "fils" : "", "act" : "move .75", "ens" : [3, 6], "OFF" : "", "color" :  "g", "msg" : "Let me explore a bit!"},
"LOCATE" : {"next" : "DECIDE", "frere" : "REACH", "fils" : "DECIDE", "act" : "move 0; wait 5", "ens" : [5, 9], "OFF" : "EXPLORE", "color" :  "g", "msg" : "Ooh..I find something around!"},
"DECIDE" : {"next" : "ORIENT", "frere" : "ORIENT", "fils" : "", "act" : "wait 5", "ens" : [8, 8], "OFF" : "", "color" :  "b", "msg" : "I'm trying to decide!"},
"ORIENT" : {"next" : "REACH", "frere" : "", "fils" : "", "act" : "turn ", "ens" : [8, 10], "OFF" : "DECIDE", "color" :  "b", "msg" : "I chose something, I will orient towards it."},
"REACH" : {"next" : "CONSUME", "frere" : "CONSUME", "fils" : "", "act" : "move .5; PPCWait 1; move 0", "ens" : [5, 13], "OFF" : "ORIENT,LOCATE", "color" :  "g", "msg" : "I will approach this object"},
"CONSUME" : {"next" : "IDLE", "frere" : "", "fils" : "", "act" : "wait 10; tpx 0.; setYaw 0", "ens" : [6, 16], "OFF" : "REACH,EAT", "color" :  "g", "msg" : "I got it! Nom.. nom.. nom.."}
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
