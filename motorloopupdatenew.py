import random
from methods import *

valence = [("food",  'float64'),
           ("water", 'float64')]

targettype = [("yaw", 'float64'), ("pos", 'float64', 2)]
valuetype = [("actual", "float64"), ("desired", "float64")]

motion = [("command", targettype), ("Iext", 'float64'), ("note", '|S64') ]
location = [("command", targettype), ("note", '|S64') ]

vttype = [("name",  '|S64'),
           ("valence",  valence),
           ("Iext", 'float64')]


global weights #, VT, BG, MMA,
global PC

weights = np.asarray([.5] * 4)

#VT = noisyZeros(4, vttype) # Just the representative feature of each stimulus. For eg : stim1 = ("food" : 8, "water" : 1)

#MMA = noisyZeros(4, motion) # The motor command that will lead to respective stimulus in VT. For eg : mot1 = {"yaw" : 45, move : 1, "expected" : (x,y)}

PC = (0,0) # gives current location - (x,y)

class VisualCortex(object) :
    def __init__(self, MC, PPC, ACC, SC):
        self.pop = np.zeros(4, vttype)
        self.MC = MC
        self.PPC = PPC
        self.ACC = ACC
        self.SC = SC
        self.begin = False
        self.BGOverride = False
        self._plotCount = 0
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)
        self.value_estimate = noisyZeros(1, valuetype)
        self.targetactive = False

    def resetValues(self) :
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)
        self.value_estimate = noisyZeros(1, valuetype)

    def process(self, moment) :
        myLoc = moment['state']['location']['position']
        myDir = moment['state']['location']['orientation']
        self.PPC.x, self.PPC.y, self.PPC.z = myLoc["x"], myLoc["y"], myLoc["z"]
        self.PPC.pos = np.array([myLoc["x"], myLoc["z"]])
        self.PPC.yaw = myDir["yaw"]
        myX, myZ = myLoc["x"], myLoc["z"]
        obX , obZ, obYaws, obName = [], [], [], []
        self.resetValues()
        for it in moment['observation']['viscinity'] :
            obX.append(it["x"])
            obZ.append(it["z"])
            obName.append(it["name"])

        i = 0
        MMA = self.PPC.pop
        self.ACC.hunger_values[:] = .1 + getNoise()
        self.ACC.thirst_values[:] = .1 + getNoise()
        seeitems = []
        for re in moment['observation']['reach'] :
            self.values["actual"][POPULATIONS[re["name"]]] = 1 + getNoise()
            self.ACC.hunger_values[POPULATIONS[re["name"]]] = FOOD_VALUES[re["name"]]
            self.ACC.thirst_values[POPULATIONS[re["name"]]] = WATER_VALUES[re["name"]]
        for se in moment['observation']['see'] :
            VT = self.pop
            VT[i]["name"] = str(se["name"])
            VT[i]["valence"]["food"] = FOOD_VALUES[se["name"]]
            VT[i]["valence"]["water"] = WATER_VALUES[se["name"]]
            self.values["actual"][POPULATIONS[se["name"]]] = .75 + getNoise()
            self.ACC.hunger_values[POPULATIONS[se["name"]]] = FOOD_VALUES[se["name"]]
            self.ACC.thirst_values[POPULATIONS[se["name"]]] = WATER_VALUES[se["name"]]
            seeitems.append(se["name"])
        print 'see items' , seeitems
        appearitems = []
        for it in moment['observation']['appear'] :
            '''
            1) Activate actual of visual - only for mean postion, but a little for actual item positions
            2) Update SC with yaw details (especially for estimate position)
            3) Update PPC with position details (especially for estimate position)
            4) Should not be able to obtain appetetiveness details yet.
            '''
            self.values["actual"][POPULATIONS[it["name"]]] = .25 + getNoise()
            self.SC.pop["command"]["yaw"] = it["yaw"] # Technically, not for direct use.
            self.PPC.pop["command"]["pos"] =  np.array([it["x"], it["z"]])
            #self.ACC.hunger_values[POPULATIONS[it["name"]]] = FOOD_VALUES[it["name"]]
            #self.ACC.thirst_values[POPULATIONS[it["name"]]] = WATER_VALUES[it["name"]]
            obX.append(it["x"])
            obZ.append(it["z"])
            obName.append(it["name"])
            obYaws.append(it["yaw"])
            #MMA["command"][i]["yaw"] = it["yaw"]
            #MMA["command"][i]["pos"] = np.array([it["x"], it["z"]])
            appearitems.append([it["x"], it["z"]])
        if len(appearitems) > 0 :
            if not self.targetactive :
                self.targetactive = True
                return 0
            else :
                k = np.argmax(self.values["actual"])
                if np.argmax(self.PPC.values_move[:]["desired"] < .25) : self.PPC.values_move[k]["desired"] = .75
                if np.argmax(self.ACC.insula_a.values[:]["desired"]) < .25 : self.ACC.insula_a.values[k]["desired"] = .75
                print 'appear items ', appearitems
                meanpoint = np.mean(appearitems, axis=0)
                meanyaw = getYawDelta(meanpoint[0], meanpoint[1], myLoc["x"], myLoc["z"], myDir["yaw"])
                self.value_estimate["actual"][0] = .75 + getNoise()
                self.SC.pop_estimate[0]["command"]["yaw"] = meanyaw
                self.PPC.pop_estimate[0]["command"]["pos"] = meanpoint
                self.SC.estimate_turn["actual"] = .75 + getNoise()
                self.PPC.estimate_move["actual"] = .75 + getNoise()
                print 'Mean : ' , meanpoint, ' target yaw : ', self.PPC.targetYaw, 'my yaw : ' , self.PPC.yaw
                #plotItems(myX, myZ, obX, obZ, obYaws, self._plotCount, 111)
                return 1
