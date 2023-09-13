import gym
from random import choice, randint
from math import sqrt, log

EPS = 0.00000000000001

class Node:
    def __init__(self, state, move, parent=None):
        self.state = state
        self.value = 0
        self.visits = 0
        self.move = move

        self.parent = parent
        self.children = []
    
    def visit(self, value):
        self.value += value
        self.visits += 1
    
    def get_value(self):
        # explore
        if self.visits == 0:
            return 0.75
        # exploit (UCB)
        C = 0.25
        # UCB = avg value of visiting node this far + ratio of parent visits to self visits (weighted)
        return (self.value / self.visits) + C * (sqrt(2 * log(self.get_parent().get_visits() + 1)) / self.visits);

    def set_state(self, state):
        self.state = state
    
    def get_state(self):
        return self.state
    
    def set_move(self, move):
        self.move = move
    
    def get_move(self):
        return self.move

    def add_child(self, child):
        self.children.append(child)
        return

    def get_children(self):
        return self.children
    
    def get_parent(self):
        return self.parent
    
    def get_visits(self):
        return self.visits

    def get_raw_value(self):
        return self.value
    

class MCTS:
    def __init__(self, level):
        # MCTS params / variables
        self.expands = 100
        self.rollout_length = 3
        self.tree = []
        self.reward_compare = 0
        self.key_reward_table = {}
        self.goal_reward_table = {}
        self.init = True
        
        # gvgai jank specific stuff
        self.level_path = "gym_gvgai/envs/games/zelda_v0/zelda_" + level[:-3] + ".txt"
        self.level = level
        self.env = gym.make("gvgai-zelda-" + self.level)
        self.init_state = None

        # logging information for level gen
        self.deaths = {}
        self.X = []
        self.Y = []

        return
    
    def get_action(self, state, last_move):
        # first, write the current state to file so we can reset to it (forward model jank)
        text_state = self.pixel_to_text(state)
        self.save_to_file(text_state)

        # set up reward function
        if self.init:
            self.init_state = text_state
            key = None
            goal = None
            for i in range(9):
                for j in range(13):
                    if text_state[i][j] == "+":
                        key = (i, j)
                    if text_state[i][j] == "g":
                        goal = (i, j)

            self.gen_reward_table(self.key_reward_table, text_state, key, 0)
            self.gen_reward_table(self.goal_reward_table, text_state, goal, 0)
            for i in range(9):
                for j in range(13):
                    if (i, j) in self.key_reward_table:
                        print(self.key_reward_table[(i, j)], end=" ")
                    else:
                        print("X", end=" ")
                print()
            for i in range(9):
                for j in range(13):
                    if (i, j) in self.goal_reward_table:
                        print(self.goal_reward_table[(i, j)], end=" ")
                    else:
                        print("X", end=" ")
                print()
            self.init = False


        self.reward_compare = 0
        self.reward_compare = self.reward(text_state)


        # grab our root, either a new node or the last appended value in our tree
        #root = Node(text_state, None)
        if len(self.tree) == 0:   
            root = Node(text_state, None)
        else:
            root = self.tree[-1]
            root.set_state(text_state) # update state for minor diffs (stochastic env)

        

        for e in range(self.expands):
            self.env.reset()
            leaf = self.select(root)
            child_act = self.expand(leaf)
            reward, child = self.simulate(leaf, child_act, last_move)
            self.backprop(child, reward)
            
        
        # select our best action
        best_val = -2.0
        best_child = None
        values = []
        visits = []
        moves = []
        raw_values = []
        for c in root.get_children():
            val = c.get_value()
            values.append(val)
            visits.append(c.get_visits())
            moves.append(c.get_move())
            raw_values.append(c.get_raw_value())
            if val > best_val + EPS:
                best_val = val
                best_child = c

        print("raw values", raw_values)
        print("values", values)
        print("visits", visits)
        print("moves", moves)
        
        # book-keeping
        self.tree.append(best_child)
        self.save_to_file(self.init_state)

        player = self.player_position(text_state)
        self.X.append(str(player[0]))
        self.Y.append(str(player[1]))
        
        self.write_log_file()
        return best_child.get_move()
    
    def select(self, root):
        NUM_ACTIONS = 6
        leaf = root

        # traverse until we reach a leaf node
        # NOTE: maybe an issue with expanding a state that proceeds to take an L, check for this 
        while len(leaf.get_children()) == NUM_ACTIONS:
            m_val = -5000
            m_child = None
            for c in leaf.get_children():
                val = c.get_value()
                if val > m_val:
                    m_child = c
                    m_val = val
            
            leaf = m_child
            self.env.step(leaf.get_move())

        return leaf

    def expand(self, leaf):
        NUM_ACTIONS = 6
        children = leaf.get_children()
        possible = []

        # choose a child which has not been expanded yet
        for i in range(NUM_ACTIONS):
            add = True
            for c in children:
                if c.get_move() == i:
                    add = False
            if add:
                possible.append(i)
        
        # return our new child's action (we'll make the tree's node in simulate)
        child_act = choice(possible)
        return child_act

    def simulate(self, leaf, child_act, last_move):
        #print('blop')
        # do the simulation 
        stateObs, _, done, _ = self.env.step(child_act)
        # double move
        if child_act not in [0, 1] and child_act != last_move:
            stateObs, _, done, _ = self.env.step(child_act)
            last_move = child_act
        
        child_state = self.pixel_to_text(stateObs)
        child = Node(child_state, child_act, leaf)
        leaf.add_child(child)

        #print("rolllllout start")
        player = None
        last_player = None
        last_player = self.player_position(child_state)

        for i in range(self.rollout_length):
            # death tracking: keep track of the closest enemy and player position
            player = self.player_position(child_state)
            
            # random rollout
            rand_move = randint(0, 5)
            stateObs, _, done, _ = self.env.step(rand_move)
            # double move
            if rand_move not in [0, 1] and rand_move != last_move and last_move != 1:
                stateObs, _, done, _ = self.env.step(rand_move)
                last_move = child_act
            
            child_state = self.pixel_to_text(stateObs)
            # check terminal conditions
            if done:
                # negative terminal: there is no player
                negative = True
                for row in child_state:
                    if "A" in row:
                        negative = False
                
                # otherwise, we win!
                if negative:
                    print("death encountered!!! rollout")
                    # locate the nearest lad :3
                    min_dist = 1000
                    enemy = None
                    if last_player != None:
                        for k in range(9):
                            for l in range(13):
                                if child_state[k][l] in ["1", "2", "3"]:
                                    dist = abs(last_player[0] - k) + abs(last_player[1] - l)
                                    if dist < min_dist:
                                        min_dist = dist
                                        enemy = (child_state[k][l], (k, l))
                        self.log_death(enemy)
                    else:
                        print("last player is None")

                    # put the fear of death in this agent's heart.
                    return self.reward(child_state), child
                else:
                    print("victory?")
                    continue
                    #return self.reward(child_state), child
                
                last_player = player
        
        # if we've reached the end of our rollouts, use our reward function with current state
        end_state = self.pixel_to_text(stateObs)
        return self.reward(end_state), child

    def backprop(self, child, reward):
        curr = child
        while curr.get_parent():
            curr.visit(reward)
            curr = curr.get_parent()
        return

    def reward(self, text_state):
        # can try a few different reward functions, going to start with manhatten distance to key/goal!
        key = None
        player = None
        goal = None
        for i in range(len(text_state)):
            for j in range(len(text_state[0])):
                if text_state[i][j] == "A":
                    player = (i, j)
                elif text_state[i][j] == "+":
                    key = (i, j)
                elif text_state[i][j] == "g":
                    goal = (i, j)
        
        # no player, we dead
        if not player:
            print("death encountered!!! reward func")
            return -1
        
        # if the key exists, it's our goal
        if key:
            #print("key is current goal", key)
            return (16 - (self.key_reward_table[player] + 1)) / 32.0
            #return (1.0 / (abs(player[0] - key[0]) + abs(player[1] - key[1]) + 1)) - self.reward_compare 

        # we have the key, so goal is our goal
        #print("goal is current goal")         
        return (32 - (self.goal_reward_table[player] + 1)) / 32.0
        

    def log_death(self, enemy):
        # enemy of the form (enemy_id, (x, y))
        if enemy in self.deaths:
            self.deaths[enemy] += 1
        else:
            self.deaths[enemy] = 1
    
    def write_log_file(self):
        f = open("log" + self.level[:-3] + ".txt", "w+")
        f.write(" ".join(self.X) + "\n")
        f.write(" ".join(self.Y) + "\n")
        
        bucket2 = []
        bucket3 = []
        for death in self.deaths:
            death_info = (str(death[1][0]), str(death[1][1]), str(self.deaths[death]))
            if death[0] == "2":
                bucket2.append(death_info)
            else:
                bucket3.append(death_info)
        
        f.write("2: ")
        for death_info in bucket2:
            f.write(" ".join(death_info) + " ")
        f.write("\n")

        f.write("3: ")
        for death_info in bucket3:
            f.write(" ".join(death_info) + " ")
        f.write("\n")
        f.close()

    def gen_reward_table(self, reward_table, state, current, value):
        # recursively floodfill our rewards
        i, j = current[0], current[1]
        if current in reward_table and reward_table[current] <= value:
            return
        
        reward_table[current] = value

        for k in [-1, 0, 1]:
            for l in [-1, 0, 1]:
                if i + k < 9 and j + l < 13 and state[i + k][j + l] != "w" and k != l:
                    self.gen_reward_table(reward_table, state, (i + k, j + l), value + 1)
        
    def pixel_to_text(self, state):
        text_rep = []
        for i in range(9):
            text_rep.append([])
            for j in range(13):
                th = i*10 + 5
                tw = j*10 + 5

                # rgb and colour codes
                rgb = (state[th][tw][0], state[th][tw][1], state[th][tw][2])
                PLAYER = 201
                WALL = 153
                WALL2 = 110
                ONE = 38
                TWO = 61
                THREE = 32
                GOAL = (87, 71)
                KEY = 30
                
                # switch case based on different tiles
                t = "."
                if rgb[2] == PLAYER or rgb[2] == ONE:
                    t = "A"
                elif rgb[2] == WALL or rgb[2] == WALL2:
                    t = "w"
                elif rgb[2] == ONE:
                    t = "1"
                elif rgb[2] == TWO:
                    t = "2"
                elif rgb[2] == THREE:
                    t = "3"
                elif rgb[0] == GOAL[0] and rgb[1] == GOAL[1]:
                    t = "g"
                elif rgb[2] == KEY:
                    t = "+"
                text_rep[i].append(t)
        
        # cut my life into pieces
        return text_rep
    
    def player_position(self, text_state):
        for i in range(9):
            for j in range(13):
                if text_state[i][j] == "A":
                    return (i, j)
        return None

    def save_to_file(self, text_state):
        f = open(self.level_path, "w")
        for l in text_state:
            f.writelines(l)
            f.write("\n")
        f.close()
        pass
    

