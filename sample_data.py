import json

BLOCK_ITEM_SAMPLE = json.loads('''
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

CUBOID_SAMPLE = json.loads('''
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
'''
)