'''
The Sensory dudes - in alphabetical order.
Just kidding : in the order of location, need and preference
'''

class SuperiorColliculus(object) :
    '''
    SC
    '''
    def __init__(self):
        self.x, self.y, self.z = 0. ,0. ,0.
        self.pos = np.array([self.x, self.z])
        self.yaw = 0.
        self.targetPos = np.array([None, None]) # Only (x, z)
        self.targetYaw = None
        '''
        To start with, values (desired & actual), one for each of the possible positions
        prefixed for the stimuli.
        '''
        self.pop = np.zeros(MAXIMUM_POSITIONS, location)
        self.values_turn = noisyZeros(MAXIMUM_POSITIONS, valuetype)
        self.pop_estimate = np.zeros(1, location)
        self.estimate_turn = noisyZeros(1, valuetype)

    def isTurningEstimateOn(self) :
        return np.max(self.estimate_turn[:]["Iext"]) > .25

    def activateEstimateTurn(self, targetYaw=0) :
        self.resetValues()
        self.estimate_turn[0]["Iext"] = .75
        self.estimate_turn[0]["note"] = "setYaw " + str(targetYaw) + ";"

    def resetValues(self) :
        print 'Resetting values'
        self.values[:]["Iext"] = .1 + getNoise()
        self.value_estimate[:]["Iext"] = .1 + getNoise()


class PrimarySomatoSensoryCortex(object) :
    '''
    Class:PPC
    '''
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
        self.pop = np.zeros(MAXIMUM_POSITIONS, location)
        self.values_move = noisyZeros(MAXIMUM_POSITIONS, valuetype)
        self.pop_estimate = np.zeros(1, location)
        self.estimate_move = noisyZeros(1, valuetype)


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

    def check(self) :
        print 'PPC diff des and act : ', np.concatenate([self.values_move["desired"], self.estimate_move["desired"]]) - np.concatenate([self.values_move["actual"], self.estimate_move["actual"]])

    def continueTurn(self) :
        return (np.abs(self.yaw - self.targetYaw) > 1.5)

    def update(self) :
        self.targetOn = self.moving or self.turning or self.waiting

    def status(self) :
        print 'target', self.targetOn, 'moving', self.moving, 'waiting ', self.waiting, 'turning ', self.turning


    def activateTurn(self, targetYaw=0) :
        self.resetValues()
        self.values_turn[0]["Iext"] = .75
        self.values_turn[0]["note"] = "setYaw " + str(targetYaw) + ";"

    def activateEstimateMove(self, target = []) :
        self.resetValues()
        self.estimate_move[0]["Iext"] = .75
        if target != [] :
            self.estimate_move[0]["note"] = "tpx " + target[0] + "; tpz "+ target[1] +";"

    def resetValues(self) :
        print 'Resetting values'
        self.values[:]["Iext"] = .1 + getNoise()
        self.value_estimate[:]["Iext"] = .1 + getNoise()

