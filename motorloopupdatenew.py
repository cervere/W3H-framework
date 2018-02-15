import random
from methods import *

valence = [("food",  'float64'),
           ("water", 'float64')]

targettype = [("yaw", 'float64'), ("pos", 'float64', 2), ("dist", 'float64')]
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
    def __init__(self, FEF, MC, ACC):
        self.pop = np.zeros(4, vttype)
        self.FEF = FEF
        self.MC = MC
        self.ACC = ACC
        self.SC = self.FEF.SC
        self.PPC = self.MC.PPC
        self.insula_a = self.ACC.insula_a
        self.begin = False
        self.BGOverride = False
        self._plotCount = 0
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)
        self.value_estimate = noisyZeros(1, valuetype)
        self.gatheringAppearInfo = 3
        self.gatheringSeeInfo = 3

    def resetValues(self) :
        self.values = noisyZeros(MAXIMUM_STIMULI, valuetype)
        self.value_estimate = noisyZeros(1, valuetype)

    def process(self, moment) :
        '''
        VCProcess
        '''
        myLoc = moment['state']['location']['position']
        myDir = moment['state']['location']['orientation']
        self.PPC.x, self.PPC.y, self.PPC.z = myLoc["x"], myLoc["y"], myLoc["z"]
        self.PPC.pos = np.array([myLoc["x"], myLoc["z"]])
        self.SC.yaw = myDir["yaw"]
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
        reachitems, seeitems, appearitems = [], [], []

        for re in moment['observation']['reach'] :
            self.values["actual"][POPULATIONS[re["name"]]] = 1 + getNoise()
            self.ACC.hunger_values[POPULATIONS[re["name"]]] = FOOD_VALUES[re["name"]]
            self.ACC.thirst_values[POPULATIONS[re["name"]]] = WATER_VALUES[re["name"]]
            reachitems.append(re["name"])
        print 'reach items' , reachitems

        minseedist = 0
        maxseedist = 0
        for se in moment['observation']['see'] :
            VT = self.pop
            VT[i]["name"] = str(se["name"])
            VT[i]["valence"]["food"] = FOOD_VALUES[se["name"]]
            VT[i]["valence"]["water"] = WATER_VALUES[se["name"]]
            self.values["actual"][POPULATIONS[se["name"]]] = .75 + getNoise()
            self.SC.pop[POPULATIONS[se["name"]]]["command"]["yaw"] = se["yaw"] # Technically, not for direct use.
            self.PPC.pop[POPULATIONS[se["name"]]]["command"]["pos"] =  np.array([se["x"], se["z"]])
            dist = euclDist(se["x"], se["z"], self.PPC.x, self.PPC.z)
            self.PPC.pop[POPULATIONS[se["name"]]]["command"]["dist"] = dist
            if minseedist == 0 or dist < minseedist :
                minseedist = dist
            if maxseedist == 0 or dist > maxseedist:
                maxseedist = dist
            self.ACC.values[POPULATIONS[se["name"]]] = .25 + getNoise()
            seeitems.append(se["name"])

        for it in moment['observation']['appear'] :
            '''
            1) Activate actual of visual - only for mean postion, but a little for actual item positions
            2) Update SC with yaw details (especially for estimate position)
            3) Update PPC with position details (especially for estimate position)
            4) Should not be able to obtain appetetiveness details yet.
            '''
            self.values["actual"][POPULATIONS[it["name"]]] = .25 + getNoise()
            self.SC.pop[POPULATIONS[it["name"]]]["command"]["yaw"] = it["yaw"] # Technically, not for direct use.
            self.PPC.pop[POPULATIONS[it["name"]]]["command"]["pos"] =  np.array([it["x"], it["z"]])
            obX.append(it["x"])
            obZ.append(it["z"])
            obName.append(it["name"])
            obYaws.append(it["yaw"])
            appearitems.append([it["x"], it["z"]])

        if len(seeitems) > 0 and not self.FEF.working :
            print 'see items' , seeitems
            print minseedist, maxseedist
            if self.gatheringSeeInfo > 0 :
                self.MC.working = False
                self.gatheringSeeInfo -= 1
            else :
                for s in seeitems :
                    factor = 1 - ((self.PPC.pop[POPULATIONS[se["name"]]]["command"]["dist"] - minseedist)/maxseedist)
                    food, water = FOOD_VALUES[se["name"]], WATER_VALUES[se["name"]]
                    if (THIRST_FATAL_LIMIT - self.insula_a.thirst) <= (HUNGER_FATAL_LIMIT - self.insula_a.hunger) :
                        self.insula_a.values["actual"][POPULATIONS[se["name"]]] += .25 * water/10
                    else :
                        self.insula_a.values["actual"][POPULATIONS[se["name"]]] += .25 * food/10

                    self.ACC.values[POPULATIONS[se["name"]]] +=  .25 * factor

        elif len(appearitems) > 0 and not self.FEF.working :
            '''
            Just to add some delay
            '''
            if self.gatheringAppearInfo > 0 :
                self.value_estimate["actual"][:] = .5 + getNoise(self.value_estimate["actual"].size)
                self.MC.working = False
                self.gatheringAppearInfo -= 1
            else :
                print 'appear items ', appearitems
                k = np.argmax(self.values["actual"])
                if np.argmax(self.PPC.values_move[:]["desired"] < .25) : self.PPC.values_move[k]["desired"] = .75
                if np.argmax(self.ACC.insula_a.values[:]["desired"]) < .25 : self.ACC.insula_a.values[k]["desired"] = .75
                meanpoint = np.mean(appearitems, axis=0)
                meanyaw = getYawDelta(meanpoint[0], meanpoint[1], myLoc["x"], myLoc["z"], myDir["yaw"])
                self.FEF.working = np.abs(self.SC.yaw - meanyaw) > 1
                self.SC.pop_estimate[0]["command"]["yaw"] = meanyaw - self.SC.yaw
                self.PPC.pop_estimate[0]["command"]["pos"] = meanpoint
                #plotItems(myX, myZ, obX, obZ, obYaws, self._plotCount, 111)

        # This is not urgent need, but just a motivation to explore
        need = (self.ACC.getCurrentThirst() + self.ACC.getCurrentHunger() > 0)
        print 'About need : ', need, self.values["actual"], self.MC.working, self.FEF.working
        if need and (np.max(self.values["actual"]) < .2 or self.MC.working or self.FEF.working) :
            self.value_estimate["desired"][:] = .5 + getNoise() #SET VC ESTIMATE DESIRED
            targetyaw = self.SC.pop_estimate[0]["command"]["yaw"]
            sourceyaw = self.SC.yaw
            if True : #np.abs(targetyaw - sourceyaw) > 1 :
                #self.FEF.values["Iext"][:] = self.values["actual"][:]
                self.FEF.value_estimate["Iext"][:] = ((targetyaw - sourceyaw)/targetyaw) * self.value_estimate["desired"][:]
                #self.SC.values_turn["desired"][:] = self.FEF.values["Iext"][:]
                self.SC.estimate_turn["desired"][:] = self.FEF.value_estimate["Iext"][:]

