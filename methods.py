import json
import numpy as np
from pprint import pprint
from sample_data import *
from constants import *
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

debug = False

REACH_SCOPE = 1
SEE_SCOPE = 3
APPEAR_SCOPE = 7
AGENT_FOV = np.pi * (2./3)


def inFOV (agent, item, fov=AGENT_FOV) :
    m = np.tan(fov/2)
    c = agent[1] - m*agent[0]
    x = (item[1] - c) / m
    return item[0] < x


def setPosition(moment, x,y,z, yaw=90, pitch=1.0) :
    ''' See moment.json for the representation of each moment in time.
    The 'state' attribute has location parameters including the 3-D coordinates
    and the yaw, pitch of the agent
    '''
    position = {"x" : x, "y" : y, "z" : z}
    orientation = {"yaw" : yaw, "pitch" : pitch}
    moment['state']['location']['position'] = position
    moment['state']['location']['orientation'] = orientation

def setContext(moment, reach, see):
    elements, repeats = np.unique(np.concatenate([reach, see]), return_counts=True)
    strengths = np.around(1.* repeats / repeats.sum(), decimals=2)
    for x, y in zip(elements, strengths) :
        moment['observation']['context'][x] = y

def getYawDelta(targetx, targetz, sourcex, sourcez, syaw) :
    dx = (targetx - sourcex)
    dz = (targetz - sourcez)
    targetYaw = (math.atan2(dz, dx) * 180.0/np.pi) - 90
    # Find shortest angular distance between the two yaws, preserving sign:
    difference = targetYaw - syaw
    while (difference < -180) :
        difference += 360
    while (difference > 180) :
        difference -= 360
        # Normalise:
    #difference /= 180.0
    return difference

def setCues(moment, x, z, far_entities):
    sx, sz = moment['state']['location']['position']['x'], moment['state']['location']['position']['z']
    syaw = moment['state']['location']['orientation']["yaw"]
    moment['observation']['reach'] = []
    moment['observation']['see'] = []
    moment['observation']['appear'] = []
    moment['observation']['viscinity'] = []


    for ent in far_entities:
        if ent["name"] == AGENT_NAME : continue
        #(For the points on the left of the agent, inFOV calculation is the same
        # by transforming the point to the right of the agent
        ex, ez = ent["x"], ent["z"]
        trans_point = [ex, ez]
        if ex > x : trans_point[0] = 2*x - ex
        ent['yaw'] = getYawDelta(ex, ez, sx, sz, syaw)
        zdist = abs(ez - z)

        if zdist <= APPEAR_SCOPE :
            #print zdist, math.radians(np.abs(ent['yaw'])), AGENT_FOV/2
            if math.radians(np.abs(ent['yaw'])) < AGENT_FOV/2 :
                if   zdist <= REACH_SCOPE : moment['observation']['reach'].append(ent)
                elif zdist <= SEE_SCOPE   : moment['observation']['see'].append(ent)
                else                      : moment['observation']['appear'].append(ent)
            else : moment['observation']['viscinity'].append(ent)



def prepareMoment(moment, ob):
    ''' Takes malmo object at each instant and forms a moment
    This might seem redundant in the beginning but later would be useful
    as better representation for the models
    '''
    moment['globalTime'] = ob.get(u'WorldTime', 0)
    x, y, z, yaw, pitch = ob.get(u'XPos', 0), ob.get(u'YPos', 0), ob.get(u'ZPos', 0), ob.get(u'Yaw', 0),ob.get(u'Pitch', 0)
    setPosition(moment, x, y, z, yaw, pitch)
    '''
    Context is considered only from 'REACH' and 'SEE' zones. And it is a weighted
    list of all the block types present in both the zones
    For e.g {"lapis_block" : 0.8, "sandstone" : 0.2}
    '''
    if "far_entities" in ob: #Make sure these keys like "far_entities" are picked from a common place even in the XML
        setContext(moment, ob.get(u'reach', []), ob.get(u'see', []))
        setCues(moment, x, z, ob.get(u'far_entities', []))

def getBlocks(info) :
    ''' Given the type of block and the set of coordinates,
    returns the part of XML with DrawBlock tags.
    Usage : getBlocks('{"lava" : ["(5,226,29)", "(5,226,39)"]}')
    '''
    xml = ''
    configurations = info["config"]
    for configuration in configurations:
            active = configuration.get("active", "True")
            if active == "False" :
                continue
            blocktype = configuration["type"]
            coords = configuration["points"]
            for point in coords:
                x,y,z = point.strip('()').split(',')
                xml += '<DrawBlock x="'+ x +'"  y="'+ y +'" z="'+ z +'" type="'+ blocktype+'" />\n'
    return str(xml)