class Insula_A(object):
    def __init__(self, hunger=0, thirst=0, energy=100):
        self.hunger = hunger
        self.thirst = thirst
        self.energy = energy
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)

    def timeEffect(self) :
        self.hunger += .6
        self.thirst += .8
        self.energy -= .75

    def moveEffect(self) :
        self.hunger += 1
        self.thirst += 2
        self.energy -= 1.5

    def status(self) :
        print 'Hunger : %4.2f, Thirst : %4.2f, Energy : %4.2f' % (self.hunger, self.thirst, self.energy)

    def resetValues(self) :
        print '[RESET] : Insula_A'
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)


class Insula_O(object):
    def __init__(self):
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)


'''
The Frontal dudes - no kidding, in the order of location (where and how), need and preference
'''

class FrontalEyeFields(object) :
    def __init__(self):
        self.pop = np.zeros(MAXIMUM_POSITIONS, motion)
        self.values = np.zeros(MAXIMUM_POSITIONS, motion)
        self.value_estimate = np.zeros(1, motion)
        # Some global flags : let's see how feasible it is to have these
        self.turning = False

    def resetValues(self) :
        print 'Resetting values'
        self.values[:]["Iext"] = .1 + getNoise()
        self.value_estimate[:]["Iext"] = .1 + getNoise()

class MotorCortex(object) :
    def __init__(self, PPC):
        self.pop = np.zeros(MAXIMUM_POSITIONS, motion)
        self.values = np.zeros(MAXIMUM_POSITIONS, motion)
        self.value_estimate = np.zeros(1, motion)
        # Some global flags : let's see how feasible it is to have these
        self.moving = False
        self.PPC = PPC

    def process(self, agent_host) :
        agent_host.sendChat('In Motor')

    def resetValues(self) :
        print 'Resetting values'
        self.values[:]["Iext"] = .1 + getNoise()
        self.value_estimate[:]["Iext"] = .1 + getNoise()


class AnteriorCingulateCortex(object) :

    '''
        Refer the hunger and thirst values from Insula 1
        Learn the expense rate as per movement and time
        Estimate for each stimulus, the rough cost of action
    '''
    def __init__(self, insula_a):
        self.insula_a = insula_a
        self.hunger_values = noisyZeros(MAXIMUM_STIMULI)
        self.thirst_values = noisyZeros(MAXIMUM_STIMULI)

    def getCurrentHunger(self) :
        return self.insula_a.hunger

    def getCurrentThirst(self) :
        return self.insula_a.thirst

    def check(self) :
        self.insula_a.resetValues()
        if self.getCurrentThirst() > THIRST_LIMIT :
            for item in THIRST_ITEMS :
                self.insula_a.values["desired"][POPULATIONS[item]] = .5
        if self.getCurrentHunger() > HUNGER_LIMIT :
            for item in HUNGER_ITEMS :
                self.insula_a.values["desired"][POPULATIONS[item]] = .5
        self.insula_a.values["desired"] = self.insula_a.values["desired"] + getNoise(self.insula_a.values["desired"].size)


    def status(self) :
        print 'From ACC : Hunger : %4.2f, Thirst : %4.2f' % (self.insula_a.hunger, self.insula_a.thirst)


class OrbitoFrontalCortex(object) :
    '''
    Receives partially observable state information about stimuli from
    extra cortical structures. Receives food and thirst relevance values of each stimulus
    from Insula_O
    '''

    def __init__(self, insula_o) :
        self.insula_o = insula_o
        self.pref_values = noisyZeros(MAXIMUM_STIMULI)

'''
And, in the guest appearance : The Basal Ganglia - details awaited!
'''

