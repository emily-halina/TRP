package agents.MCTS;

import engine.core.MarioAgent;
import engine.core.MarioForwardModel;
import engine.core.MarioTimer;
import engine.helper.MarioActions;
import engine.helper.GameStatus;

import java.util.ArrayList;
import java.lang.Math;
import java.util.Random;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;


/**
 * @author EmilyHalina
 */
public class Agent implements MarioAgent {
    private boolean[] action;
    private int flag = 0;
    private int expands = 1000;
    private ArrayList<Node> roots = new ArrayList<Node>();
    public int markedChildren = 0;
    private ArrayList<Float> xPositions = new ArrayList<Float>();
    private ArrayList<Float> yPositions = new ArrayList<Float>();
    public HashMap<float[], Integer> deaths = new HashMap<float[], Integer>();

    private class Node{
      public boolean[] move; // move from parent to node
      public Node parent;
      public ArrayList<Node> children;
      public double value;
      public int visits;
      public Node next = null;
      public boolean onPath;
      public float xVal;
      public float yVal;

      public Node(boolean[] m, Node p, MarioForwardModel model){
        this.move = m;
        this.parent = p;
        this.children = new ArrayList<Node>();
        this.value = 0;
        this.visits = 0;
        this.onPath = false;

        // track x val
        MarioForwardModel clone = model.clone();
        if (this.move != null){
          clone.advance(this.move); 
        }
        this.xVal = clone.getMarioFloatPos()[0];
        this.yVal = clone.getMarioFloatPos()[1];
      }

      public void addChild(Node c){
        children.add(c);
      }

      public void setOnPath(boolean p){
        onPath = p;
      }

      public boolean getOnPath(){
        return onPath;
      }

      public void setXVal(float x){
        xVal = x;
      }

      public float getXVal(){
        return xVal;
      }

      public void setYVal(float y){
        yVal = y;
      }

      public float getYVal(){
        return yVal;
      }

      public String print(){
        if (this.move == null){
          return "root";
        }
        else{
          return getActionString(this.move);
        }
      }

      public void printTree(){
        print();
        System.out.println();
        for (int i = 0; i < this.children.size(); i++){
          this.children.get(i).print();
        }
        System.out.println();
      }

      public double getValue(int total_expands){
        if (this.visits == 0){
          return 1;
        }
        double C = 0.25;
        // UCB = avg value of visiting node this far + the UCB thing
        return (this.value / this.visits) + C * (Math.sqrt(2 * Math.log(total_expands)) / this.visits);
      }

      public void visit(double update){
        this.value += update;
        this.visits++;
      }

      public boolean hasUnexplored(){
        for (int i = 0; i < this.children.size(); i++){
          if (this.children.get(i).visits == 0){
            return false;
          }
        }
        return true;
      }
    }

    @Override
    public void initialize(MarioForwardModel model, MarioTimer timer) {
        this.action = new boolean[MarioActions.numberOfActions()];
        this.simple = false;
        //this.tree = new AStarTree();
    }

    @Override
    public boolean[] getActions(MarioForwardModel model, MarioTimer timer) {
        xPositions.add(model.getMarioFloatPos()[0]);
        yPositions.add(model.getMarioFloatPos()[1]);
        
        // initialize our MCTS tree
        Node root = null;
        // get our last child
        if (roots.size() != 0){
          root = roots.get(roots.size() - 1);
        }
        // first run
        else{
          root = init(model);
        }
        
        // do the thing
        for (int e = 0; e < expands; e++){
          MarioForwardModel clone = model.clone();

          // selection
          Node leaf = select(clone, root, e);

          // expansion
          Node child = expand(clone, leaf);

          // simulation
          double reward = simulate(clone, child);
          // backprop
          backprop(reward, child);
        }


        // pick out the action with the highest value!
        double max_value = Float.NEGATIVE_INFINITY; // should be bounded by 0, but being safe
        Node best_child = null;
        for (int i = 0; i < root.children.size(); i++){
          double v = root.children.get(i).getValue(expands);
          if (v > max_value){
            best_child = root.children.get(i);
            max_value = v;
          } 
        }

        if (best_child != null){

          // set our chosen fella as "on path"
          best_child.setOnPath(true);
          this.markedChildren++;

          roots.add(best_child);
          MarioForwardModel end_check = model.clone();
          end_check.advance(best_child.move);
          if (end_check.getGameStatus() == GameStatus.WIN || end_check.getGameStatus() == GameStatus.LOSE){
            if (end_check.getGameStatus() == GameStatus.WIN){
              createGraph();
            }
          }
          
          return best_child.move;
        }
        else{
          System.out.println("what the fuck");
        }

        return this.action;
    }

