# SALSA RIO CONTROL
The SALSA telescopes are controlled by a Galil RIO47200, which can be programmed in the DMC language (digital motion control)using GalilTools.
The RIO supports 4 threads and programs must be &lt;200 rows and &lt;40 columns.<br>
The telescopes are moved by setting the direction and turning on the motors.
Movement is detected by a light-sensitive detector and cogs.
The cogs block the detector when the telescope moves which is how motion is detected.
## IO capabilities
The RIO have 10 active outputs and 2 active inputs.
### Output
+ 0: Elevation motor on/off
+ 1: Elevation motor CCW-mode on/off
+ 2: Azimuth motor on/off
+ 3: Azimuth motor CCW-mode on/off
+ 4: Elevation LED
+ + Flashing: Motion detected
+ + On: Motion error detected
+ 5: Azimuth LED
+ + Flashing: Motion detected
+ + On: Motion error detected
+ 6: Reduce applied voltage to the (elevation?) motor.
+ 7: Reduce applied voltage to the (azimuth?) motor.
+ 8: LNA is active
+ 9: Noise diode is active
### Input
+ 0: Elevation cog detector is blocked (digital 0) or not blocked (digital 1) by cog.
+ 1: Azimuth cog detector is blocked (digital 0) or not blocked (digital 1) by cog.

## Thread layout
The program utilizes all 4 threads as follows:
+ 0: Telescope initialization and detects if the telescope is stuck (i.e. motors are on but telescope is not moving).
+ 1: Azimuth motion detection.
+ 2: Elevation motion detection.
+ 3: Telescope move loop and bounds check.

## Interaction with the telescope
SALSA interacts with the telescope through an ethernet connection.<br>
A hard reset can be issued by sending the command `RS`, which resets the RIO to a power-on state.
A soft reset can be issued by sending the commands `HX0`, `HX1`, `HX2`, `HX3` and `XQ #init`, which stops all runing threads and initializes the telescope (on thread 0).
If the initialization is not started on thread 0 the telescope may not function properly and may be damaged if used.<br>
All variables can be accessed when connected to the RIO.
For simplicity only the folowing variables should be accessed via ethernet.
### Read and write access
+ t\_az: Target azimuth cog value.
+ t\_el: Target elevation cog value.
### Read-only access
+ c\_az: Current azimuth cog value.
+ c\_el: Current elevation cog value.
+ az\_dpch: Azimuth degrees per cog-hole distance. Multiplying az\_dpch with c\_az yields current azimuth offset in degrees.
+ el\_dpch: Elevation degrees per cog-hole distance Multiplying el\_dpch with c\_el yields current elevation offset in degrees.
+ minaz: Minimum allowed aimuth cog values (i.e. new\_az>=minaz)
+ maxaz: Maximum allowed aimuth cog values (i.e. new\_az<=maxaz)
+ minel: Minimum allowed elevation cog values (i.e. new\_el>=minel)
+ maxel: Maximum allowed elevation cog values (i.e. new\_el<=maxel)
+ knowpos: = 0 indicates that the telescope needs (re-)initialization.
+ stuck: = 1 indicates that the telescope is stuck; all threads have stopped and the motors have turned off. The azimuth and elevation LEDs have been turned on to indicate an error.
### Conversion between cog and azimuth offset
The RIO program has a read-only variable for each direction for this purpose - az\_dpch for azimuth and el\_dpch for elevation (dpch for degrees per cog-hole).
These values represents the smallest movement in their respective direction that can be detected.
The offsets increase in clockwise direction as defined by the motors when output bit 1 (for elevation) and 3 (for azimuth) is cleared (digial zero).
For elevation this offset increases in the direction that is towards the sky from the zero-offset elevation.<br>
Conversion from degrees to cogs is done by dividing the degree offset with the corresponding dpch value.<br>
Conversion from cogs to degrees is done by multiplying the cog offset with the corresponding dpch value.<br>
### Zero-offset position and and offsets
All cog offsets are relative to a zero-offset position.
This position can be determined by sending the command `SB3;SB1;SB2;SB0` to the RIO and wait until the telescope has stopped moving (do not forget to send the command `CB2;CB0;CB3;CB1` to stop the motors).
This position should be measured and added to any offset that has been read from the telescope and converted to degrees (see previous section).
Likewise this position should be subtracted from any position that should be converted to cog offset and sent to the RIO (see previous section).
### Setting and reading position
Positions are set by converting the desired position into cog offsets and sent to the telescope. Positions are acquired by converting a cog offset that has been read from the telescope. See the previous two sections for details on how to convert positions into cog offsets and cog offsets into positions.