class AbstractBasalGanglia(object) :
    def __init__ (self, name, strategy=lambda x : np.argmax(x)) :
        self.name = name
        self.strategy = strategy # Selection strategy - could be choose the maximum or some other

    def select(self, source, target) :
        target[self.strategy(source)] = 1


class BasalGanglia(object) :
    def __init__(self):
        self.pop = noisyZeros(4)
        self.begin = False
        self._plotCount = 0
        self.msg = ""
    def process(self, moment, VC, PPC, MC, ACC) :
        PPC.checks()
#                if grantedState == "DECIDE" : self.decide(VC, PPC, MC, ACC)

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

class ACCVAConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #ACC
        self.target = target #VA
        self.weights= weights

    def propagate(self) :
        print 'Propogating'
        '''
        VA updating ACC
        Insula_a actual updating ACC
        ACC deciding (it could be either among stimuli or just w/o stimuli)
        ACC updates VA
        ACC updates Insula_a desired
        '''
        #self.source.insula_a.values["desired"][:] = 0
        ACC = self.source
        VA = self.target
        need = False
        # VA updating ACC
        VAPop = self.target.pop
        for it in VAPop :
            if it["name"] != '' :
                print 'setting acc values'
                ACC.hunger_values[POPULATIONS[it["name"]]] = it["valence"]["food"]
                ACC.thirst_values[POPULATIONS[it["name"]]] = it["valence"]["water"]
        ACC.hunger_values[:] = normalize(ACC.hunger_values, 10)
        ACC.thirst_values[:] = normalize(ACC.thirst_values, 10)
        print 'after acc', ACC.hunger_values, ACC.thirst_values

        ACC.insula_a.resetValues()
        #Insula_a actual updating ACC
        if ACC.getCurrentThirst() > THIRST_LIMIT :
            for item in THIRST_ITEMS :
                ACC.insula_a.values["desired"][POPULATIONS[item]] = .5
                VA.values["desired"][POPULATIONS[item]] = .5
        if ACC.getCurrentHunger() > HUNGER_LIMIT :
            for item in HUNGER_ITEMS :
                ACC.insula_a.values["desired"][POPULATIONS[item]] = .5
                VA.values["desired"][POPULATIONS[item]] = .5
        ACC.insula_a.values["desired"][:] =  ACC.insula_a.values["desired"][:] + getNoise(ACC.insula_a.values["desired"].size)
        VA.values["desired"][:] =  VA.values["desired"][:] + getNoise(VA.values["desired"].size)
        # This is not urgent need, but just a motivation to explore
        need = (ACC.getCurrentThirst() + ACC.getCurrentHunger() > 0)
        print 'checking need : ', need, ' and VA actual values : ', VA.values["actual"]
        if need and np.max(VA.values["actual"]) < .5 :
            print 'There is a current need, activating estimates '
            VA.value_estimate[0]["desired"] = .5 + getNoise()


class MCVAConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #MC
        self.target = target #VA
        self.weights= weights

    def propagate(self) :
        '''
        If something in visual (desired) is active, makes motor active
        '''
        VA = self.target
        PPC = self.source.PPC
        self.source.values["Iext"][:] = VA.values["actual"][:]
        self.source.value_estimate["Iext"][:] = VA.value_estimate["desired"][:]
        PPC.values_move["desired"][:] = self.source.values["Iext"][:]
        PPC.estimate_move["desired"][:] = self.source.value_estimate["Iext"][:]
        if PPC.estimate_move["actual"][0] > .25 :
            PPC.estimate_move["desired"][:] = 0 + getNoise()
            VA.value_estimate["desired"][:] = 0 + getNoise()


def normalize(values, maximum) :
    a = [-1, 1, -1, 1]
    np.random.shuffle(a)
    values = (values/(maximum * 1.)) + (a * getNoise(values.size))
    return values

class MCPPCConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #MC
        self.target = target #PPC
        self.weights= weights

    def check(self) :
        print 'propagate MC to PPC'

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
"REACH" : {"next" : "CONSUME", "frere" : "CONSUME", "fils" : "", "act" : "move .5; PPCWait 1; move 0", "ens" : [5, 13], "OFF" : "ORIENT,LOCATE", "color" :  "g", "msg" : "I will appraoch this object"},
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
