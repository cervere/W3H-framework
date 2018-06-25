# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier
# Distributed under the (new) BSD License.
#
# Contributors: Nicolas P. Rougier (Nicolas.Rougier@inria.fr)
# -----------------------------------------------------------------------------
# References:
#
# * Interaction between cognitive and motor cortico-basal ganglia loops during
#   decision making: a computational study. M. Guthrie, A. Leblois, A. Garenne,
#   and T. Boraud. Journal of Neurophysiology, 109:3025–3040, 2013.
# -----------------------------------------------------------------------------
import numpy as np
from model import *
import matplotlib.backends.backend_pdf as pltpdf


tau = 0.01
clamp = Clamp(min=0, max=1000)
sigmoid = Sigmoid(Vmin=0, Vmax=20, Vh=16, Vc=3)
threshold  = 40
TMS = 3000
STR_GAIN = +1.0

def weights(shape):
    Wmin, Wmax = 0.25, 0.75
    N = np.random.normal(0.5, 0.005, shape)
    N = np.minimum(np.maximum(N, 0.0), 1.0)
    return (Wmin + (Wmax - Wmin) * N)


ACC_CTX = AssociativeStructure(
    tau=tau, rest=- 3.0, noise=0.010, activation=clamp)
ACC_STR = AssociativeStructure(
    tau=tau, rest=0.0, noise=0.001, activation=sigmoid)
ACC_STN = Structure(tau=tau, rest=-10.0, noise=0.001, activation=clamp)
ACC_GPI = Structure(tau=tau, rest=+10.0, noise=0.030, activation=clamp)
ACC_THL = Structure(tau=tau, rest=-40.0, noise=0.001, activation=clamp)
structures = (ACC_CTX, ACC_STR, ACC_STN, ACC_GPI, ACC_THL)



cognitive_connections = [ #Only cognitive channels
    OneToOne(ACC_CTX.cog.V, ACC_STR.cog.Isyn, np.array([0.53183305, 0.56847023, 0.52183305, 0.55847023]), gain=STR_GAIN),
    #OneToOne(ACC_CTX.cog.V, ACC_STR.cog.Isyn, weights(4), gain=STR_GAIN),
    OneToOne(ACC_CTX.cog.V, ACC_STN.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_STR.cog.V, ACC_GPI.cog.Isyn, np.ones(4), gain=-2.0),
    OneToAll(ACC_STN.cog.V, ACC_GPI.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_GPI.cog.V, ACC_THL.cog.Isyn, np.ones(4), gain=-0.5),
    OneToOne(ACC_THL.cog.V, ACC_CTX.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_CTX.cog.V, ACC_THL.cog.Isyn, np.ones(4), gain=+0.4)
]

motor_connections = [ #Only motor channels
    OneToOne(ACC_CTX.mot.V, ACC_STR.mot.Isyn, weights(4), gain=STR_GAIN),
    OneToOne(ACC_CTX.mot.V, ACC_STN.mot.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_STR.mot.V, ACC_GPI.mot.Isyn, np.ones(4), gain=-2.0),
    OneToAll(ACC_STN.mot.V, ACC_GPI.mot.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_GPI.mot.V, ACC_THL.mot.Isyn, np.ones(4), gain=-0.5),
    OneToOne(ACC_THL.mot.V, ACC_CTX.mot.Isyn, np.ones(4), gain=+1.0),
    OneToOne(ACC_CTX.mot.V, ACC_THL.mot.Isyn, np.ones(4), gain=+0.4)
]

associative_connections = [ # associative channels
    OneToOne(ACC_CTX.ass.V, ACC_STR.ass.Isyn, weights(4 * 4), gain=STR_GAIN),
    CogToAss(ACC_CTX.cog.V, ACC_STR.ass.Isyn, weights(4), gain=+0.2),
    MotToAss(ACC_CTX.mot.V, ACC_STR.ass.Isyn, weights(4), gain=+0.2),
    AssToCog(ACC_STR.ass.V, ACC_GPI.cog.Isyn, np.ones(4), gain=-2.0),
    AssToMot(ACC_STR.ass.V, ACC_GPI.mot.Isyn, np.ones(4), gain=-2.0)
]

connections = []
for c in cognitive_connections : connections.append(c)
for m in motor_connections : connections.append(m)
for a in associative_connections : connections.append(a)

OFC_CTX = AssociativeStructure(
    tau=tau, rest=- 3.0, noise=0.010, activation=clamp)
OFC_STR = AssociativeStructure(
    tau=tau, rest=0.0, noise=0.001, activation=sigmoid)
OFC_STN = Structure(tau=tau, rest=-10.0, noise=0.001, activation=clamp)
OFC_GPI = Structure(tau=tau, rest=+10.0, noise=0.030, activation=clamp)
OFC_THL = Structure(tau=tau, rest=-40.0, noise=0.001, activation=clamp)
OFC_structures = (OFC_CTX, OFC_STR, OFC_STN, OFC_GPI, OFC_THL)

