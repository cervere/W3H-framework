import MalmoPython
import os
import random
import sys
import time
import json
import random
import errno
import numpy as np
import copy
from pprint import pprint
from collections import namedtuple
from methods import *
from xmlutils import GetMissionXML, GetItemDrawingXML
from constants import *
from motorloopupdatenew import *
#### Grid data goes to context
#### ObservationsFromNearby goes to cues / items with locations
import matplotlib.backends.backend_pdf

EntityInfo = namedtuple('EntityInfo', 'x, y, z, name, quantity, yaw, pitch, life')
EntityInfo.__new__.__defaults__ = (0, 0, 0, "", 1)



def SendCommand(command):
    agent_host.sendCommand(command)

def SendChat(msg):
    agent_host.sendCommand( "chat " + msg )

def SetVelocity(vel):
    agent_host.sendCommand( "move " + str(vel) )

def SetTurn(turn):
    agent_host.sendCommand( "turn " + str(turn) )

recordingsDirectory="EatingRecordings"
try:
    os.makedirs(recordingsDirectory)
except OSError as exception:
    if exception.errno != errno.EEXIST: # ignore error if already existed
        raise

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

validate = True
# Create a pool of Minecraft Mod clients.
# By default, mods will choose consecutive mission control ports, starting at 10000,
# so running four mods locally should produce the following pool by default (assuming nothing else
# is using these ports):
my_client_pool = MalmoPython.ClientPool()
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10000))
#my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10001))
#my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10002))
#my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10003))

agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print 'ERROR:',e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)

if True or agent_host.receivedArgument("test"):
    num_reps = 1
else:
    num_reps = 30000

with open('moment.json') as fp:
    base_moment = json.load(fp)

itemdrawingxml = GetItemDrawingXML(testing=True)

with open('moments.json', 'w') as mm:
    mm.write('Starting')

