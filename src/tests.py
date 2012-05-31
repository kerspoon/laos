'''
Created on 4 Aug 2011

@author: james
'''


from misc import Error
from psat_report import PsatReport
from script import read_psat, read_probabilities, make_failures, batch_simulate, \
    simulate_scenario, report_in_limits, clean_files, text_to_scenario, \
    single_simulate, single_matlab_script, simulate, read_report, report_to_psat, \
    scenario_to_psat
from simulation_batch import Scenario, SimulationBatch
import StringIO

def example1(n=100):
    """make `n` outages, simulate them, and save the resulting batch"""

    psat = read_psat("rts.m")
    prob = read_probabilities("rts.net")
    batch = make_failures(prob, n)

    batch_simulate(batch, psat, 30)

    with open("rts.bch", "w") as result_file:
        batch.write(result_file)

# example1()


def example2(report_filename="tmp.txt"):
    """test a report and actually see why if fails"""
    
    with open(report_filename) as report_file:
        report = PsatReport()
        res = report.read(report_file)
        print "result =", res, "."

# example2()


def example3():
    """one random failure"""
    
    psat = read_psat("rts.m")
    prob = read_probabilities("rts.net")
    batch = make_failures(prob, 1)
    scenario = batch[0]
    report = simulate_scenario(psat, scenario)
    print "result =", report_in_limits(report), "."


# example3()


def example4():
    """one specified scenario, simulated"""

    clean_files()
    clean = False

    data = """
           [example_4] opf
remove generator g12
           """
           
    #remove generator g33
    #set all demand 0.7686144
    #remove bus 6
             
    scenario = text_to_scenario(data)
    psat = read_psat("rts.m")
    report = simulate_scenario(psat, scenario, clean)

    print "result = '" + str(report_in_limits(report)) + "'"

# example4()


def example5():

    clean_files()
    clean = False

    data = """
           [base] opf
           [dead_slack] opf
             remove generator g12
           [two_dead_slack] opf
             remove generator g12
             remove generator g13
           [three_dead_slack] opf
             remove generator g12
             remove generator g15
           [four_dead_slack] opf
             remove generator g13
             remove generator g12
           [five_dead_slack] opf
             remove generator g15
             remove generator g12
           [all_dead_slack] opf
             remove generator g12
             remove generator g13
             remove generator g15
           [rem_bus_1] opf
             remove bus 1
           [rem_li_a1] opf
             remove line a1
           [rem_gen_g1] opf
             remove generator g1
           [set_double] opf
             set all demand 2.0
           [set_half] opf
             set all demand 0.5
           """

    #data = """
    #       [fail_001] pf
    #         remove generator g32
    #         remove generator g13
    #"""

    batch = SimulationBatch()
    batch.read(StringIO(data))
    psat = read_psat("rts.m")

    for scenario in batch:
        report = simulate_scenario(psat, scenario, clean)
        print "result = '" + str(report_in_limits(report)) + "'"


#example5()


# -----------------------------------------------------------------------------

def test001():
    """
    a system after OPF should not depend on the values of generator.p or
    generator.v. These should be set by the OPF routine based upon price.

    You have to temporarily delete assert(in_limits) for this to work.
    
    It requires looking at the resulting files to make sure they are the 
    same as well as checking the output on the console.
    """

    clean_files()
    clean = False

    psat = read_psat("rts.m")
    report = single_simulate(psat, "opf", "base", clean)
    print "base result = '" + str(report_in_limits(report)) + "'"

    for gen in psat.generators.values():
        gen.p = 1.0
        gen.v = 1.0
    report = single_simulate(psat, "opf", "unit", clean)
    print "unit result = '" + str(report_in_limits(report)) + "'"

    for gen in psat.generators.values():
        gen.p = 10.0
        gen.v = 10.0
    report = single_simulate(psat, "opf", "ten", clean)
    print "ten  result = '" + str(report_in_limits(report)) + "'"

    for gen in psat.generators.values():
        gen.p = 0.0
        gen.v = 0.0
    report = single_simulate(psat, "opf", "zero", clean)
    print "zero result = '" + str(report_in_limits(report)) + "'"


# test001()


