import sys
from skillLevelGen import concat_files, process_input

ID_TO_SYMBOL = {
    2 : "g",
    4 : "r",
    6 : "k",
    11 : "T",
    14 : "k",
    17 : "-"
}

def place_enemies(file_content, level, meanness):
    death_dict = file_content["death_info"]
    # normalize death counts
    total_deaths = 0
    for key in death_dict:
        for k in death_dict[key]:
            total_deaths += death_dict[key][k]
    
    for key in death_dict:
        for k in death_dict[key]:
            death_dict[key][k] /= total_deaths
    
    curr = 0
    update = True
    selected = []
    # greedily select threats
    while curr < meanness and update:
        update = False
        best_val = -1
        best_pos = (-1, -1)
        best_enemy = -1

        for key in death_dict:
            for k in death_dict[key]:
                comp = death_dict[key][k]
                if curr + comp < meanness and comp > best_val and not k in selected:
                    best_val = comp
                    best_pos = k
                    best_enemy = key
        
        # if we selected an enemy, place it!
        if best_val > -1:
            update = True

            # not a pit
            if best_enemy != 17:
                level[best_pos[1]][best_pos[0]] = ID_TO_SYMBOL[best_enemy]
            # a pit
            else:
                for i in range(15, -1, -1):
                    level[i][best_pos[0]] = "-"
            
            # update the value / selected
            curr += best_val
            selected.append(best_pos)
    
    #print(curr)
    return

def main():
    file_content = None
    # enemies.py level meanness source[1..n]
    if len(sys.argv) == 4:
        file_content = process_input(sys.argv[3])
    elif len(sys.argv) > 4:
        file_content = concat_files(sys.argv[3:])
    else:
        print("Usage: python3 enemies.py levelfile meanness(0-1) source[1..n]")
        return
    
    # grab our file
    f = open(sys.argv[1], "r")
    level = f.read().splitlines()
    f.close()

    # initialize level representation
    for i in range(len(level)):
        r = []
        for c in level[i]: 
            r.append(c) 
        level[i] = r

    # normalize meanness value (input range 0 - 4, output 0 - 1)
    meanness = float((float(sys.argv[2]) - 1) / 4)

    place_enemies(file_content, level, meanness)

    f = open("temp.txt", "w+")
    for i in range(len(level)):
        f.write("".join(level[i]) + "\n")
    f.close()

main()
    