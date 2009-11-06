
LAOS
====

A program to look at the security of the IEEE RTS 96 using PSAT in Matlab. Python is used to generate the files to test. 

Todo
====

 1. make a script to run opf on a given file from the command line
 2. from a solved opf, say whether it is an 'acceptable system'
 3. make a program with the following:

      - Delete a line
      - Delete a bus
      - Delete a generator
      - Change generator power
      - Change demand power   

 4. combine with the Monte Carlo scenario generator
 5. add the ability to SCOPF using N-1

* * * * *

Notes
=====

 - Settings.distrsw = 1 % use distributed slack bus
 - Settings.init % status (including PF diverged!)
 - OPF.conv % did the OPF converge
 - OPF.report % not sure but should be checked out
 - clpsat.refresh = 0 % don't bother re-running the PF
 - clpsat.showopf % not sure


