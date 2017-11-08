# W3H-framework
## Systemic view of brain modeling

This framework, under development, is an attempt to model different memory systems of the brain in interaction, which results in the wide range  of behavioral repertoire of an animal.

The framework describes the interactions between several sensori-motor loops corresponding to different aspects of the external environment in which the animal survives.  [[1]](https://hal.inria.fr/hal-01246653/)

## Abstract :
This research statement is inspired from the idea of 'survival of an animal in an external world'. An animal constantly interacts with various stimuli in its environment through its actions. These stimuli vary in time, in their characteristics, and in their outcomes when the animal interacts with them. Essentially, this variation results in different types of uncertainty in the animal's representation of the environment. Thereby, the wide range of animal's behavioral repertoire to interact with such an environment emerges from its internal states and needs, estimating the uncertainty in the environment, and continuously  learning from the outcomes of its actions.

The aforementioned process involving the animal's perception, action and learning in the external environment is carried out by several sensory and motor information flows of the brain+body system. Depending on the context, animal's behavior emerges from either a conditioned response (an appetitive or an aversive response triggered by a previously learned association to a certain stimulus), or a goal-directed motivation that involves planning a certain task and more generally from the continuous learning that reinforces the animal's choices. Plenty of research in neuroscience explains the above mentioned processes, but mostly as individual accounts of specific aspects whereas the key aspect of our work is to propose an integrated process of different sensory-motor flows involved.

The attempt is thus to integrate the knowledge of different sensori-motor loops and their functioning to this end. Such an integrated representation requires finer definitions of animal's state in the environment, its internal needs and action contingencies depending on its evaluation of the state (using anticipation, desirability and internal motivation etc.).

Given the complexity of the brain structures, the task we target and the data involved, with respect to the Marr and Poggio tri-level hypothesis*, we target to link the functional (??) level to the algorithmic level, thus propose an effective description formalizing the existing functional specifications of the mentioned sensori-motor loops. At the implementation level, beyond the usual fairly constrained neuronal computation framework, we consider a more general dynamical system, compatible with biological constraints such as distributed computing, local adaptation of the global objectives.

At the experimental level, we choose a simple but realistic task where an agent has to explore  the environment and exploit the available stimuli considering the needs of its internal state. We use Malmo, an experimentation platform by Microsoft, based on the Minecraft game, to design a controlled environment (varying level of complexity) and further study the emerging behavior of the agent.

The framework design is compatible with the integration of existing detailed neuronal implementations of the individual brain structures and pathways in the related aspects. Thereby it provides a way to validate them in a systemic context. (For e.g, Some parts of Carrere et al model for Amygdala, VTA and Topalidau's model of action selection and habit formation would be a great start)            

(References to be added)
# References
[1] - Alexandre, Frédéric. "A behavioral framework for a systemic view of brain modeling." (2015).
