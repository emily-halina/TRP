import sys

LEVEL_NAME = sys.argv[1]
OUT_NAME = "temp.txt"

def read_file(filename):
    f = open(filename, "r")
    content = f.read().splitlines()
    f.close()

    content_dict = {}

    X = content[0].split(" ")
    Y = content[1].split(" ")
    assert(len(X) == len(Y))
    content_dict["positions"] = []
    for i in range(len(X)):
        content_dict["positions"].append((int(X[i]), int(Y[i])))
    
    return content_dict

def concat_files(filenames):
    content = {}
    content["positions"] = []

    for f in filenames:
        file_content = read_file(f)
        for p in file_content["positions"]:
            content["positions"].append(p)

    return content

def convert(content, original_level):
    level = []
    for i in range(9):
        level.append([])
        for j in range(13):
            level[i].append("w")
    
    positions = content["positions"]

    for pos in positions:
        level[pos[0]][pos[1]] = "."
    
    f = open(original_level, "r")
    og_content = f.read().splitlines()
    f.close()
    
    player = None
    key = None
    goal = None
    for i in range(9):
        for j in range(13):
            if og_content[i][j] == "A":
                player = (i, j)
            if og_content[i][j] == "+":
                key = (i, j)
            if og_content[i][j] == "g":
                goal = (i, j)

    level[player[0]][player[1]] = "A"
    level[key[0]][key[1]] = "+"
    level[goal[0]][goal[1]] = "g"

    return level

def write_file(level, filename):
    f = open(filename, "w+")
    for row in level:
        for c in row:
            f.write(c)
        f.write("\n")
    f.close()
    return

def main():
    content = None
    if len(sys.argv) == 3:
        #print("argv 3")
        content = read_file(sys.argv[2])
    else:
        content = concat_files(sys.argv[2:])
    
    canvern_level = convert(content, LEVEL_NAME)
    write_file(canvern_level, OUT_NAME)
    return

if __name__ == "__main__":
    main()