    @Override
    public String getAgentName() {
        return "MCTS";
    }

    public Node init(MarioForwardModel model){
      // initialize root
      Node root = new Node(null, null, model);

      // add all possible moves as initial children of root
      ArrayList<boolean[]> possibleActions = getPossibleActions(model);
      for (int i = 0; i < possibleActions.size(); i++){
        Node child = new Node(possibleActions.get(i), root, model);
        root.addChild(child);
      }
      root.value = 5;
      return root;
    }

    public Node init_exists(Node root, MarioForwardModel model){
      ArrayList<boolean[]> possibleActions = getPossibleActions(model);
      for (int i = 0; i < possibleActions.size(); i++){
        boolean has = false;
        for (int j = 0; j < root.children.size(); j++){
          if (possibleActions.get(i) == root.children.get(j).move){
            has = true;
          }
        }
        if (!has){
          Node child = new Node(possibleActions.get(i), root, model);
          root.addChild(child);
          System.out.println("didn't have a move, adding " + i);
        }
        else{
          System.out.println("had this one " + i);
        }
      }
      return root;
    }

    public Node select(MarioForwardModel clone, Node root, int total_expands){
      // select best possible leaf via UCT
      Node leaf = root;
      // while we still haven't reached a leaf
      while (leaf.children.size() == getPossibleActions(clone).size()){
        double max = Float.NEGATIVE_INFINITY;
        Node chosen = leaf.children.get(0);
        int child = 0;
        for (int i = 0; i < leaf.children.size(); i++){
          if (leaf.children.get(i).getValue(total_expands) > max){
            max = leaf.children.get(i).getValue(total_expands);
            chosen = leaf.children.get(i);
            child = i;
          }
        }
        leaf = chosen;
        clone.advance(leaf.move);
      }
      return leaf;
    }

    public Node expand(MarioForwardModel clone, Node leaf){
      // expand a previously unexpanded child, selected at random
      Random random = new Random();
      ArrayList<boolean[]> possibleActions = getPossibleActions(clone);
      ArrayList<boolean[]> childMoves = new ArrayList<boolean[]>();
      ArrayList<boolean[]> choices = new ArrayList<boolean[]>();

      // get the current child moves
      for (int i = 0; i < leaf.children.size(); i++){
        childMoves.add(leaf.children.get(i).move);
      }

      // collect unexpanded children
      for (int i = 0; i < possibleActions.size(); i++){
        boolean[] hi = possibleActions.get(i);
        boolean found = false;

        // i hate java moment
        for (int j = 0; j < childMoves.size(); j++){
          boolean f = true;
          for (int k = 0; k < 5; k++){
            if (childMoves.get(j)[k] != hi[k]){
              f = false;
            }
          }
          if (f){
            found = true;
          }
        }

        if (!found){
          choices.add(possibleActions.get(i));
        }
      }

      // E X P A N D
      try{
        int choice_ind = random.nextInt(choices.size());
        Node child = new Node(choices.get(choice_ind), leaf, clone);
        leaf.addChild(child);
        clone.advance(choices.get(choice_ind));
        return child;
      }
      catch(IllegalArgumentException e){
        System.out.println("weirdness: no choice, sim a random child node");
        int choice_ind = random.nextInt(childMoves.size());
        Node child = new Node(childMoves.get(choice_ind), leaf, clone);
        clone.advance(childMoves.get(choice_ind));
        return child;
      }
    }