# Modifying the RIO program
The control program may not exceed 200 lines of code, where each line must be less than 40 columns.
If the program is longer that 200 lines it will automatically be compressed by removing whitespace, comments and placing multiple statements per line.
If the compressed program does not exceed 200 lines a warning will be issued.
If the compressed program still exceeds 200 lines an error will occur.<br>
The program should be developed using GalilTools which facilitates uploading/downloading and testing.
All variables have global scope so a few conventions should be followed to facilitate development.
+ Variables declared in #AUTO should be considered global.
+ Variables declared in subroutines (beginning with a label and end with EN) should be considered local to the suproutine.
+ Statements which are connected should be written on one line to allow for more complex programs. Examples are setting multiple bits (`CB2;CB0;CB3;CB1`), setting multiple connected variables (c\_az=0;t\_az=0) and simple if-statements (IF(@OUT[5]);CB5;ELSE;SB5;ENDIF).
+ Indent with 1 space when entering a subroutine or if-statement
## Microprocessor properties
The microprocessor takes approximately 40 microseconds to execute a single statement. The `WT` command depends on the internal clock which has a resolution of 1 ms. This means that a `WT X` will sleep untill the internal clock ticks `X` times, which will take between `X-1` and `X` ms.<br>
When timing is crucial in a loop with multiple statements it may be necessary to include the execution time of the actual loop.
## The telescope is a mechanical system
When modifying the control code keep in mind that
+ The telescope is equipped with mechanical switches to prevent physical damage on the system if control of the telescope is lost and the code is malfunctioning. These switches should NOT be hit during normal operation to increase their lifespan. The switches should only be hit under normal operation during the initialization.
+ Make sure that the telescope does not get stuck (meaning that the motors are on but the telescope is not moving).
+ To reduce strain on the system, CCW-mode should be set before starting motor and motor should be stopped before clearing CCW-mode.
+ Starting and stopping the telescope is not instant. This is the reason why the telescope must be stopped before it can change direction.

# DMC code layout
The code is divided into five parts - AUTO, INIT, chkaz, chkel, chkmv.
## \#AUTO
This part of the program is executed when the RIO powers on. It is intended to initialize global variables and constants. It also should not start any motors as this should only be done when actively sending a command to do so.
## \#INIT
This part of the program is the manual initialization code. It will reset the telescop to a known location and start all threads. If the telescope is stuck and all threads have halted this code can be executed to re-initialize the telescope. It should therefore not be required to run a software reset if the telescope gets lost.
## \#chkaz/\#chkel
This part of the program continously check for any movement in azimuth/elecation. The telescope is supplied with a light-sensitive detector and a light as well as a cogwheel which spinns such that the cogs block the detector when the telescope is moving. Due to poor isolation between cables there are somtimes false positives and negatives. For this reason one must use the average from a few samples. The spikes last for less than a millisecond so no more than 10 samples should be required to filter out the false positives/negatives.<br>
It takes about 70 ms for a cog or hole to pass the detector at full motor speed. This must be taken into consideration when sampling. In order to be positive that a cog is completely blocking or not it is recommended that requiring all of the samples to detect either 0 or 1 since there may be ambigous results at the cog edges.
## \#chkmv
This part of the program controls the motion of the telescope based on its current position and target position. It operates on a fixed-time loop that consists of the following steps:
+ Read target position and perform a bounds check.
+ Select action (stop or move) based on the target position.
+ Run motors (if necessary).
+ Check if stuck.
The speed of the motor can be changed by varying the duty cycle of the motors. Due to limitations of the DMC language and code size constraints there are three different speeds:
+ Full - target is far away.
+ Slow - target is near (< ~15 degrees).
+ Very slow - target is very close (< ~1 degree).
Due to the limited position tracking capabilities of the system it is crucial that the telescope must come to a halt before changing the direction of motion. The code size constraint makes this very dificult to realize so it may be necessary to reset the telescope pointing every 6-12 hours to maintain a pointing error of less than 1-2 degrees.<br>
This part of the program also checks if the telescope is unable to reach its target position (i.e. it is stuck). In order to prevent the telescope from being damaged, is will stop all threads and exit. The telescope can be re-initialized (without requiring a software reset) by running the INIT code again.
