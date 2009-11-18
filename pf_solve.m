% matlab
% matlab -nodesktop -nodisplay -nojvm -nosplash -r solve
% psat MUST be in the search path for matlab

% powerflow then optimal power flow the file
% 'rts.m'. saving results to rts_??.txt
% where ?? is an incrementing number 

% setup
initpsat;

% settings
Settings.lfmit = 50;       % iteration limit
Settings.violations = 'on' % check for limits in report

% load file
runpsat('psatfilename','data');

% power flow and save report
runpsat pf;
runpsat pfrep; % it does save opf results ok

% clean up
closepsat;
exit