    public double simulate(MarioForwardModel clone, Node child){
      // togelius paper says depth of 6, so i'm placeholding that
      Random random = new Random();
      int ROLLOUT_CAP = 12; // depth of 12 final

      float old_x = clone.getMarioFloatPos()[0];

      for (int i = 0; i < ROLLOUT_CAP; i++){
        // check terminal conditions
        if (clone.getGameStatus() == GameStatus.WIN){
          return 1;
        }
        if (clone.getGameStatus() == GameStatus.LOSE){
          recordDeath(clone);
          return 0;
        }
        // choose a possible action at uniform random
        ArrayList<boolean[]> possibleActions = getPossibleActions(clone);
        int action = random.nextInt(possibleActions.size());
        clone.advance(possibleActions.get(action));
      }

      float new_x = clone.getMarioFloatPos()[0];
      // reward is based on how far mario can run: max reward comes from moving as far
      // to the right as possible!
      double reward = (1.0/2.0) + (1.0/2.0) * ( (new_x - old_x) / (11.0 * (1.0 + ROLLOUT_CAP)) );
      return reward;
    }

    public void recordDeath(MarioForwardModel clone){
      float[] marioPos = clone.getMarioFloatPos();
      // check for fall death
      if (marioPos[1] > 256){
        // making fall = 17 because enemies go up to 16
        float[] deathKey = {17, marioPos[0], marioPos[1]};

        // deaths[deathKey]++;
        if (deaths.containsKey(deathKey)){
          deaths.put(deathKey, deaths.get(deathKey) + 1);
        }
        else{
          deaths.put(deathKey, 1);
        }
      }

      float[] enemies = clone.getEnemiesFloatPos();     
      int closest = -1;
      float closest_dist = Float.POSITIVE_INFINITY;
      for (int j = 0; j < enemies.length; j += 3){
        float x = marioPos[0] - enemies[j + 1];
        float y = marioPos[1] - enemies[j + 2];
        float dist = (x * x) + (y * y);
        if (dist < closest_dist){
          closest = j;
          closest_dist = dist;
        }
      }

      if (closest == -1){
        System.out.println(marioPos[0] + " " + marioPos[1]);
        return;
      }

      float[] deathKey = {enemies[closest], enemies[closest + 1], enemies[closest + 2]};

      if (deaths.containsKey(deathKey)){
        deaths.put(deathKey, deaths.get(deathKey) + 1);
      }
      else{
        deaths.put(deathKey, 1);
      }
      return;
    }

    public void backprop(double reward, Node child){
      while (child.parent != null){
        child.visit(reward);
        child = child.parent;
      }
      return;
    }

    // get the possible actions we can take, as in robinBaumgarten agent
    public static ArrayList<boolean[]> getPossibleActions(MarioForwardModel model){
      // [left right duck jump speed]
      // potentially 24 possible actions, depending on mario's state
      ArrayList<boolean[]> possibleActions = new ArrayList<boolean[]>();
      boolean jump = model.mayMarioJump() || model.getMarioCanJumpHigher();
      boolean crouch = model.getMarioMode() != 0;

      // jumping options
      if (jump){
        possibleActions.add(createAction(false, false, false, true, false)); // j
        possibleActions.add(createAction(false, false, false, true, true)); // js
        possibleActions.add(createAction(true, false, false, true, false)); // lj
        possibleActions.add(createAction(true, false, false, true, true)); // ljs
        possibleActions.add(createAction(false, true, false, true, false)); // rj
        possibleActions.add(createAction(false, true, false, true, true)); // rjs

        // jump crouch options
        if (crouch){
          possibleActions.add(createAction(false, false, true, true, false)); // cj
          possibleActions.add(createAction(false, false, true, true, true)); // cjs
          possibleActions.add(createAction(true, false, true, true, false)); // lcj
          possibleActions.add(createAction(true, false, true, true, true)); // lcjs
          possibleActions.add(createAction(false, true, true, true, false)); // rcj
          possibleActions.add(createAction(false, true, true, true, true)); // rcjs
        }
      }

      // grounded left options
      possibleActions.add(createAction(true, false, false, false, false)); // l
      possibleActions.add(createAction(true, false, false, false, true)); // ls

      // grounded right options
      possibleActions.add(createAction(false, true, false, false, false)); // r
      possibleActions.add(createAction(false, true, false, false, true)); // ls

      // crouching options
      if (crouch){
        possibleActions.add(createAction(false, false, true, false, false)); // c
        possibleActions.add(createAction(true, false, true, false, false)); // lc
        possibleActions.add(createAction(true, false, true, false, true)); // lcs
        possibleActions.add(createAction(false, true, true, false, false)); // rc
        possibleActions.add(createAction(false, true, true, false, true)); // rcs
        possibleActions.add(createAction(false, false, true, false, true)); // cs
      }

      // do nothing lol
      possibleActions.add(createAction(false, false, false, false, false)); // nothing
      possibleActions.add(createAction(false, false, false, false, true)); // s (for fireballs)

      return possibleActions;
    }

