
LAOS
====

A program to look at the security of the IEEE RTS 96 using PSAT in Matlab. Python is used to generate the files to test. 

A program called kiribati makes a batch file containing a list of scenarios to simulate.
this is read by laos which will call matlab with a script to perform the desired simulation. The results are parsed by logparser.py

Links
=====

 1. [http://psdyn.ece.wisc.edu/IEEE_benchmarks/index.htm](University of Wisconsin) 
     * 9 Bus System
     * IEEE 39 Bus System
     * Simplified 14-Generator Australian Power System
     * (including full dynamic models)
 2. [http://www.ee.washington.edu/research/pstca/](University of Washington Power Systems Test Case Archive)
     * Power Flow Test Cases (No. buses: 14, 30, 57, 118, 300)
     * Dynamic Test Cases (17 Gen, 30 Bus "New England", 50 Generator)
     * IEEE-RTS-96
 3. [http://www.mathworks.com/access/helpdesk/help/toolbox/physmod/powersys](Matlab SimPowerSystems)
 4. [http://rwl.github.com/pylon/](Pylon)
 5. [http://www.pserc.cornell.edu/matpower/](Matpower)
 6. [http://www.power.uwaterloo.ca/~fmilano/psat.htm](PSAT)

* * * * *

Notes
=====

 * It seems like a waste to start up and shut down matlab for every simulation.
 * There might be a way to trip out and modify a system while matlab is running in a way that will be much quicker to run

To Try
======

 - Settings.distrsw = 1 % use distributed slack bus
 - Settings.init % status (including PF diverged!)
 - OPF.conv % did the OPF converge
 - OPF.report % not sure but should be checked out
 - clpsat.refresh = 0 % don't bother re-running the PF
 - clpsat.showopf % not sure
