

with open("t.txt","r") as f:
    cont=f.read()
    for line in cont.split("\n"):
        splitup = line.split()
        print(f"splitup:")
        print(splitup)
        print(f"len of splitup: {len(splitup)}")
        print(f"splitup at 0:{splitup[0]}")