    // function from robinBaumgarten A* agent
    public static boolean[] createAction(boolean left, boolean right, boolean down, boolean jump, boolean speed) {
        boolean[] action = new boolean[5];
        action[MarioActions.DOWN.getValue()] = down;
        action[MarioActions.JUMP.getValue()] = jump;
        action[MarioActions.LEFT.getValue()] = left;
        action[MarioActions.RIGHT.getValue()] = right;
        action[MarioActions.SPEED.getValue()] = speed;
        return action;
    }

    public boolean[] simple(MarioForwardModel model, MarioTimer timer){
      // a simple test i wrote: it beats 1-1 by running to the right and jumping
      action = new boolean[MarioActions.numberOfActions()];
      action[4] = model.mayMarioJump();
      if (model.getMarioCanJumpHigher()){
        action[4] = true;
      }
      action[1] = true;
      action[MarioActions.SPEED.getValue()] = true;
      return action;
    }

    // robin agent function
    public static String getActionString(boolean[] action) {
        String s = "";
        if (action[MarioActions.RIGHT.getValue()])
            s += "R";
        if (action[MarioActions.LEFT.getValue()])
            s += "L";
        if (action[MarioActions.SPEED.getValue()])
            s += "S";
        if (action[MarioActions.JUMP.getValue()])
            s += "J";
        if (action[MarioActions.DOWN.getValue()])
            s += "D";
        if (s.length() == 0) {
            s = "[NONE]";
        }
        s += " ";
        return s;
    }

    public void createGraph(){
      
      // link up the tree!
      Node root = roots.get(0);
      for (int i = 0; i < roots.size() - 1; i++){
        Node parent = roots.get(i);
        Node child = roots.get(i + 1);
        int assigned = 0;
        for (int j = 0; j < parent.children.size(); j++){
          if (parent.children.get(j).move == child.move){
            parent.children.set(j, child);
            parent.next = child;
            assigned++;
          }
        }
        if (assigned != 1){
          System.out.println("wtf we assigned " + assigned + " times");
        }
      }
      
      Node curr = roots.get(0);
      int count = 0;

      while (curr != null){
        curr = curr.next;
        count++;
      }

      // write the graph to a file for Perusal
      try{
            FileWriter m = new FileWriter("source5.txt");
            m.write(roots.size() + "\n");
            System.out.print(roots.size() + "\n");

            for (int i = 0; i < roots.size(); i++){
              m.write(roots.get(i).print() + " ");
              System.out.print(roots.get(i).print() + " ");
            }

            m.write("\n");
            System.out.println();

            for (int i = 0; i < roots.size(); i++){
              m.write(roots.get(i).getXVal() + " ");
              System.out.print(roots.get(i).getXVal() + " ");
            }

            m.write("\n");
            System.out.println();

            for (int i = 0; i < roots.size(); i++){
              m.write(roots.get(i).getYVal() + " ");
              System.out.print(roots.get(i).getYVal() + " ");
            }

            m.write("\n");
            System.out.println();

            m.write("size " + roots.size() * expands);
            System.out.println("size " + roots.size() * expands);
            m.write("\n");

            // adding in enemy information
            ArrayList<ArrayList<float[]>> deathInfo = outputDeathInfo();
            for (int i = 0; i < deathInfo.size(); i++){
              ArrayList<float[]> enemy = deathInfo.get(i);
              m.write(String.valueOf(i + 1)); // i hate java moment
              m.write(": ");
              for (int j = 0; j < enemy.size(); j++){
                float[] stats = enemy.get(j);
                m.write((int)stats[0] + " " + stats[1] + " " + stats[2] + " ");
              }
              m.write("\n");
            }

            m.close();
          }
          catch (IOException e){
            System.out.println("ewwow"); // why am i like this
          }
      
      System.out.println("the length of the tree is " + count);
      return;
    }