for iRepeat in range(num_reps):
    my_mission = MalmoPython.MissionSpec(GetMissionXML("Explore the world" , itemdrawingxml),validate)
    # Set up a recording
    my_mission_record = MalmoPython.MissionRecordSpec(recordingsDirectory + "//" + "Mission_" + str(iRepeat) + ".tgz")
    my_mission_record.recordRewards()
    my_mission_record.recordMP4(24,400000)
    max_retries = 3
    for retry in range(max_retries):
        try:
            # Attempt to start the mission:
            agent_host.startMission( my_mission, my_client_pool, my_mission_record, 0, "itemTestExperiment" )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print "Error starting mission",e
                print "Is the game running?"
                exit(1)
            else:
                time.sleep(2)

    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        time.sleep(0.1)
        world_state = agent_host.getWorldState()

    reward = 0.0    # keep track of reward for this mission.
    waitCycles = 0
    currentSequence = "move 0;"
    observations = {"data" : []}
    all_moments = {"data" : []}
    turnUntil, moveUntil = False, False
    INS_A = Insula_A()
    ACC = AnteriorCingulateCortex(INS_A)
    BG = BasalGanglia()
    PPC = PrimarySomatoSensoryCortex()
    SC = SuperiorColliculus()
    FEF = FrontalEyeFields()
    MC = MotorCortex(PPC)
    DLS = AbstractBasalGanglia("DLS")
    VC = VisualCortex(MC, PPC, ACC, SC)
    eatact = []
    INS_A_DESIRED = []
    INS_A_ACTUAL = []
    SC_DESIRED = []
    SC_ACTUAL = []
    TURN_ESTIMATE_VALUES = {"desired" : [], "actual" : []}
    PPC_DESIRED = []
    PPC_ACTUAL = []
    MOVE_ESTIMATE_VALUES = {"desired" : [], "actual" : []}
    VA_DESIRED = []
    VA_ESTIMATE = {"desired" : [], "actual" : []}
    VA_DESIRED_TIMES = []
    MOTOR_VALUES = []
    MOTOR_ESTIMATE_VALUES = []
    HUNGER_VALUES = []
    THIRST_VALUES = []
    ACC_HUNGER_VALUES = []
    ACC_THIRST_VALUES = []
    VA_ACTUAL = []
    STATE_CHANGE_TIMES = []
    STATE_CHANGE_STATE = []
    traces_x, traces_z = [], []
    checkTimes = [25, 50, 75]
    checking = 0
    prevSeq = ''
    note = ''
    ACCtoVA = ACCVAConnection(ACC, VC)
    MCtoVA = MCVAConnection(MC, VC)
    movingOn, turningOn = False, False
    movenote, turnnote = '', ''
    np.random.shuffle(RANDOM_NOISE)
    while world_state.is_mission_running:
        world_state = agent_host.getWorldState()
        if world_state.number_of_observations_since_last_state > 0:
            #print "in the beginning ", MC.state, 'target', PPC.targetOn, 'moving', PPC.moving, 'waiting ', PPC.waiting, 'turning ', PPC.turning
            '''
             Observe(Environment)
                * Internal
                    * Hunger, Thirst, Well-being - (Get this from Insula_A)
                * External
                    * Appear, See, Reach zones
            '''
            msg = world_state.observations[-1].text
            ob = json.loads(msg)
            observations["data"].append(ob)
            moment = copy.copy(base_moment)
            prepareMoment(moment, ob)
            traces_x.append(moment['state']["location"]["position"]["x"])
            traces_z.append(moment['state']["location"]["position"]["z"])
            with open('moments.json', 'a') as mm:
                pprint(moment, stream=mm)
            if moment['globalTime'] % 10 == 0 :
                INS_A.timeEffect()
                #INS_A.status()
                #ACC.status()
                ACC.check()
            if VC.process(moment) < 1 :
                print 'Stopping immediately : visual returned zero'
                SetVelocity(0)
                PPC.moving = False
            ACCtoVA.propagate()
            MCtoVA.propagate()
            '''
             Perceive(Observations)
                * Internal
                    * Search with a goal / Explore randomly
                * External
                    * What is it?
                    * Where is it? If it is in :
                         - Appear : access only location, not values^, move towards the C.O.G of all the objects
                         - See : access location, estimate values and the desiredness
                         - Reach : Verify if it is the one of interest.
                         ^ - Later with context, appear also could give some value.
                    * "estimate values" - What values does it change?
                    * "desiredness"- Do I need/want that change?
             Act(Observations, Perception)
                * Search (MOVE with random exploration, no location target but some desired value)
                    * Involves just turn to look for things which "appeared" but not anymore in "see" zone
                * Reach (MOVE towards a particular target, because it is decided to be interesting in the previous moment)
                    * Involves orienting, turning, moving towards.
                * Consume - If the interest is still ON, consume, update the respective values^^.
                    ^^ - Later the consumption could be gradual over time, instead of an instantaneous update.

            '''
            #BG.process(moment, VC, PPC, MC,ACC)
            if BG.msg != "" :
                SendChat(BG.msg)
                BG.msg = ""
            #MC.process(agent_host)
            if False and (not PPC.targetOn or VC.BGOverride) :
                if MC.nextAction != "" :
                    if currentSequence != "" : currentSequence += '; ' + MC.nextAction
                    else : currentSequence = MC.nextAction
            VA_DESIRED_TIMES.append(moment['globalTime'])
            VA_DESIRED.append(np.array(VC.values["desired"]))
            VA_ESTIMATE["desired"].append(np.array(VC.value_estimate["desired"]))
            VA_ESTIMATE["actual"].append(np.array(VC.value_estimate["actual"]))
            VA_ACTUAL.append(np.array(VC.values["actual"]))
            INS_A_DESIRED.append(np.array(INS_A.values["desired"]))
            INS_A_ACTUAL.append(np.array(INS_A.values["actual"]))
            SC_DESIRED.append(np.array(SC.values_turn["desired"]))
            SC_ACTUAL.append(np.array(SC.values_turn["actual"]))
            TURN_ESTIMATE_VALUES["desired"].append(np.array(SC.estimate_turn["desired"]))
            TURN_ESTIMATE_VALUES["actual"].append(np.array(SC.estimate_turn["actual"]))
            PPC_DESIRED.append(np.array(PPC.values_move["desired"]))
            PPC_ACTUAL.append(np.array(PPC.values_move["actual"]))
            MOVE_ESTIMATE_VALUES["desired"].append(np.array(PPC.estimate_move["desired"]))
            MOVE_ESTIMATE_VALUES["actual"].append(np.array(PPC.estimate_move["actual"]))
            MOTOR_VALUES.append(np.array(MC.values["Iext"]))
            MOTOR_ESTIMATE_VALUES.append(np.array(MC.value_estimate["Iext"]))
            HUNGER_VALUES.append(ACC.getCurrentHunger())
            THIRST_VALUES.append(ACC.getCurrentThirst())
            ACC_HUNGER_VALUES.append(np.array(ACC.hunger_values))
            ACC_THIRST_VALUES.append(np.array(ACC.thirst_values))


            '''
            ACT
            '''
            ACC.status()
            if moment['globalTime'] > 225 :
                MC.resetValues()
            elif False : #moment['globalTime'] > 50 :
                MC.estimate_turn[0]["Iext"] = .1
                MC.estimate_move[0]["Iext"] = .75
                MC.estimate_move[0]["note"] = "tpx .25; tpz 35;"
                MC.values_turn[:]["Iext"] = .1
                MC.values_move[:]["Iext"] = .1


            '''
            Decide Action
            '''
            motor_pop = np.concatenate([FEF.values["Iext"], FEF.value_estimate["Iext"]])
            winning_motor = np.argmax(motor_pop)
            print 'time ', moment['globalTime']
            if True : #not PPC.moving :
                if motor_pop[winning_motor] > 0.25 :
                    if winning_motor > FEF.values.size - 1 :
                        turnnote = FEF.value_estimate[winning_motor - FEF.values.size]["note"]
                    else :
                        turnnote = FEF.values[winning_motor]["note"]
                    if turnnote != "" and turnnote.split(" ")[1].split(";")[0] > 0 :
                        print 'turnnote ', turnnote
                        turnSpeed = 0.2
                    else :
                        turnSpeed = -0.2
                    currentSequence = "turn " + str(turnSpeed) + ";"
                    turningOn = True
                elif turningOn :
                    currentSequence = "turn 0;" + turnnote
                    turningOn = False
                    turnnote = ''
            print 'com : ', turnnote
            motor_pop_move = np.concatenate([MC.values["Iext"], MC.value_estimate["Iext"]])
            winning_motor = np.argmax(motor_pop_move)
            if True : #not turningOn :
                if motor_pop_move[winning_motor] > 0.25 :
                    if winning_motor > MC.values.size - 1 :
                        movenote = MC.value_estimate[winning_motor - MC.values.size]["note"]
                    else :
                        movenote = MC.values[winning_motor]["note"]
                    print 'Some move active', movenote
                    currentSequence += "move .6; "
                    PPC.moving = True
                else :
                    currentSequence += "move 0;" + movenote
                    PPC.moving = False
                    movenote = ''
            #currentSequence = prevSeq + currentSequence


        '''
        The internal reward processing can be handled later.
        At this moment, rewards (or changes because of consumption) are handled explicitly
        if world_state.number_of_rewards_since_last_state > 0:
            # A reward signal has come in - see what it is:
            delta = world_state.rewards[0].getValue()
            energy += delta
        '''

        if PPC.waitCount > 0 : PPC.waitCount -= 1
        #if not PPC.waitSignal and PPC.waitCount == 0:
            #PPC.waiting = False
            # Time to execute the next command, if we have one:
        if PPC.waitCount == 0 and currentSequence != "":
            print 'executing ', currentSequence
            commands = currentSequence.split(";", 1)
            command = commands[0].strip()
            if len(commands) > 1:
                currentSequence = commands[1]
            else:
                currentSequence = ""
            verb,sep,param = command.partition(" ")
            if verb == "wait":
                PPC.waitCount = int(param.strip())
                PPC.waiting = True
            elif verb == "PPCWait":
                PPC.waitSignal = True
            else:
                agent_host.sendCommand(command) # Send the command to Minecraft.

        PPC.update()
        if PPC.moving : INS_A.moveEffect()
        if VC.BGOverride : VC.BGOverride = False
        eatactens = actionMap["LOCATE"]["ens"]
        time.sleep(0.1)


    with open('observations.json', 'w') as fp:
        pprint(observations, stream=fp)
    # mission has ended.
    print "Mission " + str(iRepeat+1) + ": Reward = " + str(reward)
    for error in world_state.errors:
        print "Error:",error.text
    time.sleep(0.5) # Give the mod a little time to prepare for the next mission.

    VC._plotCount += 1
    VC_DESIRED_PLOT = np.asarray(VA_DESIRED)
    VC_ACTUAL_PLOT = np.asarray(VA_ACTUAL)
    INS_A_DESIRED_PLOT = np.asarray(INS_A_DESIRED)
    INS_A_ACTUAL_PLOT = np.asarray(INS_A_ACTUAL)
    SC_DESIRED_PLOT = np.asarray(SC_DESIRED)
    SC_ACTUAL_PLOT = np.asarray(SC_ACTUAL)
    PPC_DESIRED_PLOT = np.asarray(PPC_DESIRED)
    PPC_ACTUAL_PLOT = np.asarray(PPC_ACTUAL)
    ACC_HUNGER_PLOT = np.asarray(ACC_HUNGER_VALUES)
    ACC_THIRST_PLOT = np.asarray(ACC_THIRST_VALUES)
    MOTOR_VALUES_PLOT = np.asarray(MOTOR_VALUES)

    genericPlot(VA_DESIRED_TIMES, VC_DESIRED_PLOT, VC_ACTUAL_PLOT, 'Visual Areas', VA_ESTIMATE)
    genericPlot(VA_DESIRED_TIMES, SC_DESIRED_PLOT, SC_ACTUAL_PLOT, 'Superior Colliculus(SC)', TURN_ESTIMATE_VALUES)
    genericPlot(VA_DESIRED_TIMES, PPC_DESIRED_PLOT, PPC_ACTUAL_PLOT, 'PrimarySomatoSensoryCortex (PPC)', MOVE_ESTIMATE_VALUES)
    genericPlot(VA_DESIRED_TIMES, INS_A_DESIRED_PLOT, INS_A_ACTUAL_PLOT, 'Insular Cortex(-ACC)')
    genericPlot(VA_DESIRED_TIMES, ACC_HUNGER_PLOT, ACC_THIRST_PLOT, 'ACC')

    plotPath(traces_x, traces_z)

    fig = plt.figure()
    fig.suptitle('Hunger and Thirst', fontsize=20)
    ax = fig.add_subplot(111)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Units')
    #ax.set_ylim(ymin=0, ymax=1.2)
    ax.plot(VA_DESIRED_TIMES, HUNGER_VALUES, label='hunger')
    ax.plot(VA_DESIRED_TIMES, THIRST_VALUES, label='thirst')
    ax.legend(loc='center left',fontsize="x-small", bbox_to_anchor=(1, 0.5))

    FRONTALVALUES = []
    FRONTALVALUES.append(MOTOR_VALUES_PLOT)
    genericFrontalPlot(VA_DESIRED_TIMES, ['Motor', 'ACC', 'OFC'], FRONTALVALUES, 'Frontal', MOTOR_ESTIMATE_VALUES)


    #plt.show()

    pdf = matplotlib.backends.backend_pdf.PdfPages("output.pdf")
    for fig in xrange(1, plt.figure().number): ## will open an empty extra figure :(
        pdf.savefig( fig )
    pdf.close()