def test002():
    """
    make sure that limits are hit when we set them really low
    """

    clean_files()
    clean = False

    psat = read_psat("rts.m")
    report = single_simulate(psat, "pf", "base", clean)
    print "base result = '" + str(report_in_limits(report)) + "'"

    for line in psat.lines.values():
        line.i_limit = 0.01
        #line.p_limit = 0.01
        line.s_limit = 0.01
    report = single_simulate(psat, "opf", "small", clean)
    print "small result = '" + str(report_in_limits(report)) + "'"


# test002()


def test003():
    """
    load flow a file then do it again; psat_report and psat_data should match
    """

    clean_files()

    simtype = "opf"

    def helper(title):
        matlab_filename = "matlab_" + title
        psat_filename = title + ".m"
        single_matlab_script(matlab_filename + ".m", psat_filename, simtype)
        res = simulate(matlab_filename)
        if res != [True]: raise Error("expected [True] got %s" % str(res))

    helper("rts")

    report = read_report("rts_01.txt")
    psat = read_psat("rts.m")

    new_psat = report_to_psat(report, psat)

    with open("test_d.m", "w") as new_psat_stream:
        new_psat.write(new_psat_stream)

    helper("test_d")


#test003()


def test004():
    """
    run two simulations on differnt files
    """

    clean_files()
    clean = False

    data = """
           [notused] pf
             #set all demand 0.5
           """

    scenario = text_to_scenario(data)

    psat = read_psat("rts.m")
    scenario.title = "mod1"
    report = simulate_scenario(psat, scenario, clean)
    print "first result = '" + str(report_in_limits(report)) + "'"

    psat = read_psat("rts2.m")
    scenario.title = "mod2"
    report = simulate_scenario(psat, scenario, clean)
    print "second result = '" + str(report_in_limits(report)) + "'"

# test004()


def test005():
    """simulate an islanded system

       by cutting all the lines across one line it is seperated. But still 
       passes he simulation. Reoving all the generators hit the multiplier 
       limit on fix_mismatch.

       A power flow is more likely to fail. Theoretically an OPF could 
       treat the two islended sections as seperate power systems and
       optimise each. Unfortunatly PF doesn't yet work!
    """

    clean_files()
    clean = False

    data = """
           [example_4] pf
             remove line a24
             remove line a19
             remove line a18
             remove line a15
           """

    scenario = text_to_scenario(data)
    psat = read_psat("rts.m")
    report = simulate_scenario(psat, scenario, clean)

    print "result = '" + str(report_in_limits(report)) + "'"


# test005()


def test006():
    """playing with shunt"""

    clean_files()

    def dosim(title, simtype):
        matlab_filename = "matlab_" + title
        psat_filename = title + ".m"
        single_matlab_script(matlab_filename + ".m", psat_filename, simtype)
        simulate(matlab_filename)

    def cycle(in_filename, out_psat_filename):
        report = read_report(in_filename + "_01.txt")
        psat = read_psat(in_filename + ".m")

        new_psat = report_to_psat(report, psat)
        new_psat.generators[39].v = "1.01401"
        new_psat.generators[40].v = "1.01401"
        new_psat.generators[41].v = "1.01401"
        new_psat.generators[42].v = "1.01401"
        new_psat.generators[43].v = "1.01401"

        with open(out_psat_filename + ".m", "w") as new_psat_stream:
            new_psat.write(new_psat_stream)

    def copy_kill_shunt_mod(in_filename, out_psat_filename):
        psat = read_psat(in_filename + ".m")
        psat.shunts = {}
        psat.generators[39].v = "1.01401"
        psat.generators[40].v = "1.01401"
        psat.generators[41].v = "1.01401"
        psat.generators[42].v = "1.01401"
        psat.generators[43].v = "1.01401"
        psat.loads[6].q = "1.299"

        with open(out_psat_filename + ".m", "w") as new_psat_stream:
            psat.write(new_psat_stream)

    def copy_psat(in_filename, out_filename):
        psat = read_psat(in_filename + ".m")
        with open(out_filename + ".m", "w") as psat_stream:
            psat.write(psat_stream)

    # convert 'rts.m' to form for diff.
    copy_psat("rts", "psat_base")

    def inner_test6():
        """we can remove the effect of the shunt by
           changing the load Q value and removing the shunt"""
        simtype = "opf"
        copy_kill_shunt_mod("psat_base", "psat_a")
        dosim("psat_a", simtype)
        cycle("psat_a", "psat_b")
        dosim("psat_b", simtype)
        cycle("psat_b", "psat_c")
        dosim("psat_c", simtype)
    # inner_test6()

    def inner_test7():
        """after taking out the shunt we should have a stable solution
           with either pf or opf."""
        simtype = "opf"
        copy_kill_shunt_mod("psat_base", "psat_a")
        dosim("psat_a", simtype)
        copy_psat("psat_base", "psat_b")
        dosim("psat_b", simtype)
    # inner_test7()

    def inner_text8():
        simtype = "opf"
        copy_psat("psat_base", "psat_a")
        dosim("psat_a", simtype)
        cycle("psat_a", "psat_b")   
        dosim("psat_b", simtype) 
        cycle("psat_b", "psat_c")   
        dosim("psat_c", simtype) 
        cycle("psat_c", "psat_d")   
        dosim("psat_d", simtype) 
        cycle("psat_d", "psat_e")   
        dosim("psat_e", simtype) 
        cycle("psat_e", "psat_f")   
        dosim("psat_f", simtype) 
        
        
    def inner_text9():
        copy_psat("psat_base", "psat_a")
        dosim("psat_a", "opf")
        
        

