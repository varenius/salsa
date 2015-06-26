classdef SalsaSpectrum<handle
    
    % Class to initialize and do operations on spectra from the Salsa
    % Onsala telescopes and the control software. Create a spectrum object
    % using the syntax
    %
    % spec = SalsaSpectrum('filename.fits');
    %
    % which then can be displayed and analyzed.
    %
    %
    % This software comes with no warranty. It has been thoroughly
    % tested, but there may still be bugs. It can be downloaded on the
    % SALSA onsala Web site at vale.oso.chalmers.se.

	% version 2.2
	% 23 june, 2015
    % - Changed sign of velocity to reflect change in sign in 
	%   the controller software writing the FITS files. 
	%   This is due to sign convention used in SalsaJ.
	% - Changed offset for reference pixel to be consistent with
	%   SalsaJ, i.e. instead of +2 in control software I use +2 in 
	%   matlab code.
    
    % version 2.1
	% 31 may, 2015
    % - Fixed readLAB function to use https instead of http. Now urlwrite
    % works also for linux! Removed wget, curl from the code.
    
    % version 2.0
	% 30 may, 2015
    % - Changed to read ONLY new SALSA files, i.e. with proper
	%   keywords also adjusted for SalsaJ, so no use of RESTFREQ etc.

    % version 1.92
    % 27 dec, 2014
    % - Changed from theoretical 6.4 to measured 5.4 degrees for SALSA beam when downloading from LAB.
	% - Noted that showConfInt seems to be broken on this new (2014a) Matlab version. Added
	%   issue to Github tracker.
	
    % version 1.91
    % 2 aug, 2014
    % - small bugfix to accept both old and new matlab versions in GaussianFitting.
    % - Updated info to vale.

    % version 1.9
    % 30 nov, 2013
    % - small bugfix for error in GaussianFitting.

    % version 1.8
    % 11 mars, 2013
    %  - readLab now works on windows (via the "urlwrite" command). 
    
    % version 1.7
    % 7 december, 2012
    %  - interactive baseline fit
    %  - improved blind gaussian fitting, which works better with new versions
    %    of matlab.
    %  - no fitting is now performed if no peaks are found
    %  - interactive gaussian fit (function fitGaussiansInteractive)
    %  - fixed the readLab function, now searches for either curl or wget
    %    to download the data.
    %  - added code that calculates uncertainties on fitted gaussian
    %  parameters (gaussErr, gaussErrFreq, gaussErrVel)
    %  - added choice in fitting method, nlinfit or lsqcurvefit. Both give
    %  similar answers. nlinfit is faster, lsqcurvefit can constrain
    %  parameter values (e.g. the amplitude of the gaussian should not be
    %  negative).
    
    % Version 1.6
    % 21 november, 2012
    % Changes:
    %    - added smoothSpectrum function (experimental)
    %    - cleaned up the help information
    
    properties (Constant)
        c = 2.99792458e8;           % speed of light
        HIfreq = 1.42040575177e9;   % HI frequency in Hz
        fittype = 0;                % 1 for nlinfit, 0 for lsqcurvefit
    end
    
    properties (GetAccess = 'private', SetAccess = 'private')
        baseSubtracted
        coordType
        gaussiansFitted
    end
    
    properties(GetAccess = 'public', SetAccess = 'private')
        % public read access, but private write access.
        fileName
    end
    
    properties
        freq                 % frequency array
        vel                  % velocity array
        index                % spectrum index array
        info                 % fitsinfo
        data                 % data spectrum
        %basePol              % coeffiecients of fitted polynomial baseline
        baseLine             % fitted polynomial baseline
        baseWindow           % all indices of the baseline windows
        baseWindowParVel     % velocity values of start-end baseline window
        baseWindowParInd     % index values -"-
        baseWindowParFreq    % frequency values -"-
        rms                  % rms value calculated in the baseline windows
        gaussFit             % fitted gaussian functions
        gaussConfInt         % 68% confidence interval on the gaussian fit
        gaussPar             % parameters of gaussians
        gaussParVel          % -"- in velocity units
        gaussParFreq         % -"- in frequency units
        gaussErr             % 1 sigma errors on gaussians
        gaussErrVel          % -"- in velocity units
        gaussErrFreq         % -"- in frequency units
        gaussIntegrated      % integrated intensity in K km/s
        residuals            % residuals data - gauss fit
        labVel               % velocity axis of LAB spectrum
        labSig               % data of LAB spectrum
        
    end % properties
    
    
    methods
        function spec = SalsaSpectrum(fname)
            % Constructor for the SalsaSpectrum class.
            
            spec.fileName = fname;
            spec.data = fitsread(fname);
            spec.info = fitsinfo(fname);
            
            % get the frequency scale from the spec.header of the fits files
            freq_ref_pix = getKeyword(spec, 'CRPIX1') + 2;
            freq_delta = getKeyword(spec, 'CDELT1');
            %disp(2*freq_delta)
            freq_ref = getKeyword(spec, 'CRVAL1');
            n_chan = getKeyword(spec, 'NAXIS1');
            vlsr = getKeyword(spec, 'VELO-LSR')*1000;
                   
            spec.freq = freq_ref + ( (1:n_chan) - freq_ref_pix )*freq_delta;
            spec.vel = (  -(spec.freq - freq_ref)/freq_ref * ...
                spec.c - vlsr) / 1000; % Changed VLSR sign 2015-06-23 to work with SalsaJ
            spec.index = 1:n_chan;
            spec.baseSubtracted = 0;
            spec.gaussiansFitted = 0;
            
            spec.coordType = {getKeyword(spec,'CTYPE2'), ...
                getKeyword(spec,'CTYPE3')};
            
        end % constructor
        
        
        function handle = plot(obj, varargin)
            % HANDLE = PLOT(obj,varargin)
            %
            % Plot a spectrum. The default syntax
            %
            % spec.plot()
            %
            % By default the velocity scale is used. Other options are
            % 'pix' for indices and 'freq' for frequency.
            %
            % spec.plot('freq')
            %
            % If you have fitted Gaussians, they will also be
            % displayed.
            %
            % If a second 'dummy' argument is supplied, and gaussians have
            % been fitted, the individual Gaussians will be shown.
            %
            % spec.plot('vel', 'dummy')
            
            clf
            hold on
            box on
            %grid on
            
            fff = 7;
            set(gca, 'fontsize', fff)
            ff = fff;
            
            
            if ~isempty(varargin)
                type = varargin{1};
            else
                type = 'vel';
            end
            
            if strcmp(type,'freq')
                
                diffx = min(diff(obj.freq))/2;
                handle = stairs( (obj.freq - diffx)/1e6, obj.data);
                xlabel('Frequency (MHz)','fontsize', ff);
                ylabel('Antenna temperature [K]','fontsize', ff);
                
                if ~isempty(obj.gaussParFreq)
                    hh=plot(obj.freq/1e6, obj.gaussFit);
                    set(hh,'color', 'r')
                end
                
            elseif strcmp(type, 'pix')
                diffx = min(diff(obj.index))/2;
                handle = stairs(obj.index-diffx, obj.data);
                xlabel('Pixels ]','fontsize', ff);
                ylabel('Antenna temperature [K]','fontsize', ff);
                
                if ~isempty(obj.gaussPar)
                    hh=plot(obj.index, obj.gaussFit);
                    set(hh,'color', 'r')
                end
                
            elseif strcmp(type,'vel')
                
                diffx = min(diff(obj.vel))/2;
                handle = stairs(obj.vel - diffx, obj.data);
                xlabel('Velocity [km/s]','fontsize', ff);
                ylabel('Antenna temperature [K]','fontsize', ff);
                
                if ~isempty(obj.gaussParVel)
                    hh=plot(obj.vel, obj.gaussFit);
                    set(hh,'color', 'r');
                end
            end
            
            % what about plotting individual gaussians?
            if nargin == 3
                if obj.gaussiansFitted
                    obj.showIndividual(type);
                end
            end
            
            titlestr = sprintf(['Salsa %s=%d %s=%d. date=%s ' ...
                't=%5.1fs'], ...
                obj.getKeyword('CTYPE2'), ...
                obj.getKeyword('CRVAL2'), ...
                obj.getKeyword('CTYPE3'), ...
                obj.getKeyword('CRVAL3'), ...
                obj.getKeyword('DATE-OBS'), ...
                obj.getKeyword('OBSTIME'));
            
            titlestr = sprintf('%s=%5.1f %s=%5.1f', ...
                obj.getKeyword('CTYPE2'), ...
                obj.getKeyword('CRVAL2'), ...
                obj.getKeyword('CTYPE3'), ...
                obj.getKeyword('CRVAL3'));
            
            title(titlestr,'fontsize', ff);
        end
        
        
        function showResiduals(obj)
            % SHOWRESIDUALS(obj)
            %
            % Plot the residuals; the difference between the data and
            % the Gaussian model.
            if obj.gaussiansFitted == 1
                plot(obj.vel, obj.residuals,'g');
            else
                ME = MException('SalsaSpectrum:showResiduals', ['To ' ...
                    '' ']show residuals you must ' ...
                    'first perform a Gaussian fit']);
                throw(ME);
            end
        end
        
        
        function handle=showIndividual(obj,varargin)
            % HANDLE = SHOWINDIVIDUAL(obj,varargin)
            %
            % plots the individual gaussian functions fitted to the spectrum. Can
            % only be called after fitGaussians has ben used.
            
            if nargin == 2
                type = varargin{1};
            else
                type = 'vel';
            end
            
            if strcmp(type,'vel')
                gpar = obj.gaussParVel;
                xx = obj.vel;
            elseif strcmp(type,'freq')
                gpar = obj.gaussParFreq;
                xx = obj.freq/1e6;
            elseif strcmp(type,'pix')
                gpar = obj.gaussPar;
                xx = obj.index;
            end
            
            ngauss = length(gpar)/3;
            
            gaussFunc = @(par,ind) (par(1).*exp(-1/2*(ind- ...
                par(2)).^2./ ...
                par(3)^2));
            for i = 1:ngauss
                ii = i*3-2;
                indGauss(:,i) = gaussFunc( gpar(ii:(ii+2)), xx );
            end
            handle = plot(xx, indGauss,'k-.');
            
            
        end
        
        
        function shiftVel(obj, deltav)
            % SHIFTVEL(obj,deltav)
            %
            % Shift the velocity scale by a value. To shift the scale 20 km/s
            % toward positive velocities, use
            %
            % spec.shiftVel(-20)
            
            obj.vel = obj.vel - deltav;
            if obj.gaussiansFitted
                obj.gaussParVel(2:3:end) = obj.gaussParVel(2:3:end) - deltav;
            end
        end
        
        
        function scale(obj, scalefac)
            % SCALE(obj,scalefac)
            %
            % Scale the spectrum and fitted Gaussians by a factor, by
            % multiplication. To scale a spectrum down by 20%, use the
            % command
            %
            % spec.scale(8/10)
            
            if obj.gaussiansFitted
                obj.gaussPar(1:3:end) = obj.gaussPar(1:3:end)* scalefac;
                obj.gaussParFreq(1:3:end) = obj.gaussParFreq(1:3:end)*scalefac;
                obj.gaussParVel(1:3:end) = obj.gaussParVel(1:3: ...
                    end)*scalefac;
                obj.gaussFit = obj.gaussFit * scalefac;
            end
            obj.data = obj.data*scalefac;
            
        end
        
        
        function fitBaseline(obj,varargin)
            % FITBASELINE(obj,varargin)
            %
            % fit a polynomial to the spectrum baseline. Define the
            % baseline using a set of windows in the following way:
            %
            % [ x11 x12 x21 x22 x31 x32 ... ]
            %
            % as the first parameter passed to the function.
            %
            % The baseline vector should consist of an even number of
            % values. If not, the function gives an error.
            %
            % The baseline windows are supplied in units of
            %
            % 1. indices     ['pix']
            % 2. velocity    ['vel']
            % 3. frequency   ['freq']
            %
            % Send the string (e.g. 'vel') as a second argument. The index
            % unit is default.
            %
            % By default, this routine fits a first order polynomial to
            % the chosen spectral windows. Supply another polynomial order
            % as an argument
            %
            % spec.fitBaseline([-200 -150 40 200], 'vel', 2)
            %
            % This command will fit a second order polynomial between
            % velocities -200 to -150 and 40 to 200
            
            if obj.baseSubtracted
                disp('A baseline has already been fitted and subtracted.')
                return
            end
            
            % interactive marking of baseline windows, no arguments
            if nargin == 1
                coord = 'vel';
                disp(['Mark each baseline window by clicking twice, on ' ...
                    'each side of the window.'])
                disp(['You can mark several windows ' ...
                    'but it is important that you only click an even number ' ...
                    'of times.'])
                disp('Press return when you are finished.');
                obj.plot(coord);
                
                i = 1;
                colors = repmat({'r', 'r', 'g','g','m','m','y','y'},1,3);
                
                while 1
                    [tmpv tmpd] = ginput(1);
                    if tmpv ~= 0
                        
                        dataOnLine = mean(obj.data(obj.getIndices ...
                            (tmpv+ [-2 0 2],'vel')));
                        aa=plot(tmpv, dataOnLine, 'ro');
                        set(aa,'markerfacecolor',colors{i},'markeredgecolor',colors{i});
                        vind(i) = tmpv;
                        i = i + 1;
                    else
                        break
                    end
                end
                
                %[vind y] = ginput;
                if mod( length(vind), 2 ) == 1
                    ME = MException('SalsaSpectrum:fitBaseline',['You ' ...
                        'must give an even number ' ...
                        'of values defining the ' ...
                        'baseline windows']);
                    throw(ME);
                end
                
                %if max(vind) > max(obj.vel)
                ind = getIndices(obj,vind,coord);
                order = input('Input polynomial order: ');
                
                % arguments given
            elseif nargin > 1
                if mod( length(varargin{1}), 2 ) == 1
                    ME = MException('SalsaSpectrum:fitBaseline',['You ' ...
                        'must give an even number ' ...
                        'of values defining the ' ...
                        'baseline windows']);
                    throw(ME);
                end
                
                ind = varargin{1};
                order = 1;
                
                if length(varargin) == 1
                    coord = 'pix';
                elseif length(varargin) == 2
                    if ~ischar(varargin{2})
                        order = varargin{2};
                        coord = 'pix';
                    else
                        coord = varargin{2};
                        ind = getIndices(obj,ind,coord);
                    end
                elseif length(varargin) == 3
                    coord = varargin{2};
                    order = varargin{3};
                    ind = getIndices(obj,ind,coord);
                end
                
            end
            % end check length of input
            
            obj.baseWindowParInd = ind;
            obj.baseWindowParFreq = getIndices(obj,ind,'pixfreq');
            obj.baseWindowParVel = sort( getIndices(obj,ind,'pixvel') );
            
            ind=sort(ind);
            indices = [];
            for i = 1:2:length(ind)
                indices = [indices ind(i):ind(i+1)]; %#ok<AGROW>
            end
            
            obj.baseWindow = indices;
            
            % fit the baseline to the indices
            basePol = polyfit( obj.index(indices), ...
                obj.data(indices), order);
            obj.baseLine = polyval(basePol, obj.index);
            
            obj.getRms();
            
            if nargin == 1
                obj.showBaseline
            end
            
        end
        
        
        function back = getIndices(obj,ind,coord)
            % help function for the fitBaseline function
            if strcmp(coord, 'vel')
                % from velocities to pixels
                back = round( interp1(obj.vel, obj.index, ind) ) ;
            elseif strcmp(coord,'freq')
                % from frequency to pixels
                back = round( interp1(obj.freq, obj.index, ind ) );
            elseif strcmp(coord, 'pixvel')
                % from pixels to velocities
                back = interp1(obj.index, obj.vel, ind);
            elseif strcmp(coord, 'pixfreq')
                % from pixels to frequencies
                back = interp1(obj.index, obj.freq, ind);
            end
            
        end
        
        
        function showBaseline(obj)
            % SHOWBASELINE(obj)
            % Show the fitted baseline overlaid on the spectrum, as well as boxes
            % indicating the baseline windows.
            %
            % spec.showBaseline()
            %
            % This function does not subtract the baseline. Use the
            % subtractBaseline function to do that.
            
            if ~isempty(obj.baseWindow)
                obj.plot();
                hold on
                handle1=plot(obj.vel, obj.baseLine, 'r');
                set(handle1, 'linewidth', 1);
                obj.showBaselineWindows();
            else
                disp('You must fit a baseline before using showBaseline')
            end
            
        end
        
        
        function subtractBaseline(obj)
            % SUBTRACTBASELINE(obj)
            %
            % Subtract the fitted baseline from the data.
            if isempty(obj.baseLine)
                
                ME = MException('SalsaSpectrum:subtractBaseline', ...
                    ['You must fit a baseline before ' ...
                    'using subtractBaseline']);
                throw(ME);
                
            elseif obj.baseSubtracted
                
                ME = MException('SalsaSpectrum:subtractBaseline', ...
                    'A baseline has already been subtracted');
                throw(ME);
                
            else
                obj.data = obj.data - obj.baseLine;
                obj.getRms;
                obj.baseSubtracted = 1;
            end
        end
        
        function fitGaussiansInteractive(obj)
            % FITGAUSSIANSINTERACTIVE(obj)
            %
            % Wrapper function for the fitGaussians function. Lets the user
            % define peaks in the spectrum with the mouse and sends those
            % peaks as guesses to the fitGaussians function that does the
            % actual fitting.
            
            disp(['Mark each peak in the spectrum with the mouse.'])
            disp('Press return when you are finished.');
            obj.plot('vel');
            
            % loop until return is pressed
            i = 1;
            while 1
                [tmpv tmpd] = ginput(1);
                if tmpv ~= 0
                    dataOnLine = mean(obj.data(obj.getIndices ...
                        (tmpv+[-2 0 2],'vel')));
                    aa=plot(tmpv, dataOnLine, 'ro');
                    set(aa,'markerfacecolor', 'r','markeredgecolor', 'r');
                    vind(i) = tmpv; % velocities
                    dind(i) = dataOnLine; % data values
                    i = i + 1;
                else
                    break
                end
            end
            
            % assume a line velocity standard deviation of about 8 km/s
            vsigma = 8;
            par = [dind vind repmat(vsigma,1,length(dind))];
            ngauss = length(par)/3;
            order = [];
            if ngauss > 1
                for i = 1:ngauss
                    order = [order [i:ngauss:(i+2*ngauss)]];
                end
            elseif ngauss == 1
                order = [1 2 3];
            end
            
            % send to fitGaussians to do the fitting
            obj.fitGaussians(par(order));
        end
        
        
        function fitGaussians(obj, varargin)
            % FITGAUSSIANS(obj,varargin)
            % Fit a number of gaussians to the spectrum. Supply guess
            % values of height, central value and width of each
            % gaussian, in units of velocity.
            %
            % spec.fitGaussians([60 0 8 30 -55 10])
            %
            % If you don't supply any guess, the function will search
            % for peaks in the spectrum and use those as starting
            % guesses for the fit. If the fit is not good, you can
            % redo it with a new guess.
            %
            % If you want to add gaussians to a fit, call this
            % function again with guesses for the new gaussian, and
            % send a second dummy argument, like
            %
            % spec.fitGaussians([60 -10 10],'dummy')
            %
            % which will add an extra gaussian of peak 60 K, central
            % velocity -10 km/s and velocity width 10 km/s to the fit.
            
            if nargin == 1
                
                
                % temporary smooth the data by a factor of 3
                os = 3;
                ind = obj.index(1):os:obj.index(end);
                velsmooth = obj.getIndices(ind,'pixvel');
                datasmooth = interp1(obj.index, smooth(obj.data,os+1), ...
                    ind);
                
                % a velocity difference between peaks of 10 km/s is assumed
                deltav = diff(velsmooth);
                minpeakdistance = ceil(abs(10/deltav(1)));
                if minpeakdistance < 2
                    minpeakdistance = 2;
                end
                
                % suppress warnings from findpeaks
                warning('off', 'signal:findpeaks:largeMinPeakHeight');
                
                
                [hpeak indpeak] = findpeaks(datasmooth, 'minpeakheight', ...
                    8, 'minpeakdistance', ...
                    minpeakdistance, 'threshold',0.3);
                
                % break if no peaks found
                if isempty(indpeak)
                    disp('No peaks found, exiting.')
                    return;
                end
                
                indpeak = indpeak*os;
                
                %% exclude the negative peak sometimes present around 200 - 225 pixels.
                %indremove = obj.getIndices(-130,'vel');
                %badpeak = find(indpeak>indremove);
                %
                %if ~ismember(badpeak,[])
                %    indpeak(badpeak) = [];
                %    hpeak(badpeak) = [];
                %end
                %
                %% exclude everything above 220 km/s (there is never any real signal
                %% there).
                %indremove = obj.getIndices(130,'vel');
                %badpeak = find(indpeak<indremove);
                %
                %if ~ismember(badpeak,[])
                %    indpeak(badpeak) = [];
                %    hpeak(badpeak) = [];
                %end
                %plot(indpeak, hpeak, 'gx')
                guess = [];

                % this always assumes a linewidth sigma of 7 pixels. That simple
                % assumption works very well most of the time.
                for i = 1:length(indpeak)
                    guess = [guess hpeak(i) indpeak(i) 7];
                end
                
                
            elseif nargin >= 2
                
                tmp = varargin{1};
                pcentral = obj.getIndices(tmp(2:3:end),'vel');
                psigma = tmp(3:3:end) / abs(min(diff(obj.vel)));
                par = [tmp(1:3:end) pcentral abs(psigma)];
                ngauss = length(par)/3;
                order = [];
                if ngauss > 1
                    for i = 1:ngauss
                        order = [order [i:ngauss:(i+2*ngauss)]];
                    end
                elseif ngauss == 1
                    order = [1 2 3];
                end
                
                par = par(order);
                
                if nargin == 2 % if guesses have been supplied.
                    guess = par;
                elseif nargin == 3
                    %tmp = obj.getIndices(tmp,'vel');
                    guess = [obj.gaussPar par];
                end
                
            end
            
            
            if mod( length(guess), 3 ) ~= 0 % number of guesses
                % must be divisible by three
                ME = MException('SalsaSpectrum:fitGaussians', ...
                    ['You must supply 3 guess values ' ...
                    'for each Gaussian']);
                throw(ME);
            end
            
            ngauss = length(guess)/3;
            if ngauss > 5
                sprintf(['SalsaSpectrum:fitGaussians: at most five ' ...
                    'gaussians can be fitted simultaneously. ' ...
                    'Discarding additional guesses'])
                guess = guess(1:15);
                ngauss = 5;
            end
            
            gaussFunc = @(par,ind) (par(1) .* exp( -1/2 * ( ind ...
                - par(2) ).^2 ./ par(3)^2 ));
            
            % do the fitting (should come up with a nicer way to define the
            % function) NOTE
            if ngauss == 1
                gauss = @(x, ind) gaussFunc( x(1:3), obj.index);
            elseif ngauss == 2
                gauss = @(x, ind) (gaussFunc( x(1:3), obj.index) + ...
                    gaussFunc( x(4:6), obj.index )); ...
            elseif ngauss == 3
            gauss = @(x, ind) (gaussFunc( x(1:3), obj.index) + ...
                gaussFunc( x(4:6), obj.index) + ...
                gaussFunc( x(7:9), obj.index));
            elseif ngauss == 4
                gauss = @(x, ind) (gaussFunc( x(1:3), obj.index) ...
                    + gaussFunc( x(4:6), obj.index) ...
                    + gaussFunc( x(7:9), obj.index) ...
                    + gaussFunc( x(10:12), obj.index));
            elseif ngauss == 5
                gauss = @(x, ind) (gaussFunc( x(1:3), obj.index) ...
                    + gaussFunc( x(4:6), obj.index) ...
                    + gaussFunc( x(7:9), obj.index) ...
                    + gaussFunc( x(10:12), ...
                    obj.index) + ...
                    gaussFunc( x(13:15), obj.index)); ...
                    
            end
            
            % make the fit
            
            % NOTE
            %
            % nlinfit - faster
            % lsqcurvefit - slower, but probably more accurate and upper
            % and lower bounds can be given.
            
            if obj.fittype == 1
                [fit, rw, ~, covb]=nlinfit(obj.index, obj.data, ...
                    gauss, guess);
                ci = nlparci(fit,rw,'covar',covb,'alpha', .32);
                err = fit - ci(:,1)';
                [ypred delta] = nlpredci(gauss, obj.index, fit, rw, ...
                    'covar', covb, 'alpha', .32);
            else
                % lower bounds for lsqcurvefit.
                options = optimset('Display','off');
                lb = repmat([0 -inf 0], 1, ngauss);
                [fit, ~, residual, ~, ~, ~, jacobian] = ...
                    lsqcurvefit(gauss, guess, obj.index, obj.data, lb, [], options);
                sigmar = 1./ (length(obj.index)-ngauss) * sum(residual.^2);
                covb = full(sigmar*inv(jacobian'*jacobian));
                err = sqrt(diag(covb));
                [ypred delta] = nlpredci(gauss, obj.index, fit, residual, ...
                    'covar', covb, 'alpha', .32);
            end
            
            obj.gaussFit = gauss(fit, obj.index);
            obj.gaussPar = fit;
            obj.gaussErr = err';
            
            % calculate fit parameters in velocity units
            vCentral = obj.getIndices(fit(2:3:end),'pixvel');
            deltav = abs(min(diff(obj.vel)));
            vSigma = fit(3:3:end) * deltav;
            vPar = [fit(1:3:end) vCentral abs(vSigma)];
            vErrPar = [err(1:3:end) err(2:3:end)*deltav abs(err(3:3:end))*deltav];
            
            order = [];
            if ngauss > 1
                for i = 1:ngauss
                    order = [order [i:ngauss:(i+2*ngauss)]];
                end
            elseif ngauss == 1
                order = [1 2 3];
            end
            
            obj.gaussParVel = vPar(order);
            obj.gaussErrVel = vErrPar(order);
            
            % calculate fit parameters in frequency units
            freqCentral = obj.getIndices(fit(2:3:end),'pixfreq')/1e6;
            deltafreq = abs(min(diff(obj.freq)))/1e6;
            freqSigma = fit(3:3:end) * deltafreq;
            freqPar = [fit(1:3:end) freqCentral abs(freqSigma)];
            freqErrPar = [err(1:3:end) err(2:3:end)*deltafreq abs(err(3:3:end))*deltafreq];
            
            order = [];
            if ngauss > 1
                for i = 1:ngauss
                    order = [order [i:ngauss:(i+2*ngauss)]];
                end
            elseif ngauss == 1
                order = 1:3;
            end
            
            obj.gaussParFreq = freqPar(order);
            obj.gaussErrFreq = freqErrPar(order);
            
            obj.gaussiansFitted = 1;
            obj.residuals = obj.data - obj.gaussFit;
            % Older matlab versions need different syntax than new
            if verLessThan('matlab', '8')
                obj.gaussConfInt = [ypred'-delta ypred'+delta];
            else
                obj.gaussConfInt = [ypred-delta ypred+delta];
            end
            % integrate the gaussian functions to obtain the integrated
            % intensity in K km/s
            
            for i = 1:ngauss
                ii = i*3-2;
                obj.gaussIntegrated(i) = quad( @(x) gaussFunc( ...
                    obj.gaussParVel(ii:(ii+2)), x), -300, 300);
            end
            
            sprintf(['%d Gaussians. \nUse plot() to see the ' ...
                'fitted Gaussians.'], ngauss)
            
        end
        
        
        function getRms(obj)
            % GETRMS(obj)
            %
            % calculate and display the rms of the data contained in the baseline
            % windows.
            
            obj.rms = std( obj.data(obj.baseWindow) );
            %sprintf('rms in baseline windows: %5.2f K \n', obj.rms)
        end
        
        
        function showBaselineWindows(obj)
            % SHOWBASELINEWINDOWS(obj)
            %
            % Plot a graphical representation of the chosen
            % baseline windows.
            
            hold on
            vind = obj.baseWindowParVel;
            ind = obj.baseWindowParInd;
            heightfac = 6;
            
            for i = 1:2:length(vind)
                
                medval = median( obj.data( ind(i+1):ind(i) ) );
                
                rr=rectangle('position', [vind(i) (-heightfac/2*obj.rms ...
                    + medval) ...
                    abs(vind(i+1)-vind(i)) ...
                    (heightfac*obj.rms)]);
                set(rr,'edgecolor','g', 'linewidth',1)
            end
            
        end
        
        
        function back = getKeyword(obj, key)
            
            % GETKEYWORD(OBJ, KEY) returns the value of KEY from the fits
            % header OBJ.INFO.
            %
            % This function was kindly provided by Magnus Sandén and Eskil
            % Varenius.
            
            keywords=obj.info.PrimaryData.Keywords;
            r='';
            for i=1:length(keywords)
                if (strcmp(keywords{i,1}, key))
                    r=keywords{i,2};
                end
            end
            if (strcmp(r, ''))
                ME = MException('getKeyword:keywordNotFound', ...
                    'Keyword not found in fits header.');
                throw(ME);
            end
            back = r;
            
        end
        
        function back = showLab(obj)
            
            if ~isempty(obj.labVel)
                handle1 = plot(obj.labVel, obj.labSig, 'c-.');
                set(handle1, 'color', [.7 0 .7]);
                back = handle1;
            else
                sprintf(['LAB data not downloaded yet. Use the ' ...
                    'readLab function to download LAB data']);
            end
            % a
        end
        % end function showLab
        
        function handle = showConfInt(obj,varargin)
            % SHOWCONFINT(obj)
            %
            % If gaussians have been fitted, show the calculated 68%
            % confidence interval on the current graph.
            %
            % by default, velocity units are used. Supply 'freq' och 'pix'
            % for frequency or pixel units instead.
            
            if nargin > 1
                coord = varargin{1};
            else
                coord = 'vel';
            end
            
            obj.plot(coord);
            hold on
            xx = [obj.vel fliplr(obj.vel)];
            yy = [obj.gaussConfInt(:,1)' fliplr(obj.gaussConfInt(:,2)')];
           
			size(xx)
			size(yy)
			
            hh = fill(xx,yy,'k');
            greycol = .75*[1 1 1];
            set(hh, 'facecolor', greycol, 'edgecolor', greycol);
            uistack(hh,'bottom');
            handle = hh;
            
            
        end
        
        function readLab(obj,varargin)
            % READLAB(obj)
            %
            % download data from the LAB survey at
            % http://www.astro.uni-bonn.de/hisurvey/profile/index.php
            %
            % by default, convolved to Salsa's angular resolution. If you
            % want higher angular resolution, supply the value (in
            % degrees) as an argument
            
            %             if ispc
            %                 disp('Sorry, dowloading LAB data does not work on Windows.')
            %                 return
            %             end
            
            if ~isempty(obj.labVel)
                disp('LAB data already downloaded and loaded')
                return
            end
            
			% Theoretical calculation
            salsares = round( (1.22 * 0.21 / 2.3) * 180/pi * 10 ...
                ) / 10;

			% Specify resolution
			%salsares = 6.4; 

            % dowload spectra with resolution given by user.
            if nargin == 2
                salsares = varargin{1};
            end
            
            glon = obj.getKeyword('CRVAL2');
            glat = obj.getKeyword('CRVAL3');
            
            % check if the correct lab data has already been downloaded
            if exist('lab.txt','file') == 2
                fid = fopen('lab.txt', 'r');
                
                % read the first line and check the coordinates
                % there. Check first if the file is empty.
                
                tline = fgetl(fid);
                
                if (tline==-1)
                    % the file is empty, download it again.
                    download = 1;
                    fclose(fid);
                else
                    coords = sscanf(tline, '%%%% %f %f %f %f');
      
                    fclose(fid)
                    
                    if [(round(coords(1)) == round(glon)) && (round(coords(2)) == ...
                            round(glat))]
                        % The correct file is already downloaded.
                        download = 0;
                        disp('correct file already downloaded');
                    else
                        % Download the file.
                        download = 1;
                    end % check if correct coordinates
                    
                end % check if the file is empty
            else
                download = 1;
            end % check if the correct file already exists
            
            
            if download

                comm1 = 'https://www.astro.uni-bonn.de/hisurvey/profile/download.php?';
                comm2 = sprintf('ral=%3.2f\\&decb=%3.2f\\&csys=0\\&beam=%3.2f', ...
                    glon, glat, salsares);
                url = [comm1,comm2];
                
                sprintf(['Downloading LAB data for galactic longitude ' ...
                    '%d and latitude %d'], glon, glat)
                try
                    [a, status] = urlwrite(url, 'lab.txt');
                catch me
                    disp('Could not download LAB data');
                end
        
            end
            
            fid = fopen('lab.txt','r');
            
            % find the part of the file with the LAB data
            while 1
                tline = fgetl(fid);
                % find the position in the file of the LAB data
                if regexp(tline, '%%LAB')
                    break
                end
            end
            
            i = 1;
            while ~feof(fid)
                tline = fgetl(fid);
                tmp = sscanf(tline, '%f %f');
                if ischar(tmp) || isequal(tmp, [])
                    break
                end
                lab(:,i) = tmp;
                i = i + 1;
            end
            
            fclose(fid);
            lab = lab';
            obj.labVel = lab(:,1);
            obj.labSig = lab(:,2);
        end
        
        
        function clipSpectrum(obj, window)
            % BACK = CLIPSPECTRUM(obj,window)
            %
            % NOTE: EXPERIMENTAL, USE AT YOUR OWN RISK.
            %
            % given the indices in the window parameter, this
            % function "clips" (removes) the indicated spectral
            % channels from the data. Several spectral windows can
            % be specified.  Only the 'pixel' spectral unit can be
            % used.
            %
            %   spec.clipSpectrum([1 10 230 250])
            %
            % would clip all channels between channels 1 and 10 (1 2 3
            % 4 5 6 etc) and between channels 230 and 250.
            
            indices = [];
            for i = 1:2:length(window)
                indices = [indices window(i):window(i+1)];
            end
            
            obj.data(indices) = NaN;
            %obj.vel(indices) = [];
            %obj.freq(indices) = [];
            %obj.index(indices) = [];
            if ~isempty( obj.gaussFit )
                obj.gaussFit(indices) = NaN;
            end
        end
        
        
        function despike(obj,varargin)
            % DESPIKE(obj,varargin)
            %
            % NOTE: EXPERIMENTAL, USE AT YOUR OWN RISK.
            %
            % experimental function to remove 'spikes' in the data. Works well for
            % the spike at the edge of the spectrum, works
            % sometimes also for strong RFI in the spectrum.
            
            if nargin == 2
                n = varargin{1};
                lim = 10;
            elseif nargin == 3
                n = varargin{1};
                lim = varargin{2};
            elseif nargin == 1
                n = 10;
                lim = 10;
            end
            
            % if gaussians have been fitted, exclude that
            % region of the spectrum from the despiking
            
            if obj.gaussiansFitted
                % Extract indices of the part where the gauss
                % fit is below some value. A value of 0.01
                % appears appropriate.
                
                gind = find(obj.gaussFit<0.01);
            else
                gind = obj.index;
            end
            
            x = obj.data(gind)';
            % extend data vector by n data points at both ends
            xi = [flipud(x(1:n)); x; flipud(x(end-n+1:end))];
            % apply order n median filter
            xfilt = medfilt1(xi,n);
            % difference to filtered data
            dif = abs(xfilt(1+n:end-n)-x);
            % number of spikes
            nspike = sum(dif>lim);
            % replace spikes with NaNs
            x(dif>lim) = NaN;
            obj.data(gind) = x';
            
            if obj.gaussiansFitted
                obj.residuals = obj.data - obj.gaussFit;
            end
        end
        
        
        function smoothSpectrum(obj,varargin)
            % SMOOTH(obj,varargin)
            %
            % Smooth a spectrum to a lower spectral resolution. To lower
            % the resolution by a factor of 2, supply the command
            %
            % spec.smooth(2)
            
            if nargin == 2
                os = varargin{1};
            else
                os = 2;
            end
            
            ind = obj.index(1):os:obj.index(end);
            vel = obj.getIndices(ind,'pixvel');
            freq = obj.getIndices(ind, 'pixfreq');
            obj.data = interp1(obj.index, smooth(obj.data,os+1), ...
                ind);
            
            if obj.gaussiansFitted
                obj.gaussFit = interp1(obj.index, obj.gaussFit, ind);
                obj.residuals = obj.gaussFit - obj.data;
            end
            
            if obj.baseSubtracted
                obj.baseLine = interp1(obj.index, obj.baseLine, ind);
            end
            
            obj.index = 1:length(obj.data);
            obj.vel = vel;
            obj.freq = freq;
            
            if obj.baseSubtracted
                baseindnew = obj.getIndices(obj.baseWindowParVel,'vel');
                obj.baseWindowParInd = baseindnew;
                baseindnew = sort(baseindnew);
                indices = [];
                for i = 1:2:length(baseindnew)
                    indices = [indices baseindnew(i):baseindnew(i+1)];
                end
                obj.baseWindow = indices;
            end
            
            
        end
        
    end % methods
    
    
end % class
