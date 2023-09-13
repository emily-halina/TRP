#!/bin/bash
S=12 #size of the binary space parition segments
E=2 #density of the enemies, (0 - 4), where 4 is all the enemies and 0 is none

python3 scripts/skillLevelGen.py source/1-1/source1.txt
python3 scripts/bsp.py temp.txt levels/1-1copy.txt $S
cp temp.txt tempb.txt
python3 scripts/enemies.py temp.txt $E source/1-1/source1.txt
cp temp.txt output/out.txt

rm temp.txt
rm tempb.txt