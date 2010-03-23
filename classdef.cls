
-------------------------------------------------------------------------------

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

------------------------------------------------------------------------------
  
class Scenario
  """
  Scenario is a structure for holding changes to a network such as the loss
  of a components or change in power.

  It currently supports removing a line, generator, or busbar as well as 
  setting all load (demand) by a factor. 'simtype' says how it should be
  simulated. 
  """

  func write    :: Ostream -> None

  var title      :: Str
  var simtype    :: Literal('pf','opf')
  var kill_bus   :: [BusNum]
  var kill_gen   :: [Cid]
  var kill_line  :: [Cid]
  var all_demand :: Real
  var result     :: Literal('pass', 'fail', 'error')

class SimulationBatch
  """
  Manager for a set of Scenario instances, called a batch file. This class
  probably isn't needed. 
  """
  func add      :: Scenario -> None
  func read     :: Istream -> None
  func write    :: Ostream -> None
  func __iter__ :: None -> Iter(Scenario)

------------------------------------------------------------------------------

private func probability_failure :: PReal 'failrate' -> UnitReal
  """
  returns the probability of a component 
  failing given the failure rate
  """

private func probability_outage :: PReal 'mttf' -> PReal 'mttr' -> UnitReal
  """
  returns the probability of a component 
  being on outage given the mean time to fail
  and restore
  """

private func fail :: UnitReal 'pfail'
  """
  does it fail?
  """

class NetworkProbability
  """
  A Data file containing the probability of failure of various components
  as well as joint failure of different components. It creates scenarios 
  from a network probability data file. 
  """
  func read     :: Istream -> None
  func write    :: Ostream -> None

  func outages  :: Str -> Scenario
    """
    Create a Scenario representing a possible state of the system
    as the system operator would see it (before any operator action).
    i.e. make a scenario.
    Hence it covers things like components out of service for maintanence
    and a load forcast.
    """

  func failures :: Str -> Scenario
    """
    Create a Scenario representing unexpected changes to a scenario. So it
    covers things like failures and load forcast error.
    """

  private func crow_fails :: [Cid] 'linekill' -> [Cid]
    """
    tripping certain lines causes certain other line to trip with a given
    probability. This does that tripping returning the list of line ID that
    should be tripped.
    """

  class Bus
    var bus_id      :: BusNo 
    var fail_rate   :: PReal
    var repair_rate :: PReal
    var pfail       :: UnitReal
    var pout        :: UnitReal

  class Generator
    var name        :: Cid
    var bus_id      :: BusNo
    var mttf        :: PReal
    var mttr        :: PReal
    var gen_type    :: Str
    var pfail       :: UnitReal
    var pout        :: UnitReal

  class Line
    var name        :: Cid
    var fbus        :: BusNo
    var tbus        :: BusNo
    var fail_rate   :: PReal
    var repair_rate :: PReal
    var trans_fail  :: PReal
    var pfail       :: UnitReal
    var pout        :: UnitReal

  class Crow
    var line1       :: Cid
    var line2       :: Cid
    var probability :: PReal

------------------------------------------------------------------------------

class PsatReport
  """
  Read in a report from psat; check format & sanity check.
  """

  func in_limit :: None -> Bool
  func read     :: istream(report_file) -> None

  var power_flow :: Dict(BusNo, PowerFlow)
  var acceptable :: Bool

  class PowerFlow
    var name  :: BusNo 
    var v     :: Real
    var phase :: Real
    var pg    :: Real
    var qg    :: Real
    var pl    :: Real
    var ql    :: Real

------------------------------------------------------------------------------

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

------------------------------------------------------------------------------


