#! /bin/bash

# make a script that:
#   clears all (old) log files
# runs matlab in text mode and runs an 'm' file
#   that m file should do the opf and save new log files
# parse both log files and return the result. 

# if you are changing this then change it in 'solve.m' too
filename="test1234"

rmfiles=${filename}_*.txt
file1=${filename}_01.txt
file2=${filename}_02.txt

echo $rmfiles
echo $file1 
echo $file2 

rm -f $rmfiles
matlab -nodesktop -nodisplay -nojvm -nosplash -r solve
python parselog.py -t powerflow $file1
python parselog.py -t optimalpowerflow $file2

exit 0 

# if [ eq $# 1 ]; then
#     filename=$1
# else
#     filename="rts"
# fi