'''
The Sensory dudes - in the order of location, need and preference
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
        self.values_turn = noisyZeros(MAXIMUM_POSITIONS, valuetype)
        self.estimate_turn = noisyZeros(1, valuetype)


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
    def __init__(self, SC):
        self.pop = np.zeros(MAXIMUM_POSITIONS, motion)
        self.values = np.zeros(MAXIMUM_POSITIONS, motion)
        self.value_estimate = np.zeros(1, motion)
        # Some global flags : let's see how feasible it is to have these
        self.working = False
        self.SC = SC

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
        self.working = True

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
        self.pop = noisyZeros(MAXIMUM_POSITIONS, valence)
        self.values = noisyZeros(MAXIMUM_POSITIONS)
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

    def decide(self, VC, PPC, MC, ACC) :
        MMA = MC.pop
        propagate(VC.pop, self.pop, MMA)
        k = np.argmax(MMA["Iext"])
        PPC.targetYaw = MMA[k]["command"]["yaw"]
        actionMap["ORIENT"]["act"] = 'turn '+ str(float(PPC.targetYaw)/180.) + '; PPCWait 1; turn 0'
        PPC.targetPos = MMA[k]["command"]["pos"]
        PPC.targetYaw = getYawDelta(PPC.targetPos[0], PPC.targetPos[1], PPC.x, PPC.z, PPC.yaw)
        #actionMap["REACH"]["target"] = MMA[k]["command"]["pos"]

class ACCVAConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #ACC
        self.target = target #VA
        self.weights= weights

    def propagate(self) :
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
                ACC.hunger_values[POPULATIONS[it["name"]]] = it["valence"]["food"]
                ACC.thirst_values[POPULATIONS[it["name"]]] = it["valence"]["water"]
        ACC.hunger_values[:] = normalize(ACC.hunger_values, 10)
        ACC.thirst_values[:] = normalize(ACC.thirst_values, 10)
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
        print 'Check VA desired', VA.values["desired"]

class FEFVAConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #FEF
        self.target = target #VA
        self.weights= weights
        self.delay = self.setDelay()

    def setDelay(self) :
        return 3

    def propagate(self) :
        '''
        If something in visual (desired) is active, makes FEF active
        either for non-zero "actual" in Visual (stimuli directed)
        or non-zero "desired" in Visual (goal directed, exploration)
        '''

        FEF = self.source
        VA = self.target
        SC = FEF.SC

        FEF.values["Iext"][:] = VA.values["actual"][:]
        if(np.max(VA.ACC.values) > .25) :
            accImpact = VA.ACC.values / (np.max(VA.ACC.values) * 1.)
            FEF.values["Iext"][:] = FEF.values["Iext"] * accImpact

        SC.values_turn["desired"][:] = FEF.values["Iext"][:]

        if SC.pop_estimate[0]["command"]["yaw"] - SC.yaw > 1 :
            FEF.value_estimate["Iext"][:] = VA.value_estimate["desired"][:] + getNoise(VA.value_estimate["desired"].size)
        else :
            FEF.value_estimate["Iext"][:] = getNoise(FEF.value_estimate["Iext"].size)

        SC.estimate_turn["desired"][:] = FEF.value_estimate["Iext"][:]

        if np.max(FEF.value_estimate["Iext"]) < .2 and np.max(FEF.values["Iext"]) > .2:
            if self.delay > 0 :
                if np.max(FEF.values["Iext"]) < .5 :
                    SC.estimate_turn["actual"][:] = .5 + getNoise(SC.estimate_turn["actual"].size)
                if (FEF.values["Iext"] > .5).sum() == 1 :
                    print 'found one FEF'
                else :
                    print 'multiple FEF options'
                self.delay -= 1
            else :
                SC.estimate_turn["desired"][:] = getNoise()
                SC.estimate_turn["actual"][:] = getNoise()
                #VA.value_estimate["desired"][:] = getNoise()
                #VA.value_estimate["actual"][:] = getNoise()
                FEF.value_estimate["Iext"][:] = getNoise()
                FEF.working = False
                self.delay = self.setDelay()


class MCVAConnection(object) :

    def __init__(self, source, target, weights = np.ones(MAXIMUM_STIMULI)) :
        self.source = source #MC
        self.target = target #VA
        self.weights= weights
        self.delay = self.setDelay()

    def setDelay(self) :
        return 3

    def propagate(self) :
        '''
        If something in visual (desired) is active, makes motor active
        '''
        MC = self.source
        VA = self.target
        PPC = MC.PPC
        MC.values["Iext"][:] = VA.values["actual"][:]
        if(np.max(VA.ACC.values) > .25) :
            accImpact = VA.ACC.values / (np.max(VA.ACC.values) * 1.)
            MC.values["Iext"][:] = MC.values["Iext"] * accImpact

        MC.value_estimate["Iext"][:] = VA.value_estimate["desired"][:]
        PPC.values_move["desired"][:] = MC.values["Iext"][:]
        PPC.estimate_move["desired"][:] = MC.value_estimate["Iext"][:]
        if np.max(MC.value_estimate["Iext"]) < .2 and np.max(MC.values["Iext"]) > .2:
            if self.delay > 0 :
                PPC.estimate_move["actual"][:] = .5 + getNoise(PPC.estimate_move["actual"].size)
                self.delay -= 1
            else :
                PPC.estimate_move["desired"][:] = getNoise()
                PPC.estimate_move["actual"][:] = getNoise()
                VA.value_estimate["desired"][:] = getNoise()
                VA.value_estimate["actual"][:] = getNoise()
                MC.value_estimate["Iext"][:] = getNoise()
                MC.working = False
                self.delay = self.setDelay()


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
