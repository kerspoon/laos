
LAOS
====

A program to look at the security of the IEEE RTS 96 using PSAT in Matlab. Python is used to generate the files to test. 

batch.py 
--------

This creates batch files from a Monte Carlo sample of failure probabilities. It can either show outages or failures within the next 1h period. The batch files say which components have changed power input/output and which are on outage / failed.  

main.py
-------

This takes a batch file and a PSAT data file and runs each scenario in Matlab/PSAT using the data file as a base. The results are stored as another batch file where each scenario has the results of pass or fail appended.

psat.py
-------

Almost everything is in here. It should be separated. 

parselog.py
-----------

This takes the report from a Matlab/PSAT loadflow and converts it into a pass/fail result. It's currently very buggy.

misc.py
-------

A few utilities.


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

Classes
=======

    class NetworkData
      """
      matlab psat data file used in simulations.
      components can be removed to create specific scenarios though
      the recommended way is through the 'write_scenario' func.
      """
      func read             :: istream(psatfile) -> 
      func write            :: ostream(psatfile) ->
      func remove_bus       :: int(>0) ->
      func remove_line      :: int(>0), int(>0), Either(None, int(>0)) -> 
      func remove_generator :: int(>0), Either(None, int(>0)) -> 
      class Bus
      class Line
      class Slack
      class Generator
      class Load
      class Shunt 
      class Demand 
      class Supply
    
    class NetworkProbability
      """
      the Monte Carlo sampler, it creates
      scenarios from a network probability data file. 
      """
      func read     :: istream(netfile) -> 
      func write    :: ostream(netfile) ->
      func outages  :: str -> Scenario
      func failures :: str -> Scenario
      class Bus
      class Generator
      class Line
      class Crow
      
    class SimulationBatch
      """
      manager for a set of Scenario instances, called a batch file.
      Scenario are a structure for holding changes to a network
      such as the loss of a components or change in power.
      """
      func read     :: istream(netfile) -> 
      func write    :: ostream(netfile) ->
      func __iter__ :: -> iter(Scenario)
      class Scenario

    func write_scenario :: ostream, Scenario, NetworkData -> 
    """
    take a Scenario and NetworkData, combine to make a 
    new NetworkData which gets written to a ostream.
    """

Testing Batch.py
================

The idea is to run it many times and see if the results match the input probabilities.

    /home/james/laos $ python batch.py -o rts.batch -i 100000 rts.net
    /home/james/laos $ sort test.batch | grep -v '^\[' | uniq -c > test_res.batch

Running 

    /home/james/laos $ python batch.py -t failures -o rts.batch -i 100000 rts.net
    /home/james/laos $ python main.py rts.m rts.batch -o rts.res
