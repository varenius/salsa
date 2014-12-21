% MATLAB script to process many fits files from the SALSA telescope.
% written by Eskil Varenius 2014-12-21. Tested on Matlab R2014a. 
% This file uses the SalsaSpectrum class available on the SALSA website.
% NOTE: Needed to run matlab without desktop, i.e. start as 
% "matlab -nodesktop" for the interactive fitting to work properly.

% INPUT: All fits-files in the current directory. So, make sure this script is in the FITS directory before running.
files = dir('*.fits');
% OUTPUT: textfile with one line for each spectrum. 
% Each line will have GLON, GLAT and then center velocities of fitted peaks
outfile = fopen('OUT.txt','w');

% Check if input contains any valid files
if length(files)==0
    disp('Found 0 files. Wrong directory?')
end

% For each file, do interactive fitting and save results in outfile
for i = 1:length(files)
    % Get filename
    filename = files(i).name;
    % Open as SalsaSpectrum
    spec=SalsaSpectrum(filename);
    spec.plot();
    % Run interactive fitting of baseline to remove residual receiver shape
    spec.fitBaseline();
    spec.subtractBaseline();
    spec.plot();
    % Run interactive Gaussian fitting to get velocities in spectrum
    spec.fitGaussiansInteractive();
    spec.plot();
    % Save fitted resuls in temporary variable
    fittedvels = spec.gaussParVel(2:3:end);
    % Read coordinates from FITS file
    GLON = spec.getKeyword('CRVAL2');
    GLAT = spec.getKeyword('CRVAL3');
    % Write new line in outfile, starting with coordinates
    fprintf(outfile,'%6.2f %6.2f',GLON, GLAT);
    % Append, to this line, the fitted velocities
    for i= 1:length(fittedvels)
        fprintf(outfile,' %6.2f',fittedvels(i));
    end
    % End line with newline character, then proceed to next file
    fprintf(outfile,'\n');
end
% Close outfile to flush all buffers.
fclose(outfile);
