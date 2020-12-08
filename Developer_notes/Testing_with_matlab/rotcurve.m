% MATLAB script to plot a rotation curve of the Milky Way using data  from the SALSA telescope.
% written by Eskil Varenius 2014-12-21. Tested on Matlab R2014a. 
% INPUT: A tex file produced by the script "batch_fit", i.e. one line for each spectrum with 
% coordinates and fitted velocities
% OUTPUT: A pdf-file with a plot. This file may have some unnecessary whitespace around the figure,
% which can be removed by e.g. using the linux program "pdfcrop". Also saves an output file
% with the R and V values for plotting elsewhere.

% Define radius and velocity of the Sun.
R0 = 8.5; % kpc
V0 = 220; % km/s

% Infile
%fid= fopen('ALLDATA.txt');
fid= fopen('TEST.txt');
% Outfile
oid= fopen('ROTVALUES.txt', 'w');
fprintf(oid,'# R V(R) \n');

clf
% Read first line
tline = fgetl(fid);
% Loop until file is empty
while ischar(tline)
    % Convert from line of text to array of numbers
    numline = str2num(tline);
    % Get coordinates from first two numbers
    GLON = numline(1);
    GLAT = numline(2);
	if GLON<=90
        % Get maximum velocity, i.e. max of all fitted components
        vmax = max(numline(3:length(numline)));
        % Calculate distance and rotational velocity. Convert to radians for the sin-function.
        R = R0*sin(GLON*pi/180.0);
        V = vmax + V0*sin(GLON*pi/180.0);
        % Write line in outfile
        fprintf(oid,'%f %f \n',R, V);
        % Plot
        plot(R,V,'*')
        hold on
	end
    % Read next line
    tline = fgetl(fid);
end
% Close input file
fclose(fid);
% Set plot limits from 0 to 10kpc and 0 to 300 km/s.
rmin = 0; rmax = 10;
axis([rmin, rmax, 0, 300])
% Plot horizontal line at V0
plot([rmin, rmax],[V0,V0], 'k--')
title('Rotation curve of the Milky Way measured with SALSA')
xlabel('Distance from galactic center [kpc]')
ylabel('Rotation velocity [km/s]')
% Save final figure to file
print -painters -dpdf -r300 RotationCurve.pdf
