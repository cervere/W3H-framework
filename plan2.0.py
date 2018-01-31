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
from motorloopupdate import *
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
    MC = MotorCortex()
    VC = VisualCortex(MC, PPC, ACC)
    eatact = []
    INS_A_DESIRED = []
    INS_A_DESIRED_TIMES = []
    VA_DESIRED = []
    VA_DESIRED_TIMES = []
    STATE_CHANGE_TIMES = []
    STATE_CHANGE_STATE = []
    prev = MC.state
    while world_state.is_mission_running:
        world_state = agent_host.getWorldState()
        if world_state.number_of_observations_since_last_state > 0:
            #print "in the beginning ", MC.state, 'target', PPC.targetOn, 'moving', PPC.moving, 'waiting ', PPC.waiting, 'turning ', PPC.turning
            '''
             Roughly, at each time instance, the following sequence can be observed :
             Observe, Perceive, Act
            '''
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
            if MC.state != prev :
                print 'State changed, recording time'
                STATE_CHANGE_STATE.append(MC.state)
                STATE_CHANGE_TIMES.append(moment['globalTime'])
                prev = MC.state
            with open('moments.json', 'a') as mm:
                pprint(moment, stream=mm)
            if moment['globalTime'] % 10 == 0 :
                INS_A.timeEffect()
                INS_A.status()
                ACC.status()
                ACC.randomcheck()

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
            VC.process(moment)
            BG.process(moment, VC, PPC, MC,ACC)
            if BG.msg != "" :
                SendChat(BG.msg)
                BG.msg = ""
            MC.process(agent_host)
            if not PPC.targetOn or VC.BGOverride :
                if MC.nextAction != "" :
                    if currentSequence != "" : currentSequence += '; ' + MC.nextAction
                    else : currentSequence = MC.nextAction
                    #print 'executing ', currentSequence
            VA_DESIRED.append(np.array(VC.values["actual"]))
            VA_DESIRED_TIMES.append(moment['globalTime'])
            INS_A_DESIRED.append(np.array(INS_A.values["desired"]))

        '''
        The internal reward processing can be handled later.
        At this moment, rewards (or changes because of consumption) are handled explicitly
        if world_state.number_of_rewards_since_last_state > 0:
            # A reward signal has come in - see what it is:
            delta = world_state.rewards[0].getValue()
            energy += delta
        '''

        if PPC.waitCount > 0 : PPC.waitCount -= 1
        if not PPC.waitSignal and PPC.waitCount == 0:
            PPC.waiting = False
            # Time to execute the next command, if we have one:
            if currentSequence != "":
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
                    action, flag = command.split(" ")
                    if action == 'move' : PPC.moving = float(flag) != 0
                    elif action == 'turn' :
                        print 'turning ', PPC.turning, PPC.x, PPC.z
                        PPC.turning = float(flag) != 0
        PPC.update()
        if PPC.moving : INS_A.moveEffect()
        if VC.BGOverride : VC.BGOverride = False
        eatactens = actionMap["LOCATE"]["ens"]
        print eatactens
        eatact.append(BG.MC_gates[eatactens[0], eatactens[1]])
        time.sleep(0.1)
    with open('observations.json', 'w') as fp:
        pprint(observations, stream=fp)
    # mission has ended.
    print "Mission " + str(iRepeat+1) + ": Reward = " + str(reward)
    for error in world_state.errors:
        print "Error:",error.text
    time.sleep(0.5) # Give the mod a little time to prepare for the next mission.

    VC._plotCount += 1
    fig = plt.figure(1)
    #plt.plot(np.arange(len(eatact)), eatact)
    INS_A_DESIRED_PLOT = np.asarray(INS_A_DESIRED)
    VC_DESIRED_PLOT = np.asarray(VA_DESIRED)
    ax = fig.add_subplot(211)
    xs, ys = INS_A_DESIRED_PLOT.shape
    for pop in POPULATIONS :
        ax.plot(VA_DESIRED_TIMES, INS_A_DESIRED_PLOT[:, POPULATIONS[pop]], label=pop)
    stt, sts = [], []
    curr = 0
    for i, stat in zip(STATE_CHANGE_TIMES, STATE_CHANGE_STATE) :
        if i <= xs :
            ax.axvline(i, color='r')
            if i <= curr*50 :
                stt.append(i)
                sts.append(stat)
            else :
                for j in range(curr+1, i/50+1) :
                    stt.append(j*50)
                    sts.append(str(j*50))
                curr = i/50
                stt.append(i)
                sts.append(stat)
    ax.set_xticks(stt)
    ax.set_xticklabels(sts, rotation=60)
    ax.legend()
    ax = fig.add_subplot(212)
    xs, ys = VC_DESIRED_PLOT.shape
    for pop in POPULATIONS :
        ax.plot(VA_DESIRED_TIMES, VC_DESIRED_PLOT[:, POPULATIONS[pop]], label=pop)
    ax.legend()

    #pdf = matplotlib.backends.backend_pdf.PdfPages("output.pdf")
    #for fig in xrange(1, plt.figure().number): ## will open an empty extra figure :(
    #    pdf.savefig( fig )
    #pdf.close()

    plt.show()