    public ArrayList<ArrayList<float[]>> outputDeathInfo(){
      // output is in the deaths[enemy_id - 1] = list of [death_count, x, y]
      ArrayList<ArrayList<float[]>> ret = new ArrayList<ArrayList<float[]>>();
      for (int i = 0; i < 17; i++){
        ret.add(new ArrayList<float[]>());
      }

      for (float[] key : deaths.keySet()){
        int enemy_id = (int)key[0] - 1;
        float x = key[1];
        float y = key[2];

        ArrayList<float[]> bucket = ret.get(enemy_id);
        boolean added = false;
        for (int i = 0; i < bucket.size(); i++){
          if (bucket.get(i)[1] == x && bucket.get(i)[2] == y){
            bucket.get(i)[0] += deaths.get(key);
            added = true;
          }
        }

        if (!added){
          float[] new_key = {deaths.get(key), x, y};
          bucket.add(new_key);
        }
      }
      return ret;
    }

    // SOME EXTRA STUFF DOWN HERE 
    public class Skill{
      public ArrayList<String> moveSequence;
      public ArrayList<Integer> indSequence;
      public ArrayList<Float> XSequence;
      public ArrayList<Float> YSequence;
      public int startInd;
      public boolean onPath;
      public float x1;
      public float x2;
      public int SKILL_LEN = 12;

      public Skill(int s){
        moveSequence = new ArrayList<String>();
        indSequence = new ArrayList<Integer>();
        XSequence = new ArrayList<Float>();
        YSequence = new ArrayList<Float>();
        startInd = s;
        onPath = true;
        x1 = x2 = -1;
      }

      public int getLen() {
        if (indSequence.size() != moveSequence.size()){
          System.out.println("sizes don't match what the fuck");
        }
        return indSequence.size(); 
      }

      public int getStartInd(){
        return startInd;
      }

      public ArrayList<String> getMoveSequence() { return moveSequence; }

      public ArrayList<Integer> getIndSequence() { return indSequence; }

      public ArrayList<Float> getXSequence() { return XSequence; }
      
      public ArrayList<Float> getYSequence() { return YSequence; }


      public String getMoveString(){
        String r = "";
        for (int i = 0; i < moveSequence.size(); i++){
          r += moveSequence.get(i);
          if (i != moveSequence.size() - 1){
            r += " ";
          }
        }
        return r;
      }

      public void addMove(Node m, int i){
        moveSequence.add(getActionString(m.move));

        if (moveSequence.size() == 1){
          x1 = m.getXVal();
          //x1 = 5;
        }

        else if (moveSequence.size() == SKILL_LEN){
          x2 = m.getXVal();
        }

        XSequence.add(m.getXVal());
        YSequence.add(m.getYVal());

        indSequence.add(i);
        if (!m.getOnPath()){
          onPath = false;
        }
      }

      public Skill getClone(){
        Skill clone = new Skill(startInd);
        for (int i = 0; i < getLen(); i++){
          clone.moveSequence.add(moveSequence.get(i));
          clone.indSequence.add(indSequence.get(i));
          clone.XSequence.add(XSequence.get(i));
          clone.YSequence.add(YSequence.get(i));
        }
        clone.onPath = onPath;
        clone.x1 = x1;
        clone.x2 = x2;
        return clone;
      }

      public boolean getOnPath(){
        return onPath;
      }

      public float getXDiff(){
        return x2 - x1;
      }

      public float getX1(){
        return x1;
      }

      public float getX2(){
        return x2;
      }
    }

    public void getSkills(){
      int SKILL_LEN = 12;
      // for root in possible children, find all skills with length skill len
      ArrayList<Skill> skills = new ArrayList<Skill>();
      for (int i = 0; i < roots.size(); i++){
        Node root = roots.get(i);
        Skill skill = new Skill(i);
        // TODO: make sure that the ind path is correct
        recurseSkillsFromRoot(root, skill, SKILL_LEN, 0, skills);
        // for (int j = 0; j < root.children.size(); j++){
        //   Skill skill = new Skill(i);
        // }
        System.out.println("Size of skills after " + i + " is " + skills.size());
      }

      analyzeSkills(skills, SKILL_LEN);
      
      return;
    }

