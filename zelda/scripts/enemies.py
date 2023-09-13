import sys

ID_TO_SYMBOL = {
    2 : "2",
    3 : "3"
}

def process_input(filename):
    f = open(filename, "r")
    content = f.read().splitlines()
    f.close()

    file_content = {}
    file_content["death_info"] = {}

    two = content[2]
    three = content[3]

    two = two.split(" ")
    file_content["death_info"][2] = {}
    for i in range(1, len(two) - 2, 3):
        x = int(two[i])
        y = int(two[i + 1])
        count = int(two[i + 2])
        file_content["death_info"][2][(x, y)] = count
    
    three = three.split(" ")
    file_content["death_info"][3] = {}
    for i in range(1, len(three) - 2, 3):
        x = int(three[i])
        y = int(three[i + 1])
        count = int(three[i + 2])
        file_content["death_info"][3][(x, y)] = count

    return file_content

def concat_files(filenames):
    content = {}
    content["death_info"] = {}
    content["death_info"][2] = {}
    content["death_info"][3] = {}

    for f in filenames:
        file_content = process_input(f)
        for key in file_content["death_info"]:
            for pos in file_content["death_info"][key]:
                if pos in content["death_info"][key]:
                    content["death_info"][key][pos] += file_content["death_info"][key][pos]
                else:
                    content["death_info"][key][pos] = file_content["death_info"][key][pos]
    
    return content
                        


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

            level[best_pos[0]][best_pos[1]] = ID_TO_SYMBOL[best_enemy]
            
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

    # normalize meanness value (input range 0 - 8, output 0 - 1)
    meanness = float((float(sys.argv[2]) - 1) / 8)

    place_enemies(file_content, level, meanness)

    f = open("temp.txt", "w+")
    for i in range(len(level)):
        f.write("".join(level[i]) + "\n")
    f.close()

main()
    