import json

with open('sample.bplist',mode='r') as f:
    j = json.load(f)
    # print(j)
    print(j.keys())
    j = j['customData']['syncURL']
    print(j)