def getItems(info) :
    ''' Given the type of item and the set of coordinates,
    returns the part of XML with DrawItem tags.
    Usage : getItems('{"apple" : ["(5,226,29)", "(5,226,39)"]}')
    '''
    xml = ''
    configurations = info["config"]
    for configuration in configurations:
            active = configuration.get("active", "True")
            if active == "False" :
                continue
            itemtype = configuration["type"]
            coords = configuration["points"]
            for point in coords:
                x,y,z = point.strip('()').split(',')
                xml += '<DrawItem x="'+ x +'"  y="'+ y +'" z="'+ z +'" type="'+ itemtype+'" />\n'
    return str(xml)

def getCuboids(info) :
    ''' Given the type of Cuboid (generally for a floor) and the set of coordinates,
    returns the part of XML with DrawCuboid tags. Here is an ugly hack!
    Ideally, JSON should not be used for order specific data. Malmo processes the list
    of Cuboids (or Blocks) in the order given to superimpose one type on another.
    To convey this order in our json config, we maintain the list of types as an array
    as shown below...
    Usage : getCuboids('{
    "config" : [
            {
                "type" : "sandstone",
                "points" : ["{(-50,226,-50):(50,226,50)}"]
            },
            {
                "type" : "lapis_block",
                "points" : [
                    "{(3,226,-50):(7,226,-40)}",
                    "{(3,226,-30):(7,226,-20)}",
                    "{(3,226,-10):(7,226,0)}",
                    "{(3,226,10):(7,226,20)}",
                    "{(3,226,30):(7,226,40)}"
                ]
            }
        ]
    }')
    '''
    xml = ''
    configurations = info["config"]
    for configuration in configurations:
            active = configuration.get("active", "True")
            if active == "False" :
                continue
            cuboidtype = configuration["type"]
            coords = configuration["points"]
            for point in coords:
                start, end = point.strip('{}').split(':')
                x1,y1,z1 = start.strip('()').split(',')
                x2,y2,z2 = end.strip('()').split(',')
                xml += '<DrawCuboid x1="'+ x1 +'"  y1="'+ y1 +'" z1="'+ z1 +'" '
                xml += 'x2="'+ x2 +'"  y2="'+ y2 +'" z2="'+ z2 + '" '
                xml += 'type="'+ cuboidtype+'" /> \n'
    return str(xml)


with open('moment.json') as data_file:
    data = json.load(data_file)

#pprint(data)

setPosition(data, 1,2,3)

def printGrid(m, n, feel=1, see=3, appear=5):
    grid = np.array([["-" for i in range(n)] for j in range(m)])
    x, y = m-1, (n-1)/2
    grid[x, y] = "X"
    for i in np.arange(appear)+1:
        print x-i, y-i, y+i
        grid[x-i, max(y-i,0):min(y+i+1,n)] = "."
    for i in np.arange(see)+1:
        print x-i, y-i, y+i
        grid[x-i, max(y-i,0):min(y+i+1,n)] = "o"
    for row in grid :
        for elem in row :
            print elem,
        print
#pprint(data)

debug = False
if debug :
    print getCuboids(CUBOID_SAMPLE)
    print getBlocks(BLOCK_ITEM_SAMPLE)
    print getItems(BLOCK_ITEM_SAMPLE)


def plotActivity(structure, fig, label, color) :
    # Assuming every structure is a 2D array of neuron ensembles with a value of activation
    x, z = structure.shape
    fig = plt.figure(fig)
    ax = fig.add_subplot(111, projection='3d')
    colors = ['r', 'g', 'b']*7
    for zi in np.arange(z):
        xs = np.arange(x)
        ys = structure[zi]
        cs = np.array(['c'] * x)
        cs[(0.5<ys).nonzero()[0]] = colors[zi/3]
        ax.bar(xs, ys, zs=zi, zdir='y', color=cs, alpha=0.8)
    ax.set_xlabel('X')
    ax.set_ylabel('Z')
    ax.set_zlabel(label)
    ax.set_zlim(0,1)

colors = ['r', 'b', 'g', 'y']*2

def plotItems(myX, myZ, obX, obZ, obYaws, fig, subplot) :
    fig = plt.figure(fig)
    ax = fig.add_subplot(subplot)
    ax.plot(np.array(obX), np.array(obZ),'o')
    ax.plot(myX, myZ, 'x')
    for i in range(len(obYaws)) :
        theta = math.radians(obYaws[i] + 90)
        ax.arrow(myX, myZ, 4*math.cos(theta), 4*math.sin(theta), color=colors[i], label=i)
    ax.arrow(myX, myZ, 14.14*math.cos(np.pi/2 - AGENT_FOV/2), 14.14*math.sin(np.pi/2 - AGENT_FOV/2), color='g')
    ax.arrow(myX, myZ, 14.14*math.cos(np.pi/2 + AGENT_FOV/2), 14.14*math.sin(np.pi/2 + AGENT_FOV/2), color='g')
    ax.set_xlim(xmin=-50, xmax=50)
    ax.set_ylim(ymin=-50, ymax=50)
    fig.gca().invert_xaxis()

#struct = np.random.normal(.1, .05, (20,20))
struct = np.zeros((20,20)) + .1
#plotActivity(plt, struct)

#plt.show()
#printGrid(9,9)
