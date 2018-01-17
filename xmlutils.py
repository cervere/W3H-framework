from methods import getBlocks,getCuboids,getItems
from data import *
from data_basic import *
from constants import *

global x, y, z, START_POINT

x, y, z = 0, 1, 2
START_POINT = (0.5, 227, 0.5)

def GetMissionXML(summary, itemDrawingXML):
    ''' Build an XML mission string that uses the RewardForCollectingItem mission handler.'''

    return '''<?xml version="1.0" encoding="UTF-8" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>''' + summary + '''</Summary>
        </About>

        <ServerSection>
            <ServerHandlers>
                <FlatWorldGenerator generatorString="3;7,220*1,5*3,2;3;,biome_1" forceReset="true"/>
                <DrawingDecorator>
                ''' + itemDrawingXML + '''
                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="30000"/>
                <ServerQuitWhenAnyAgentFinishes />
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>''' + AGENT_NAME + '''</Name>
            <AgentStart>
                <Placement x=
                "''' + str(START_POINT[x]) + '''" y=
                "''' + str(START_POINT[y]) + '''" z=
                "''' + str(START_POINT[z]) + '''"/>
                <Inventory>
                    <InventoryItem slot="8" type="diamond_pickaxe"/>
                </Inventory>
            </AgentStart>
            <AgentHandlers>
                <InventoryCommands/>
                <ChatCommands/>
                <AbsoluteMovementCommands/>
                <DiscreteMovementCommands />
                <VideoProducer>
                    <Width>960</Width>
                    <Height>640</Height>
                </VideoProducer>
                <RewardForCollectingItem>
                    <Item reward="2" type="fish porkchop beef chicken rabbit mutton"/>
                    <Item reward="1" type="potato egg carrot"/>
                    <Item reward="-1" type="apple melon"/>
                    <Item reward="-2" type="sugar cake cookie pumpkin_pie"/>
                </RewardForCollectingItem>
                <ContinuousMovementCommands turnSpeedDegs="50"/>
                <ObservationFromFullStats/>
                <ObservationFromNearbyEntities>
                    <Range name="close_entities" xrange="2" yrange="2" zrange="2" />
                    <Range name="far_entities" xrange="10" yrange="2" zrange="10" update_frequency="1"/>
                </ObservationFromNearbyEntities>
                  <ObservationFromGrid>
                      <Grid name="reach">
                        <min x="-1" y="-1" z="0"/>
                        <max x="1" y="-1" z="1"/>
                      </Grid>
                      <Grid name="see">
                        <min x="-2" y="-1" z="2"/>
                        <max x="2" y="-1" z="3"/>
                      </Grid>
                      <Grid name="appear">
                        <min x="-3" y="-1" z="4"/>
                        <max x="3" y="-1" z="5"/>
                      </Grid>
                  </ObservationFromGrid>
      <AgentQuitFromTouchingBlockType>
          <Block type="grass" />
      </AgentQuitFromTouchingBlockType>

            </AgentHandlers>
        </AgentSection>

    </Mission>'''


def GetItemDrawingXML(testing=False):
    ''' Build the required blocks, items and the type of floor'''
    if testing : return str(getCuboids(floor_basic) + getBlocks(blocks_basic) + getItems(items_basic))
    else : return str(getCuboids(floor) + getItems(items) + getBlocks(blocks))
