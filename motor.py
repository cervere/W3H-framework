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
from methods import prepareMoment
from xmlutils import GetMissionXML, GetItemDrawingXML
from constants import *
from motorloop import *

#### Grid data goes to context
#### ObservationsFromNearby goes to cues / items with locations


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

global moving

moving = True

jumping = False
itemdrawingxml = GetItemDrawingXML(testing=True)

def printLevels(hunger, thirst, energy) :
    return "Hunger ("+ str(hunger) +"); Thirst ("+ str(thirst) +"); Energy ("+ str(energy) +")"

global Insula_hunger, Insula_thirst, Insula_energy

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
    currentSequence = "move 1;"
    observations = {"data" : []}
    while world_state.is_mission_running:
        updateInsulaWithTime()
        world_state = agent_host.getWorldState()
        if world_state.number_of_observations_since_last_state > 0:
            '''
             Roughly, at each time instance, the following sequence can be observed :
             Observe(Environment)
                * Internal
                    * Hunger, Thirst, Well-being - (Get this from Insula)
            '''
            SendChat('My current levels are : ' + printLevels(Insula_hunger,Insula_thirst, Insula_energy))
            '''
                * External
                    * Appear, See, Reach zones
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
            if waitCycles > 0: waitCycles -= 1
            msg = world_state.observations[-1].text
            ob = json.loads(msg)
            # Use prepareMoment - observations
            reach = np.asarray(ob.get(u'reach', 0))
            see = np.asarray(ob.get(u'see', 0))
            appear = np.asarray(ob.get(u'appear', 0))

            moment = copy.copy(base_moment)
            prepareMoment(moment, ob)
            #print "Obs : " + str(ob.get(u'far_entities', []))
            # For some debugging
            if moving and len(moment['observation']['appear']) > 0 : #The agent name is excluded already in preparing the moment
                observations["data"].append(ob)
                #pprint(moment)
                SendCommand("move 0")
                moving = False
                SendChat('Few options appear. Will evaluate using motor loop!')
                i = 0
                for it in moment['observation']['appear'] :
                    print it["x"], it["y"], it["z"], it["yaw"], it["name"]
                    VT[i]["name"] = str(it["name"])
                    VT[i]["valence"]["food"] = FOOD_VALUES[it["name"]]
                    VT[i]["valence"]["water"] = WATER_VALUES[it["name"]]
                    VT[i]["Iext"] = 1.
                    MMA["command"][i] = "setYaw " + str(it["yaw"]) + "; move 1; wait 3; tpx " + str(it["x"]) + "; "
                    i += 1

                propagate()

                k = np.argmax(MMA["Iext"])

                SendChat(MMA[np.argmax(MMA["Iext"])]["command"])
                currentSequence = MMA[np.argmax(MMA["Iext"])]["command"] + " move 0; wait 5; tpx 0.5; setYaw 0; wait 5; move 1;"
                #SendCommand(MMA[np.argmax(MMA["Iext"])]["command"])
                #SendCommand("move 1")

        '''
        The internal reward processing can be handled later.
        At this moment, rewards (or changes because of consumption) are handled explicitly
        if world_state.number_of_rewards_since_last_state > 0:
            # A reward signal has come in - see what it is:
            delta = world_state.rewards[0].getValue()
            energy += delta
        '''
        if waitCycles == 0:
        # Time to execute the next command, if we have one:
            if currentSequence != "":
                commands = currentSequence.split(";", 1)
                command = commands[0].strip()
                if len(commands) > 1:
                    currentSequence = commands[1]
                else:
                    currentSequence = ""
                verb,sep,param = command.partition(" ")
                if verb == "wait":
                    waitCycles = int(param.strip())
                else:
                    agent_host.sendCommand(command) # Send the command to Minecraft.
                    if command == 'move 1' :
                        print "changing moving"
                        moving = True

        time.sleep(0.1)
    with open('observations.json', 'w') as fp:
        json.dump(observations, fp)
    # mission has ended.
    print "Mission " + str(iRepeat+1) + ": Reward = " + str(reward)
    for error in world_state.errors:
        print "Error:",error.text
    time.sleep(0.5) # Give the mod a little time to prepare for the next mission.
