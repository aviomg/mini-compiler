import json

register_mapping={
    "x0":"zero",
    "x1":"ra",
    "x2":"sp",
    "x3":"gp",
    "x4":"tp",
}
streg=5
for i in range(0,3):
    keyname=f"x{streg}"
    register_mapping[keyname]=f"t{i}"
    streg+=1
streg=8
for i in range(0,2):
    keyname=f"x{streg}"
    register_mapping[keyname]=f"s{i}"
    streg+=1
streg=10
for i in range(0,8):
    keyname=f"x{streg}"
    register_mapping[keyname]=f"a{i}"
    streg+=1
streg=18
for i in range(2,12):
    keyname=f"x{streg}"
    register_mapping[keyname]=f"s{i}"
    streg+=1
streg=28
for i in range(3,7):
    keyname=f"x{streg}"
    register_mapping[keyname]=f"t{i}"
    streg+=1

filepath="reg_map.json"
with open(filepath,"w") as f:
    json.dump(register_mapping,f,indent=4)


#with open("reg_map.json", )