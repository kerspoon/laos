LAOS
====

A program to look at the security of the IEEE RTS 96 using PSAT in Matlab. Python is used to generate the files to test. 

Files
=====

 * **script.py** this is where all the main functionality of the program lies. see the bottom of the file for some examples of how the program can be used.

 * simulation_batch.py - **SimulationBatch** - *batch_file* - batch

 * psat_report.py - **PsatReport** - *report_file* - report

 * psat_data.py - **PsatData** - *psat_file* - psat

 * network_probability.py - **NetworkProbability** - *prob_file* - prob

 * **buslevel.py** a messy utility to get load forecast and load forecast errors. 

 * **misc.py** A few utilities.

 * **parsingutil.py** a few utilities for pyparsing

 * **modifiedtestcase.py** a few utilities for unittest

Classes
=======

    func clean_files          :: ->

    func make_outages         :: NetworkProbability, Int -> SimulationBatch
    func make_failures        :: NetworkProbability, Int -> SimulationBatch

    func read_probabilities   :: Str -> NetworkProbability
    func read_psat            :: Str -> PsatData
    func read_batch           :: Str -> SimulationBatch
    func read_report          :: Str -> PsatReport

    func report_in_limits     :: PsatReport -> Str

    func report_to_psat       :: PsatReport, PsatData -> PsatData
    func text_to_scenario     :: Str -> Scenario
    func scenario_to_psat     :: Scenario, PsatData -> PsatData

    func batch_simulate       :: SimulationBatch, PsatData, Int -> 
    func single_simulate      :: PsatData, Str, Bool -> PsatReport
    func simulate_scenario    :: PsatData, Scenario, Bool -> PsatReport

    func single_matlab_script :: Str, Str, Str -> 
    func batch_matlab_script  :: Str, SimulationBatch -> 
    func simulate             :: Str -> Bool

    class PsatData
      """
      matlab psat data file used in simulations.
      components can be removed to create specific scenarios though
      the recommended way is through the script.py helper
      """
      func read             :: istream(psat_file) -> 
      func write            :: ostream(psat_file) ->
      func remove_bus       :: int(>0) ->
      func remove_line      :: int(>0), int(>0), int(>0) -> 
      func remove_generator :: int(>0), int(>0) -> 
      func set_all_demand   :: real(>0) -> 
      func fix_mismatch     :: ->
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
      func add      :: Scenario ->
      func read     :: istream(batch_file) -> 
      func write    :: ostream(batch_file) ->
      func __iter__ :: -> iter(Scenario)
      class Scenario

    class PsatReport
      """
      Read in a report from psat; check format & sanity check.
      """
      class PowerFlow
      class LineFlow
      func in_limit :: -> Bool
      func read     :: istream(report_file) -> 
      

File Types
==========

psat_file (*.m)
----

Defined in Link 6 (PSAT). 

    Bus.con = [ ... 
      1   138  1  0  2  1;
      24  230  1  0  2  1;
     ];
     
    Line.con = [ ... 
     1   2   100  138  60  0  0   0.0026  0.0139  0.4611 0     0 1.93 0 2    1;
     ];

prob_file (*.net)
----

component probabilities. 

    bus 1 0.025 13 
    bus 2 0.025 13 
    line A1     1  2 .24    16  0.0
    line A2     1  3 .51    10  2.9
    generator G1  1 450   50    U20               
    generator G2  1 450   50    U20           
    crow A12-1 A13-2 0.075
    crow A13-2 A12-1 0.075
    crow A18   A20   0.075

batch_file (*.bch)
----

    [failure32] pf
      remove generator 13
      set all supply 0.86
    [outage0] opf
      remove generator 23
      set all demand 1.0
    [outage1] opf
      remove bus 1
      remove line 13 3
      remove generator 22

matlab_file (*.m)
----

defined by psat manual.

    initpsat;
    Settings.lfmit = 50;
    Settings.violations = 'on'
    runpsat('psat_filename','data');
    runpsat pf;
    runpsat pfrep;
    closepsat;
    exit;

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

 * There might be a way to trip out and modify a system while matlab is running in a way that will be much quicker to run
 * to test the scenario generation probabilities are correct you can use `sort test.bch | grep -v '^\[' | uniq -c > test.csv`

To Try
======

 - Settings.distrsw = 1 % use distributed slack bus
 - Settings.init % status (including PF diverged!)
 - OPF.conv % did the OPF converge
 - OPF.report % not sure but should be checked out
 - clpsat.refresh = 0 % don't bother re-running the PF
 - clpsat.showopf % not sure

