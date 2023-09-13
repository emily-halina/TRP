#!/bin/bash
S=3
E=2

python3 scripts/cavernous.py levels/original_lvl1.txt source/level1/loglvl1-1.txt source/level1/loglvl1-2.txt
python3 scripts/bsp.py temp.txt levels/original_lvl1.txt $S
cp temp.txt tempb.txt
python3 scripts/enemies.py tempb.txt $E source/level1/loglvl1-1.txt source/level1/loglvl1-2.txt
cp temp.txt output/out.txt

rm temp.txt
rm tempb.txt