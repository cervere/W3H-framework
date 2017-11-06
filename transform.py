import numpy as np
import json
import matplotlib.pyplot as plt

sight = 5
position = [sight, sight-1]
fov = np.pi * (1./2) #Starting with 90, can be changed to 120


# y = m*x + c
# c keeps chagning depending on the agent position
# If agent is at (x,y), c = (y - mx) where m is the slope => tan(fov/2)

#So given an iem's position, it can be verified if the item falls within the
# field of vision by :
# getting the x coordinate that would be on the line y=m*x+c for a given y of the item

def inFOV (agent, item, fov=np.pi * (1./2)) :
    m = np.tan(fov/2)
    c = agent[1] - m*agent[0]
    x = (item[1] - c) / m
    return item[0] < x


reach = 1
see = 3
appear = 5
vision = np.zeros((sight+1, 2*sight-1))

with open('ob.json') as fp:
    proto = json.load(fp)
costh = np.ceil(np.sin(fov/2))
vision[position[0], position[1]] =  1

y1reach = position[1] - int(reach*costh)
y2reach = position[1] + int(reach*costh)
vision[position[0] - reach : position[0] + 1, y1reach : y2reach + 1] = 1

y1see = position[1] - int(see*costh) + 1
y2see = position[1] + int(see*costh)
vision[position[0] - see : position[0] - reach , y1see : y2see] = 1

y1appear = position[1] - int(appear*costh) + 1
y2appear = position[1] + int(appear*costh)
vision[position[0] - appear : position[0] - see , y1appear : y2appear] = 1

def euc_dist (a, b) :
    return np.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2)

def ref (a, b) :
    return [b[0]-a[0], b[1]-a[1]]

print vision
plt.imshow(vision, interpolation='nearest')
plt.show()
agent = [5.5, -31.611517129711572]
item = [2.5, -31.5]
print euc_dist(agent,item)
print ref(agent, item)
