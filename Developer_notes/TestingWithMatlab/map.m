% MATLAB script to plot map of the Milky Way datafrom the SALSA telescope.
% written by Eskil Varenius 2014-12-21. Tested on Matlab R2014a. 
% INPUT: A tex file produced by the script "batch_fit", i.e. one line for each spectrum with 
% coordinates and fitted velocities
% OUTPUT: A pdf-file with a plot. This file may have some unnecessary whitespace around the figure,
% which can be removed by e.g. using the linux program "pdfcrop". 

% Define radius and velocity of the Sun. In this script we assume a flat rotation curve
% with V=V0. This can be seen to be a good approximation based on the results from the
% script "rotationcurve.m".
R0 = 8.5; % kpc
V0 = 220; % km/s

fid= fopen('ALLDATA.txt');
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
    % Get maximum velocity, i.e. max of all fitted components
    vels = numline(3:length(numline));
    % Calculate distance and rotational velocity. Convert to radians for the sin-function.
    theta = GLON-90 + 180; % Rotate to fit the Wikipedia image of galactic coordinates.
    % This means that the y coordinates below have -R0 instead of +R0.
    for VR = vels
        R = R0*V0*sin(GLON*pi/180.0)/(V0*sin(GLON*pi/180.0) + VR);
        % Calculate x,y coordinates for this cloud
        rp = sqrt(R^2-R0^2*(sin(GLON*pi/180.0))^2) + R0*cos(GLON*pi/180.0);
        rm = -sqrt(R^2-R0^2*(sin(GLON*pi/180.0))^2) + R0*cos(GLON*pi/180.0);
        if rp>0
            if rm<0
                r = rp;
                x = r * cos(theta*pi/180.0);
                y = -R0 + r * sin(theta*pi/180.0);
                % Plot
                plot(x,y,'*k')
                hold on
            elseif (isreal(rp)&&isreal(rm)==1)
                % Found two possible solutions. 
                % Easiest way to treat these is to plot both, but with another color
                r = rp;
                x = r * cos(theta*pi/180.0);
                y = -R0 + r * sin(theta*pi/180.0);
                % Plot
                plot(x,y,'*r')
                hold on
                r = rm;
                x = r * cos(theta*pi/180.0);
                y = -R0 + r * sin(theta*pi/180.0);
                % Plot
                plot(x,y,'*b')
                hold on
                [GLON, VR, rp, rm]
            end
        end
    end
    % Read next line
    tline = fgetl(fid);
end
% Close input file
fclose(fid);

% Plot position oc center and sun

text(0, 0, 'C')
hold on
text(0, -8.5, 'Sun')
hold on
text(-15, 15, 'Q1')
hold on
text(-15, -15, 'Q2')
hold on
text(15, -15, 'Q3')
hold on
text(15, 15, 'Q4')
hold on

% Set plot limits from 0 to 10kpc and 0 to 300 km/s.
xmin = -25; xmax = 25;
ymin = -25; ymax = 25;
axis([xmin, xmax, ymin, ymax])
axis square
title('Map of the Milky Way with the galactic center at (0,0)')
xlabel('[kpc]')
ylabel('[kpc]')
% Save final figure to file
print -painters -dpdf -r300 Map.pdf
