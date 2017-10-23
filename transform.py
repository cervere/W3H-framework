import numpy as np
import json

sight = 5
position = [sight, sight]
fov = 90

reach = 1
see = 3
appear = 5
vision = np.zeros((sight+1, 2*sight-1))

with open('ob.json') as fp:
    proto = json.load(fp)
costh = np.cos(90-fov/2)
vision[position[0], position[1]] =  1
y1reach = position[1] - int(np.ceil(reach*costh))
y2reach = position[1] + int(np.ceil(reach*costh))
print y1reach, y2reach
vision[position[0] - reach : position[0] + 1, y1reach : y2reach + 1] = 1

y1see = position[1] - int(np.ceil(see*costh))
y2see = position[1] + int(np.ceil(see*costh))
vision[position[0] - see : position[0] - reach , y1see : y2see + 1] = 1
print y1see, y2see
y1appear = position[1] - int(np.ceil(appear*costh))
y2appear = position[1] + int(np.ceil(appear*costh))
vision[position[0] - appear : position[0] - see , y1appear : y2appear + 1] = 1
print y1appear, y2appear
print vision
