#! /bin/bash

# make a script that:
#   clears all (old) log files
#  runs matlab in text mode and runs an 'm' file
#    that m file should do the opf and save new log files
#  parse both log files and return the result. 

rm rts_*.txt
matlab -nodesktop -nodisplay -nojvm -nosplash -r solve
python parselog.py -t powerflow rts_01.txt
python parselog.py -t optimalpowerflow rts_02.txt

