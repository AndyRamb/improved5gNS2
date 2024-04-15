import json
 
# Data to be written
dictionary = {
        "id":"root",
        "parentId": "NULL",
        "rate": 100000,
        "ceil": 100000,
        "burst": 2000,
        "cburst": 2000,
        "level": 1,
        "quantum": 1500,
        "mbuffer": 60
    }

# Serializing json
json_object = json.dumps(dictionary, indent=4)
 
# Writing to sample.json
with open("json/sample.json", "w") as outfile:
    outfile.write(json_object)