# test006()

def test007():
    """batch and single should gave same results"""
    
    clean_files()

    psat = read_psat("rts2.m")
    # prob = read_probabilities("rts.net")
    # batch = make_outages(prob, 2)

    data = """
[batch0] opf
  remove generator g1
  remove generator g4
  remove generator g31
  set all demand 0.3987456
  result pass
[batch1] opf
  remove generator g22
  remove generator g24
  set all demand 0.6670332
  result fail
           """

    batch = SimulationBatch()
    batch.read(StringIO(data))

    batch_simulate(batch, psat, 10, False)

    with open("rts.bch", "w") as result_file:
        batch.write(result_file)

    for n, scenario in enumerate(batch):
        scenario.title = "single" + str(n)
        report = simulate_scenario(psat, scenario, False) 
        scenario.result = report_in_limits(report)
    
    with open("rts2.bch", "w") as result_file:
        batch.write(result_file)

# test007()


def test008():
    clean = False
    
    def copy_psat(in_filename, out_filename):
        psat = read_psat(in_filename + ".m")
        with open(out_filename + ".m", "w") as psat_stream:
            psat.write(psat_stream)
            
    def sim(psat, scenario_text):
        scenario = text_to_scenario(scenario_text)
        return simulate_scenario(psat, scenario, clean)
        
    data = """
           [base] opf
               set all demand 0.6
           """

    copy_psat("rts", "psat_base")
    psat = read_psat("psat_base.m")
    report = sim(psat, data)
    print "base result = '" + str(report_in_limits(report)) + "'"
    opf_psat = report_to_psat(report, psat)
    opf_report = single_simulate(opf_psat, "pf", "one", clean)
    print "opf result = '" + str(report_in_limits(opf_report)) + "'"
    
    opf_psat_2 = report_to_psat(opf_report, opf_psat)
    opf_report_2 = single_simulate(opf_psat_2, "pf", "two", clean)
    print "opf result 2 = '" + str(report_in_limits(opf_report_2)) + "'"
    
test008()

# -----------------------------------------------------------------------------

def upec(n_failures=100):
    """if we happen to have a stage one that kills the shunt bus then most bugs 
    go away. use this to get some data."""

    clean_files()
    clean = True

    data = """
           [upec] opf
             # remove generator g33
             # set all demand 0.7686144
             # remove bus 6
           """

    scenario = text_to_scenario(data)
    psat = read_psat("rts2.m")

    tmp_psat = scenario_to_psat(scenario, psat)
    report = single_simulate(tmp_psat, scenario.simtype, scenario.title)
    new_psat = report_to_psat(report, tmp_psat)

    prob = read_probabilities("rts.net")
    failure_batch = make_failures(prob, n_failures)

    failure_batch.scenarios.insert(0, Scenario("basecase"))
    batch_simulate(failure_batch, new_psat, 100, clean)

    filename = scenario.title + ".bch2"
    with open(filename, "w") as result_file:
        failure_batch.csv_write(result_file)

# upec(10)

