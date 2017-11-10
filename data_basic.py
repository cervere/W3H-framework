import json
from pprint import pprint

blocks_basic = json.loads('''
{
"config" : [
        {
            "type" : "lava",
            "active" : "False",
            "points" : [
                        "(5,226,9)", "(5,226,14)", "(5,226,19)",
                        "(5,226,29)", "(5,226,39)"
                    ]
        },
        {
            "type" : "stained_glass_pane",
            "active" : "False",
            "points" : [
                        "(5,226,9)", "(5,226,14)", "(5,226,19)",
                        "(5,226,29)", "(5,226,39)"
                    ]
        },
        {
            "type" : "gravel",
            "active" : "False",
            "points" : ["(5,226,50)"]
        },
        {
            "type" : "cobblestone",
            "active" : "False",
            "points" : [
                        "(5,226,35)", "(5,226,15)", "(5,226,-5)",
                        "(5,226,-25)", "(5,226,-45)"
                        ]
        }
    ]
}
''')

floor_basic = json.loads('''
{
"config" : [
        {
            "type" : "sandstone",
            "points" : ["{(-50,226,0):(50,226,50)}"]
        },
        {
            "type" : "lapis_block",
            "points" : [
                "{(0,226,0):(0,226,50)}"
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

items_basic = json.loads('''
{
"config" : [
        {
            "type" : "cake",
            "points" : [
                "(6,226,25)"
            ]
        },
        {
            "type" : "apple",
            "points" : [
                "(3,226,25)"
            ]
        },
        {
            "type" : "water_bucket",
            "points" : [
                "(-3,226,25)"
            ]
        },
        {
            "type" : "mushroom_stew",
            "points" : [
                "(-6,226,25)"
            ]
        }
    ]
}
''')
