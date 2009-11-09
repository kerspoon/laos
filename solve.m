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
OPF.basepg = 0;            % ignore base power (as it will be done by bids/offers)
OPF.basepl = 0;            % ignore load power (as it will be done by bids/offers)

% load file
runpsat('rts','data');

% power flow and save report
runpsat pf;
runpsat pfrep;

% optimal power flow and save report
runpsat opf;
runpsat pfrep; % it does save opf results ok

% clean up
closepsat;
exit