    public void recurseSkillsFromRoot(Node root, Skill skill, int depth, int index, ArrayList<Skill> skills){

      // add ourselves to the skill
      skill.addMove(root, index);

      // base case: skill is complete, -> depth is 1. if it is, add to our master list
      if (depth == 1){
        skills.add(skill);
        return;
      }

      // base case: root is a leaf
      if (root.children.size() == 0){
        return;
      }

      // otherwise, recurse on all children, making deep copy
      for (int i = 0; i < root.children.size(); i++){
        Skill s = skill.getClone();
        recurseSkillsFromRoot(root.children.get(i), s, depth - 1, i, skills);
      }
    }

    public void analyzeSkills(ArrayList<Skill> skills, int SKILL_LEN){
      HashMap<String, Integer> counts = new HashMap<String, Integer>();
      HashMap<String, Integer> onPathCounts = new HashMap<String, Integer>();

      int on = 0;
      int timestep = 0;
      for (int i = 0; i < skills.size(); i++){
        Skill s = skills.get(i);
        String key = s.getMoveString();

        // sanity check
        if (s.getLen() != SKILL_LEN){
          System.out.println("what the fuck " + s.getLen());
        }

        // count on-path skill frequencies
        if (s.getOnPath()){
          System.out.println("Skill " + s.getMoveString() + " at timestep " + s.getStartInd() + " is on path, XDiff " + s.getXDiff() + " X1, X2 " + s.getX1() + "," + s.getX2());
          on++;
          if (onPathCounts.containsKey(key)){
            onPathCounts.put(key, onPathCounts.get(key) + 1);
          }

          else{
            onPathCounts.put(key, 1);
          }
        }

        // count skill frequencies
        if (counts.containsKey(key)){
          counts.put(key, counts.get(key) + 1);
        }
        else{
          counts.put(key, 1);
        }
      }

      int max = 0;
      String maxKey = "";
      for (String key : counts.keySet()){
        if (counts.get(key) > max){
          max = counts.get(key);
          maxKey = key;
        }
       //System.out.println("Skill: " + key + " Count: " + counts.get(key));
      }

      int omax = 0;
      String omaxKey = "";
      for (String key : onPathCounts.keySet()){
        if (onPathCounts.get(key) > omax){
          omax = onPathCounts.get(key);
          omaxKey = key;
        }
      }

      System.out.println("There are " + counts.keySet().size() + " unique skills");
      System.out.println("Most common skill was " + maxKey + " with " + max + " appearances");
      

      // on path skill frequency (most common skill on the path)
      System.out.println("There are " + on + " on path skills");
      System.out.println("Most common on path skill was " + omaxKey + " with " + omax + " appearances");

      roadblockAnalysis(skills, SKILL_LEN);
      return;
    }

