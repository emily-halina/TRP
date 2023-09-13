import sys
from random import choice, random

MIN = int(sys.argv[3])
LEVEL = sys.argv[1]
ORIGINAL = sys.argv[2]
ZERO_LIST = [".", "A", "+", "g", "2", "3"]
ENEMY_LIST = ["2", "3"]
ENEMIES = False

sections = []

# section = two 2-tuple depecting bounding box in original level
# [(x1, y1), (x2, y2)], with the smaller point on the left (top left, bottom right)
def bsp(section):
    if section == None or section in sections:
        return
    h = section[1][0] - section[0][0] + 1
    w = section[1][1] - section[0][1] + 1

    width_limit = w < 2 * MIN
    height_limit = h < 2 * MIN
    split = None
    
    # choose split choice based on
    if not width_limit and not height_limit:
        split = choice(["h", "v"]) 
    elif width_limit and not height_limit:
        split = "h"
    elif not width_limit and height_limit:
        split = "v"
    
    # base case: too smol
    if split == None:
        #print("reached", section)
        sections.append(section)
        return

    # otherwise, split randomly and recurse with two resulting segments
    dir = random() 
    s1 = s2 = None

    # horizontal
    if split == "h":
        offset = choice(range(h))
        position = section[0][0] + offset
        #print(position, "hor")

        s1 = [section[0], (position, section[1][1])]
        s2 = [(position + 1, section[0][1]), section[1]]

    # vertical
    elif split == "v":
        offset = choice(range(w))
        position = section[0][1] + offset
        #print(position, "vert")

        s1 = [section[0], (section[1][0], position)]
        s2 = [(section[0][0], position + 1), section[1]]
    
    if not s1 and not s2:
        print("error!")
        return

    if not s1 in sections:
        bsp(s1)

    if not s2 in sections:
        bsp(s2)
    
def get_level_sect(content, section):
    level_sect = []
    r = 0
    for i in range(section[0][0], section[1][0] + 1):
        level_sect.append([])
        for j in range(section[0][1], section[1][1] + 1):
            level_sect[r].append(content[i][j])
        r += 1
    return level_sect

def get_closest_matches(source, pattern, original):
    matches = []
    max_score = -1
    ph = len(pattern)
    pw = len(pattern[0])
    for i in range(len(source) - ph + 1):
        for j in range(len(source[0]) - pw + 1):
            score = 0
            segment = []
            s = 0
            for k in range(0, ph):
                segment.append([])
                for l in range(0, pw):
                    segment[s].append(original[i + k][j + l])
                    if source[i + k][j + l] == pattern[k][l]:
                        score += 1
                s += 1
            
            if score > max_score:
                matches.clear()
                matches.append(segment)
                max_score = score
            elif score == max_score:
                matches.append(segment)
    #print(max_score)
    return matches

def binarify_level(level):
    bin_level = []
    b = 0
    for i in range(len(level)):
        bin_level.append([])
        for j in range(len(level[0])):
            if level[i][j] in ZERO_LIST:
                bin_level[b].append(".")
            else:
                bin_level[b].append("w")
        b += 1
    return bin_level

# remove all zeros and insert the proper locations for key & goal & player 
def clean_level(level, mcts):
    for i in range(len(level)):
        for j in range(len(level[0])):
            if not ENEMIES and level[i][j] in ENEMY_LIST:
                level[i][j] = "."
            if level[i][j] in ZERO_LIST:
                level[i][j] = "."
            
    player = None
    key = None
    goal = None
    for i in range(len(mcts)):
        for j in range(len(mcts[0])):
            if mcts[i][j] == "A":
                player = (i, j)
            if mcts[i][j] == "+":
                key = (i, j)
            if mcts[i][j] == "g":
                goal = (i, j)
    #print(player, key, goal)
    level[player[0]][player[1]] = "A"
    level[key[0]][key[1]] = "+"
    level[goal[0]][goal[1]] = "g"


def main():
    # python3 bsp.py temp.txt 1-1copy.txt c
    print("BSP", sys.argv[3])
    f = open(LEVEL, "r")
    content = f.read().splitlines()
    f.close()

    f = open(ORIGINAL, "r")
    original_level = f.read().splitlines()
    f.close()

    init = [(0, 0), (len(content) - 1, len(content[0]) - 1)]
    

    bsp(init)

    
    sections.sort()
    bin_original_level = binarify_level(original_level)
    bin_mcts_level = binarify_level(content)
    
    output = []
    for i in range(len(content)):
        output.append([])
        for j in range(len(content[0])):
            output[i].append(".")


    for section in sections:
        pattern = get_level_sect(bin_mcts_level, section)
        if len(pattern) == 0:
            print("zero length pattern at", section, "skipping")
            continue
        
        matches = get_closest_matches(bin_original_level, pattern, original_level)
        new_pattern = choice(matches)

        for i in range(section[0][0], section[1][0] + 1):
            for j in range(section[0][1], section[1][1] + 1):
                output[i][j] = new_pattern[i - section[0][0]][j - section[0][1]]
    
    clean_level(output, content)

    f = open("temp.txt", "w+")
    for i in range(len(output)):
        f.write("".join(output[i]) + "\n")
    f.close()
    
    return

main()