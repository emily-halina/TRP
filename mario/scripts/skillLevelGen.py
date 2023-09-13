import sys

TILE = 16

ID_TO_NAME = {
    2 : "goomba",
    3 : "winged goomba",
    4 : "red koopa",
    5 : "winged red koopa",
    6 : "green koopa",
    7 : "winged green koopa",
    8 : "spiky",
    9 : "winged spiky",
    10 : "bullet bill",
    11 : "pirahna plant",
    14 : "shell",
    17 : "pit"
}

ID_TO_SYMBOL = {
    2 : "g",
    4 : "r",
    6 : "k",
    11 : "T",
    14 : "k",
    17 : "-"
}

def concat_files(file_list):
    """
    in: n/a
    out: str repping filename of combined file
    """
    N = 0
    move_seq = []
    x = []
    y = []
    death_info = {}
    for name in file_list:
        f = open(name, "r")
        content = f.read().splitlines()
        f.close()

        N += int(content[0])
        move_seq += content[1].split()
        x += content[2].split()
        y += content[3].split()
        for i in range(5, 22):
            process_deaths(content[i].split(), death_info)

    positions = []
    for i in range(len(x)):
        positions.append((float(x[i]), float(y[i])))

    content_dict = {}
    content_dict["N"] = N
    content_dict["move_seq"] = move_seq
    content_dict["positions"] = positions
    content_dict["death_info"] = death_info

    return content_dict

def process_input(filename):
    """
    in: str of filename
    out: (str, key) dictionary contaning contents of file appropriately typed 
    """
    f = open(filename, "r")
    content = f.read().splitlines()
    f.close()

    N = int(content[0])
    move_seq = content[1].split()
    x = content[2].split()
    y = content[3].split()

    positions = []
    for i in range(len(x)):
        positions.append((float(x[i]), float(y[i])))
    
    death_info = {}
    for i in range(5, 22):
        process_deaths(content[i].split(), death_info)

    # return as dict for easy ability to add 
    content_dict = {}
    content_dict["N"] = N
    content_dict["move_seq"] = move_seq
    content_dict["positions"] = positions
    content_dict["death_info"] = death_info
    return content_dict

def process_deaths(content, death_info):
    """
    collect death information by tile and location for a given enemy
    """
    if (len(content) == 1):
        return
    id = int(content[0][:len(content[0])-1])

    if id not in death_info.keys():
        death_info[id] = {}
    
    for i in range(1, len(content), 3):
        count = int(content[i])
        # can remove int casting here for more specific positions (or do something based on subtile or w/e)
        pos = (int(float(content[i + 1]) / TILE), int(float(content[i + 2]) / TILE))
        if pos in death_info[id]:
            death_info[id][pos] += count
        else:
            death_info[id][pos] = count
    return


def build_level(content):
    # initialize empty level
    # level[i][j] corresponds to i-th tile 
    level = []
    for i in range(16):
        row = []
        for j in range(1000):
            row.append("X")
        level.append(row)

    N = content["N"]
    positions = content["positions"]

    furthest_pos = (-1, -1)
    for i in range(N):
        pos = positions[i]
        tile_pos = [int(pos[0] / TILE), int(pos[1] / TILE)]
        if (tile_pos[0] > furthest_pos[0]):
            furthest_pos = (tile_pos[0], tile_pos[1])
        # make it so only these tiles are accessible
        # need extra head room if we are jumping (todo make this more granular)
        if (i != N - 1 and positions[i+1][1] / TILE != tile_pos[1]):
            level[tile_pos[1]][tile_pos[0]] = "-"
            level[tile_pos[1]][tile_pos[0] + 1] = "-"
            level[tile_pos[1] - 1][tile_pos[0]] = "-"
            level[tile_pos[1] - 2][tile_pos[0]] = "-"
        # otherwise, just need a 1-1 space
        else:
            level[tile_pos[1]][tile_pos[0]] = "-"
        
    
    # place mario in the default position
    mario_pos = [int(positions[0][0] / TILE), int(positions[0][1] / TILE)]
    level[mario_pos[1]][mario_pos[0]] = "M"

    # place flagpole at end of level
    #flag_pos = [int(positions[N-1][0] / TILE), int(positions[N-1][1] / TILE)]
    flag_pos = furthest_pos
    for i in range(16):
        if i < 12:
            level[i][flag_pos[0]] = "-"
        elif i > 13:
            level[i][flag_pos[0]] = "X"
        
    level[12][flag_pos[0]] = "F"
    level[13][flag_pos[0]] = "#"
    
    # testing some basic enemy stuff
    for key in content["death_info"]:
        if key == 17:
            for p in content["death_info"][key]:
                i = 15
                while level[i][p[0]] == "X":
                    level[i][p[0]] = "-"
                    i -= 1
    
    # trim level so it's not overly big
    for i in range(len(level)):
        level[i] = level[i][0 : flag_pos[0] + 1]
    
    return level

def output_to_file(level, outfile="temp.txt"):
    f = open(outfile, "w+")
    for i in range(len(level)):
        f.write("".join(level[i]) + "\n")
    f.close()
    return

def main():
    content = None
    if len(sys.argv) == 2:
        content = process_input(sys.argv[1])
    elif len(sys.argv) > 2:
        content = concat_files(sys.argv[1:])
    else:
        print("Usage: python3 skillLevelGen.py levelName1 levelName2 . . . (at least 1)")
        return
    level = build_level(content)
    output_to_file(level)
    return

if __name__ == "__main__":
    main()