
--------------------------------------------------------------------------------

private func write_section :: Stream -> Dict 'items' -> Str 'title' -> None
    """
    Write out one section of the Psat Data to the stream.
    """ 

private func read_section  :: Stream -> x 'classtype' -> [x]
    """
    Read one section of Matlab file, assuming the header is done.
    and assuming that each line is one row ended by a semicolon. 
    """

private func fix_mismatch :: Real 'mismatch' -> [Real] 'gen_power' -> 
                             [Real] 'gen_limit' -> [Real] 'new_gen_power'
    """
    Change the total generated power by `mismatch`. This is
    to simulate, in a very crude way, how generators will pick up 
    power through droop, governors or AVRs. To do this properly
    a dynamic simualtion is needed.

    Do this based upon current power of each generator taking into 
    account its limits. e.g. if one generator is powering 50% of
    the network it should absorb 50% of the mismatch (as long as its
    limits aren't exceeded).
    """

class PsatData
  """
  Matlab file containing information for PSAT.
  psat_data.py - PsatData - psat_file - psat
  It should be used to create specifc things to simulate by using 
  the helper functions defined in 'script.py'.
  ----
  In addition to the matlab spec a compoent can have an ID specified 
  by adding %XX to the end of its line where XX is the id. See below 
  for more info on how the ID (cid) is used.
  """
 
  type BusNo -> PInt
  type Cid   -> Str

  # These are the sections of the file that are 
  # considered. Note that they are stored in a dict
  # by the ID (cid) if they have it, or by the number
  # of the bus they are connected to.
  # Hence all that are stored by bus_no must have only 
  # one component per bus. 
  private var busses     :: Dict(BusNo, Bus)      
  private var lines      :: Dict(Cid,   Line)       
  private var slack      :: Dict(BusNo, Slack)    
  private var generators :: Dict(BusNo, Generator)
  private var loads      :: Dict(BusNo, Load)     
  private var shunts     :: Dict(BusNo, Shunt)    
  private var supply     :: Dict(Cid,   Supply)     
  private var mismatch   :: Real

  func read             :: Istream -> None
  func write            :: Ostream -> None

  func remove_bus       :: BusNo -> None
  func remove_line      :: Cid   -> None
  func remove_generator :: Cid   -> None
  func set_all_demand   :: PReal -> None
  func fix_mismatch     :: None  -> None

  class Bus
    var bus_no            :: Int 
    var v_base            :: Int
    var v_magnitude_guess :: Real
    var v_angle_guess     :: Real
    var area              :: Int
    var region            :: Int

  class Line
    var fbus     :: Int 
    var tbus     :: Int  
    var s_rating :: Int  
    var v_rating :: Int  
    var f_rating :: Int  
    var length   :: Real 
    var v_ratio  :: Real 
    var r        :: Real 
    var x        :: Real 
    var b        :: Real 
    var tap      :: Real 
    var shift    :: Real 
    var i_limit  :: Real 
    var p_limit  :: Real 
    var s_limit  :: Real 
    var status   :: Int  
    var cid      :: Str  

  class Supply
  class Slack
  class Generator
  class Load 
  class Shunt 
  class Demand

--------------------------------------------------------------------------------

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

--------------------------------------------------------------------------------
 
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

--------------------------------------------------------------------------------
  
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

--------------------------------------------------------------------------------

class PsatReport
  """
  Read in a report from psat; check format & sanity check.
  """
  class PowerFlow
  class LineFlow
  func in_limit :: -> Bool
  func read     :: istream(report_file) -> 

--------------------------------------------------------------------------------  
