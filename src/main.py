'''
Created on 27 Jul 2011

@author: james
'''

from misc import Ensure
from script import clean_files, simulate_scenario, report_to_psat, \
    batch_simulate, read_psat, read_probabilities, make_outage_cases, \
    make_failure_cases
import math
import sys
import time


def simulate_cases(outage_batch, failure_batch, psat, summary_file):
    clean_files()

    print "[C] simulate %d unique states with %d unique contingencies" % (
                                                        len(outage_batch), 
                                                        len(failure_batch))
    
    for n, scenario in enumerate(outage_batch):
        try:
            print "[C] simulating state", n + 1, "of", int(math.ceil(len(outage_batch)))
            report = simulate_scenario(psat, scenario, False)
            scenario_psat = report_to_psat(report, psat)
            clean_files()
            print "[C] simulating state - prep done."

            for x in failure_batch:
                x.result = None

            batch_simulate(failure_batch, scenario_psat, 100)
            
            filename = scenario.title + ".txt"
            with open(filename, "w") as result_file:
                failure_batch.csv_write(result_file)
            
            print "-" * 80
            print "---- Outage Case %d Stats ----" % n
            failure_batch.write_stats(sys.stdout)
            summary_file.write("Outage Case %d Stats\n" % n)
            summary_file.write("%s\n" % ("-"*80))
            failure_batch.write_stats(summary_file)
            
            print "[C] simulating state", n + 1, "done"
        except Exception as exce:
            print "[E] Error Caught at main.simulate_cases (%s)" % scenario.title
            print exce
            raise
            
            
def generate_cases(n_outages=10, n_failures=1000, sim=True, full_sim=True):
    
    if full_sim: 
        Ensure(n_outages and n_failures and sim, "can only do full sim if we have everything")
        
    clean_files()    
    batch_size = 100 
    psat = read_psat("rts.m")
    prob = read_probabilities("rts.net")

    timer_begin = time.clock()
    timer_start = timer_begin
    
    print "[G] start simulation."
    # create the base cases by sampling for outages 
    # simulate these and print to a file.
    # it should contain `n_outages` outages.
    
    summary_file = open("summary.txt", "w")
    try:
        if n_outages:
            outage_batch = make_outage_cases(prob, n_outages)
            if sim: batch_simulate(outage_batch, psat, batch_size)
    
            with open("outage.txt", "w") as result_file:
                outage_batch.csv_write(result_file)
                
            print "-" * 80
            print "---- Outage Stats ----"
            outage_batch.write_stats(sys.stdout)
            summary_file.write("%s\n" % ("-"*80))
            summary_file.write("Outage Stats\n")
            summary_file.write("%s\n" % ("-"*80))
            outage_batch.write_stats(summary_file)

            timer_end = time.clock()
            timer_time = (timer_end - timer_start)
            print "[G] outages created in %d seconds." % int(math.ceil(timer_time))
            timer_start = time.clock()
        
        # do the same for one hour changes to the system.
        if n_failures:
            failure_batch = make_failure_cases(prob, n_failures)
            if sim: batch_simulate(failure_batch, psat, batch_size)
    
            with open("failure.txt", "w") as result_file:
                failure_batch.csv_write(result_file)
    
            print "-" * 80
            print "---- Failure Stats ----"
            failure_batch.write_stats(sys.stdout)
            summary_file.write("Failure Stats\n")
            summary_file.write("%s\n" % ("-"*80))
            failure_batch.write_stats(summary_file)
            
            timer_end = time.clock()
            timer_time = (timer_end - timer_start)
            print "[G] failures created in %d seconds." % int(math.ceil(timer_time))
            timer_start = time.clock()
    
        # simulate each of the changes to each base case
        if full_sim: 
            simulate_cases(outage_batch, failure_batch, psat, summary_file)
        
            timer_end = time.clock()
            timer_time = (timer_end - timer_start)
            print "[G] full sim  in %d seconds." % int(math.ceil(timer_time))
            timer_start = time.clock()
    finally:
        timer_end = time.clock()
        timer_time = (timer_end - timer_begin)
        print "[G] total time %d seconds." % int(math.ceil(timer_time))


if __name__ == '__main__':
    generate_cases(2, 1000, True, True)