    void roadblockAnalysis(ArrayList<Skill> skills, int SKILL_LEN){
      int ROADBLOCK_THRESHOLD = 10; // xdiff at which threshold is overcame

      HashMap<Integer, Float> maxVals = new HashMap<Integer, Float>();
      HashMap<Integer, Float> secondMaxVals = new HashMap<Integer, Float>();
      HashMap<Integer, Skill> maxSkillAtTime = new HashMap<Integer, Skill>();

      for (int i = 0; i < skills.size(); i++){
        Skill s = skills.get(i);
        int startInd = s.getStartInd();
        if (maxVals.containsKey(startInd)){
          if (maxVals.get(startInd) < s.getXDiff()){
            // update values
            secondMaxVals.put(startInd, maxVals.get(startInd));
            maxVals.put(startInd, s.getXDiff());
            maxSkillAtTime.put(startInd, s);
          }
        }
        else{
          maxVals.put(startInd, s.getXDiff());
          secondMaxVals.put(startInd, s.getXDiff());
          maxSkillAtTime.put(startInd, s);
        }
      }

      float min_diff = 100;
      int max_key = -1;
      for (int key : maxVals.keySet()){
        // avg skill bucketing
        float result = 0;
        boolean valid = true;
        for (int i = 0; i < SKILL_LEN; i++){
          if (maxVals.containsKey(key - i) && secondMaxVals.containsKey(key - i)){
            result += maxVals.get(key - i) - secondMaxVals.get(key - i);
          }
          else{
            valid = false;
          }
        }
        if (valid){
          result = result / (float)SKILL_LEN;
        
          if (result < min_diff){
            min_diff = result;
            max_key = key;
          }
        }
        else{
          System.out.println("key " + key + " is not valid. maxVals contains " + maxVals.containsKey(key) + " secondMaxVals contains " + secondMaxVals.containsKey(key));
        }
        
        //System.out.println(result);
        
      }

      System.out.println("the min diff was " + min_diff + " from skill: " + maxSkillAtTime.get(max_key).getMoveString() + " at timestep " + max_key);

      float baselineXDiff = maxSkillAtTime.get(max_key).getXDiff();
      Skill selectedSkill = null;
      float selectedValue = 0;
      boolean selected = false;

      for (int i = 0; i < 300; i++){
        float result = 0;
        boolean valid = true;
        for (int j = 0; j < SKILL_LEN; j++){
          if (maxVals.containsKey(max_key + i - j) && secondMaxVals.containsKey(max_key + i - j)){
            result += maxVals.get(max_key + i - j) - secondMaxVals.get(max_key + i - j);
          }
          else{
            valid = false;
          }
        }
        result = result / (float)SKILL_LEN;

        if (valid){
          Skill maxSkill = maxSkillAtTime.get(max_key + i);
          if (!selected && maxSkill.getXDiff() - baselineXDiff >= ROADBLOCK_THRESHOLD){
            selectedSkill = maxSkill;
            selected = true;
            selectedValue = result;
          }
          System.out.println("key " + (max_key + i) + " value " + result + " skill " + maxSkill.getMoveString() + " x1 " + maxSkill.getX1() + " x2 " + maxSkill.getX2() + " xdiff " + maxSkill.getXDiff());
        }
        else{
          System.out.println("key " + (max_key + i) + " was invalid");
        }
        
      }

      if (selected){
          System.out.println("SELECTED SKILL key " + selectedSkill.getStartInd() + " value " + selectedValue + " skill " + selectedSkill.getMoveString() + " x1 " + selectedSkill.getX1() + " x2 " + selectedSkill.getX2() + " xdiff " + selectedSkill.getXDiff());
          ArrayList<Float> xSeq = selectedSkill.getXSequence();
          ArrayList<Float> ySeq = selectedSkill.getYSequence();
          for (int i = 0; i < xSeq.size(); i++){
            System.out.println(xSeq.get(i) + " " + ySeq.get(i));
          }
        }
      
      //getSkillBucket(selectedSkill, skills, SKILL_LEN);
    }

    void getSkillBucket(Skill key, ArrayList<Skill> skills, int SKILL_LEN){
      ArrayList<Skill> bucket = new ArrayList<Skill>();
      ArrayList<String> keyMoveSeq = key.getMoveSequence();

      int SIMILARITY_THRESHOLD = 8;
      for (int i = 0; i < skills.size(); i++){
        Skill curr = skills.get(i);
        ArrayList<String> currMoveSeq = curr.getMoveSequence();
        int maxSubSimilarity = 0;
        int diff = 0;

        // count the maximum substring similarity!
        for (int j = 0; j < SKILL_LEN; j++){
          if (currMoveSeq.get(j) == keyMoveSeq.get(j)){
            diff++;
            maxSubSimilarity = Math.max(maxSubSimilarity, diff);
          }
          else{
            diff = 0;
          }
        }
        if (maxSubSimilarity >= SIMILARITY_THRESHOLD){
          bucket.add(curr);
        }
      }

      System.out.println("bucket size: " + bucket.size());
      System.out.println("skills similar to " + key.getMoveString());
      for (int i = 0; i < bucket.size(); i++){
        System.out.println(bucket.get(i).getMoveString());
      }

    }

}