cognitive_connections_emotion = [ #Only cognitive channels
    OneToOne(OFC_CTX.cog.V, OFC_STR.cog.Isyn, np.array([0.56847023, 0.53183305, 0.55847023, 0.52183305]), gain=STR_GAIN),
    #OneToOne(OFC_CTX.cog.V, OFC_STR.cog.Isyn, weights(4), gain=STR_GAIN),
    OneToOne(OFC_CTX.cog.V, OFC_STN.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(OFC_STR.cog.V, OFC_GPI.cog.Isyn, np.ones(4), gain=-2.0),
    OneToAll(OFC_STN.cog.V, OFC_GPI.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(OFC_GPI.cog.V, OFC_THL.cog.Isyn, np.ones(4), gain=-0.5),
    OneToOne(OFC_THL.cog.V, OFC_CTX.cog.Isyn, np.ones(4), gain=+1.0),
    OneToOne(OFC_CTX.cog.V, OFC_THL.cog.Isyn, np.ones(4), gain=+0.4)
]

OFC_connections = []
for ce in cognitive_connections_emotion : OFC_connections.append(ce)



cues_mot = np.array([0, 1, 2, 3])
cues_cog = np.array([0, 1, 2, 3])
cues_value = np.ones(4) * 0.5
cues_reward = np.array([3.0, 2.0, 1.0, 0.0]) / 3.0

def set_trial(c, m, v, noise) :
    ACC_CTX.cog.Iext[c] = v + np.random.normal(0, v * noise)
    ACC_CTX.mot.Iext[m] = v + np.random.normal(0, v * noise)
    ACC_CTX.ass.Iext[c * 4 + m] = v + np.random.normal(0, v * noise)

colors = ['r', 'b', 'g', 'y']

def start_trial(cues, positions, bias=-1):
    combo = np.zeros(4)
    v = 7
    noise = 0.01
    ACC_CTX.mot.Iext = 0
    ACC_CTX.cog.Iext = 0
    ACC_CTX.ass.Iext = 0
    for c, m in zip(cues, positions) :
        combo[m] = c
        print c, m
        print colors[c], ' at ', colors[m]
        set_trial(c,m,v,noise)
    #print ' bias ', colors[np.max(cues_cog[:num])]
    s = v + 5
    if bias > -1 : ACC_STR.cog.Iext[bias] = s + np.random.normal(0, s * noise)
    return combo

def start_ofc_trial(cues):
    v = 14
    noise = 0.01
    OFC_CTX.cog.Iext = 0
    for c in cues :
        OFC_CTX.cog.Iext[c] = v + np.random.normal(0, v * noise)



def stop_trial():
    ACC_CTX.mot.Iext = 0
    ACC_CTX.cog.Iext = 0
    ACC_CTX.ass.Iext = 0
    OFC_CTX.cog.Iext = 0


def iterate(dt):
    global connections, OFC_connections, structures, OFC_structures

    # Flush connections
    for connection in connections:
        connection.flush()

    for OFC_connection in OFC_connections:
        OFC_connection.flush()


    # Propagate activities
    for connection in connections:
        connection.propagate()

    for OFC_connection in OFC_connections:
        OFC_connection.propagate()

    # Compute new activities
    for structure in structures:
        structure.evaluate(dt)

    for OFC_structure in OFC_structures:
        OFC_structure.evaluate(dt)


def reset():
    global cues_values, structures, OFC_structures
    cues_value = np.ones(4) * 0.5
    for structure in structures:
        structure.reset()
    for OFC_structure in OFC_structures:
        OFC_structure.reset()


dt = 0.001
from display import *

dtype = [("CTX", [("mot", float, 4), ("cog", float, 4), ("ass", float, 16)]),
         ("STR", [("mot", float, 4), ("cog", float, 4), ("ass", float, 16)]),
         ("GPI", [("mot", float, 4), ("cog", float, 4)]),
         ("THL", [("mot", float, 4), ("cog", float, 4)]),
         ("STN", [("mot", float, 4), ("cog", float, 4)])]

def choose(cues, positions, bias=False):
    reset()
    mot_choice = -1
    ofc_chosen, acc_chosen = False, False
    hunger = np.random.uniform(0, 1)
    thirst = np.random.uniform(0, 1)

    for i in xrange(0, 500):
        iterate(dt)
    start_ofc_trial(cues)
    for i in xrange(500, TMS-500):
        iterate(dt)
        if not ofc_chosen and OFC_CTX.cog.delta > 20:
            ofc_choice = np.argmax(OFC_CTX.cog.V)
            print ' chosen OFC : ', ofc_choice
            if bias :
                combo = start_trial(cues, positions, ofc_choice)
            else :
                combo = start_trial(cues, positions)
            ofc_chosen = True
        if not acc_chosen and ACC_CTX.mot.delta > threshold :
            mot_choice = np.argmax(ACC_CTX.mot.V)
        #     break
    stop_trial()
    for i in xrange(TMS-500, TMS):
        iterate(dt)

    history = np.zeros(TMS, dtype=dtype)
    history["CTX"]["mot"] = ACC_CTX.mot.history[:TMS]
    history["CTX"]["cog"] = ACC_CTX.cog.history[:TMS]

    OFC_history = np.zeros(TMS, dtype=dtype)
    OFC_history["CTX"]["cog"] = OFC_CTX.cog.history[:TMS]

    fig1 = display_ctx(OFC_history, TMS/1000.0)
    fig2 = display_ctx(history, TMS/1000.0)
    pdf = pltpdf.PdfPages("output.pdf")
    #for fig in xrange(1, plt.figure().number): ## will open an empty extra figure :(
    pdf.savefig( fig1 )
    pdf.savefig( fig2 )

    pdf.close()

    if mot_choice > -1 :
        return combo[mot_choice], mot_choice
    else :
        return -1, -1

def test() :
    for i in range(5) :
        np.random.shuffle(cues_cog)
        np.random.shuffle(cues_mot)
        c1, c2 = cues_cog[:2]
        m1, m2 = cues_mot[:2]
        cues = [c1, c2]
        positions = [m1, m2]
        cog, mot = choose(cues, positions)
        print 'choosen ', cog, ' at ', mot


# -----------------------------------------------------------------------------
