# TRP
Tree-based Reconstructive Partitioning (TRP) is a Procedural Content Generation via Machine Learning (PCGML) approach for level generation.

On a high level, TRP uses a Monte Carlo Tree Search to play through a game's level, then records the search tree information. We then use that search tree information to generate new levels. TRP can work with as little as a single level example and playthrough, making it ideal for low-data domains.

This repository contains an implementation of TRP for the [Mario AI Framework](https://github.com/amidos2006/Mario-AI-Framework) and [GVGAI Zelda](https://github.com/rubenrtorrado/GVGAI_GYM) environments.

Additional details on how TRP works and an evaluation of the approach against 6 PCG baselines can be found in "Tree-based Reconstructive Partitioning: A Novel Low-Data Level Generation Approach", a conference paper at [AIIDE 2023](https://sites.google.com/view/aiide-2023/home). If you use this work in any capacity in a research project or publication, please include the following citation.

```
citation info soon to come!
```

# Generated Examples

Examples of generated levels can be found in the output/example-levels folder for both Mario and GVGAI Zelda. The "fixed" folder contains levels all generated with the same parameters, and "variable" contains levels generated with different parameters per level. The parameters used are in the filenames, and the details of the parameters are discussed in the paper.

# Generating Levels based on Existing Playthroughs

To generate new levels based on existing playthroughs, run the gen_level.sh script in the corresponding domain's folder. This will generate a new level in a file named out.txt in the output folder.

You can tweak the parameters / number of source files used for generation at the top of the gen_level.sh script.

# Creating New Playthrough Information

To collect new playthrough data, you will need to download the respective environment for each domain and run the provided MCTS script. In both cases, the MCTS script should be used as the "agent" playing the level. It will automatically collect data as it plays, and save it at the end of the stage.