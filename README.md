
rasPyCNC
==========
A simple CNC (Grbl) gcode sender designed tob e used on a 480x320 touchscreen and a joypad.

**Note: This release is yet not thoroughly tested. Please use at your own risk!**

Requirements
------------

The program requires a Linux computer and a monitor, preferably a Raspberry Pi 2 or better and a 480x320 touchscreen like [this one from Adafruit](https://www.adafruit.com/products/2097).

Moreover, python 2.7 is required with the following additional modules:

 - psutil
 - PySerial
 - PySide (and Qt libraries)
 - evdev

Instructions
------------

Starting the program
--------

The program is started by the following command line:

    python raspyCNC.py [-f] [-d]

The following command-line options can be used:

    -f or --fullscreen: start the program fullscreen
    -d or --dummy: use a dummy Grbl sender (echo to stdout) instead of serial communication

Usage
--------

When first started, the program will look for a serial connection to a CNC machine. Once both are found, the program will enter “jog mode”, showing the following screen:

![JogWidget start screen](http://fsantini.github.com/rasPyCNCController/doc_images/jogwidget_noLoad.jpg)

From this screen, the machine position can be controlled and the origin set. The position is  controlled by the joypad, with the following button mapping:


![JogWidget button mapping](http://fsantini.github.com/rasPyCNCController/doc_images/jogScheme.jpg)

Clicking on “Load” or pressing button 10 on the joypad, opens the file selection:

![FileWidget](http://fsantini.github.com/rasPyCNCController/doc_images/fileWidget.jpg)

In this mode, the mounted partitions (drives) are shown on the left pane, and the current directory is shown in the right pane. A file can be selected via mouse/touchscreen, or using the hat buttons of the joypad. Button 1 of the joypad selects a file or navigates the directory structure (clicking on a directory will open it).

Once the desired file is selected, press “OK” or button 9 of the joypad to load it. The program will return to the jog screen. “Cancel” does not load any new file.

The file is loaded asynchronously and analyzed; the bounding box of the part is displayed in order to have an idea of the dimensions and check that it will fit in the available stock. An estimation of the printing time is given.

Once the proper origin for the part is selected, pressing “Run” or button 9 will run the job, and the program will enter the following “Run” mode:

![RunWidget](http://fsantini.github.com/rasPyCNCController/doc_images/runWidget.jpg)

The estimated time is replaced by a progress bar, and a stop button appears for emergency stop. Button 9 of the joypad will also quickly stop the job. In case of stop, the position reference is lost and the machine is reset.

The “Pause” button (button 10 of the joypad) stores the current position and temporarily enters the jog mode; the user can then move the machine position. When “Resume” is clicked (button 10), the machine will safely move back to the stored position and resume the job.

**Important note: the displayed position information is in millimiters. The program should be able to correctly interpret gcode files in imperial units, but additional testing is required. Estimated time and Pause commands might not work correctly with imperial units.**

Jogging
--------

The program is designed to work with a joypad. However, jog commands using a numeric keypad are also supported. Only 1mm movements are supported at the moment and the key mapping is the following:
 - 4,6: X movement
 - 8,2: Y movement
 - 9,3: Z movement
 - 5: Go home
 - 0: Set home
 - Enter: Set Z=0
 
You can also write your own joggers to support more devices. Please see the Joggers/AbstractJogger.py file for more instructions.

ShuttleXpress support
--------

RasPyCNC now supports the ShuttleXpress jogger too. Please notice that this is only available under Linux because it requires the evdev system.
The device can be used to jog the machine by keeping one of the axis buttons pressed (first three buttons, see below) and **at the same time** rotating the encoder or the wheel. Rotating the encoder or the wheel alone will do nothing.
Pressing one of the axis buttons together with the forth button will set the work coordinate to zero for that axis.
Finally, the fifth button changes the step size of the rotary encoder, cycling through 1, 0.1 and 10mm steps.
![ShuttleXpress description](http://fsantini.github.com/rasPyCNCController/doc_images/jogShuttle_scheme.png)

Host Commands
--------

The software supports the host command `@pause`, which can be prefixed by a `;` or enclosed in parentheses (`(@pause)`), in the running GCode to insert a pause in the execution of the program.

Probing
--------
This is an exciting new feature especially thought for PCB milling. It can be (de)activated in the configuration file.
In order to use this feature, an electrical touch probe must be attached to your machine, [like this one](https://www.shapeoko.com/forum/viewtopic.php?f=4&t=6444&p=50333#p50331).
If the functionality is activated, two extra buttons appear in the jog page:
![JogWidget with probe](http://fsantini.github.com/rasPyCNCController/doc_images/screenshot_with_probe.png)

The **Z Probe** functionality tests the Z height in a single point and sets the working Z coordinate at the touch point.
The **Grid Probe** functionality is activated when a file is loaded. It runs a series of Z probes over the whole working area (defined as the bounding box, rounded up to the nearest 10mm, so make sure you have enough space!). The Z offsets are stored and then during the job, the Z value is constantly adjusted to keep a constant cutting depth.
**Please note**: At the moment the Z adjustment only works in metric units and absolute movements!

Example PCB Milling workflow
--------
The following is an example of the workflow used to etch/mill a single sided PCB board with this software.

 1. Design the PCB and convert it into GCode with Eagle/pcb_gcode or pcb2gcode.
 2. Place the board on the milling machine.
 3. Load the etching gcode file.
 4. Zero the machine on where etching should start.
 5. Connect the probe and run a *Grid Probe*.
 6. Disconnect the probe.
 7. Run the etching job. The commands will be automatically adjusted to the board geometry.
 8. Remove the etching bit and place the drilling bit.
 9. Load the drilling GCode file.
 10. Connect the probe and run a *Z Probe* to account for the different bit length.
 11. Run the drilling job.
 12. Repeat for milling etc.

Configuration
------------

The application can be configured by modifying the `cnc_config.py` file. Many aspects can be configured, including:

 - Serial port and baud rate
 - Joypad button mappings (note that the buttons start from 0, so button 1 is defined as 0 in the configuration)
 - Jog parameters

The configuration allows the definition of a standard G0 feed rate for the calculation of estimated time; however, the program will attempt to read the actual value from the Grbl configuration at runtime.

Installation
------------

The software is designed to run on a Raspberry Pi and a 480x320 touchscreen. Smaller touchscreens are not suitable for the interface. Also, the program cannot run without a joypad.

In order to make it pretty, I used a 3D-printed case that can be found [here](http://www.thingiverse.com/thing:1229473).

A ready-made image for a RPi2 can be downloaded from the releases section.

Here's a picture of my setup:

![Raspberry Pi](http://fsantini.github.com/rasPyCNCController/doc_images/raspberry.jpg)

License
------------

The program is licensed under GPL v3. Please see LICENSE.txt for details.
The following files contain code from other people:
 - GrblWriter.py: contains code from Will Welch, https://github.com/welch/shapeoko
 - GCodeAnalyzer.py: contains code from RepetierHost, repetierdev@gmail.com (Licensed under Apache 2.0 License)
Please see the sources for further details on licensing.

> Written with [StackEdit](https://stackedit.io/).
