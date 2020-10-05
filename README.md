# AM2302-Reliable
Probably overcomplicated but functional realiable AM2302 temperature/humidity grabber for Raspberry Pi

When using the AM2302 temperature sensor, occasionally I would get some obvious anomalies, such as temperatures going from 20C to -12C, 86C, etc.

To fix this I've made this, it's probably overcomplicated but as far as I can tell it works.

It's currently set to log to a mySql databse however this can be modified easily as the main code is written in functions.

# How to use / How it works
Set the pin variable to whichever GPIO pin your sensor is connected to, configure the database details and the interval you want the temperature to be logged.

When the script is ran it will grab 6 samples from the sensor, the first three being temperature, the other three being humidity.

Validate these figures (no massive differences, so for example '20.1 / 20.2 / 20.0' would be okay, '20.1 / 40.3 / 10.2' would not) by typing YES.

The script will then average out the humidity and temperature and then test every future polled data against this average, by making sure it is not above or below a certain threshold, which can be modified in the code.

This would obviously have the issue that true larger drops in temperature over a long period of time would fail, however this script will reset the average to the last 3 temperature/humidity readings it stored. This should filter out any, if not all anomalies as immediate drops in temperature of around 5C within 3 polls would be rejected, where as if say the temperature in a room was gradually falling, the averages would similarly drop too, and only realistic readings will be kept.

# Modifying it
There may be cases if you do use this script where more sudden temperature drops would actually happen. If polling at 30 seconds, as a new average is generated every 3 polls. This means every 1.5 minutes if there is a temperature drop that exceeds the upper and lower limits of the temperature and humidity filtering system they'd be rejected.

To fix this, modify lines 80-83 to have a bigger margin for temperature/humidity changes.

# Actual use
This script was just put together pretty rapidly as a quick solution. It's probably overcomplicated but as far as my use is concerned, it's been logging to mySql for 2 weeks without any errors or anomalies being stored.

Feel free to use and modify this yourself if you'd like.
