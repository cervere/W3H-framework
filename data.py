import json
from pprint import pprint

blocks = json.loads('''
{
"config" : [
        {
            "type" : "lava",
            "points" : [
                        "(5,226,9)", "(5,226,14)", "(5,226,19)",
                        "(5,226,29)", "(5,226,39)"
                    ]
        },
        {
            "type" : "stained_glass_pane",
            "points" : [
                        "(5,226,9)", "(5,226,14)", "(5,226,19)",
                        "(5,226,29)", "(5,226,39)"
                    ]
        },
        {
            "type" : "gravel",
            "points" : ["(5,226,50)"]
        },
        {
            "type" : "cobblestone",
            "points" : [
                        "(5,226,35)", "(5,226,15)", "(5,226,-5)",
                        "(5,226,-25)", "(5,226,-45)"
                        ]
        }
    ]
}
''')

floor = json.loads('''
{
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
        },
        {
            "type" : "stone",
            "active" : "False",
            "points" : [
                "{(5,227,-33):(5,227,-33)}",
                "{(5,227,-13):(5,227,-13)}",
                "{(5,227,3):(5,227,3)}",
                "{(5,227,23):(5,227,23)}",
                "{(5,227,43):(5,227,43)}"
            ]
        }
    ]
}
''')

items = json.loads('''
{
"config" : [
        {
            "type" : "apple",
            "points" : [
                "(2,226,-42)", "(2,226,-22)", "(2,226,-2)",
                "(2,226,18)", "(2,226,38)"
                , "(4,227,-49)"
            ]
        },
        {
            "type" : "water_bucket",
            "points" : [
                "(2,226,-32)", "(2,226,-12)", "(2,226,-2)",
                "(2,226,18)", "(2,226,38)"
            ]
        }
    ]
}
''')

with open('observations.json') as fp:
    obs = json.load(fp)
for ob in obs['data'] :
    print ob['WorldTime'], ob['XPos'], ob['YPos'], ob['ZPos']
#pprint(obs)