"""A Script To Take many voltage readings from a daq970 and report how long it took to get the readings."""

import pyvisa as visa
import time
import csv
import datetime
import pyqtgraph as pg

pg.mkQApp()


def listresources():
    resource_list = rm.list_resources()
    return resource_list


# Read in the config.txt file to get the variables needed below.
with open("config.txt") as config:
    config = config.readlines()
    config = [line.rstrip() for line in config]
    config = [i for i in config if i[0] != "#"]

# Begin finding out the daq resources that are available.
rm = visa.ResourceManager()
# Make a variable that is the list of visa devices attached to the computer.
resources = listresources()
# Use the first instrument in the list.  If you need to specify a different one this may need to be changed.
dac = rm.open_resource(resources[0])
# Compose the query string based on which channels are described in the config file.  Always fill the instrument
# up fom the top slot and don't skip any cards and this will work.
if config[4] == "-1" and config[2] != "-1":
    query = str(
        'MEAS:VOLT:DC? ' + config[6] + ',' + config[7] + ',(@' + config[0] + ':' + config[1] + ',' + config[2] + ':' +
        config[3] + ')')
elif config[2] == "-1":
    query = str(
        'MEAS:VOLT:DC? ' + config[6] + ',' + config[7] + ',(@' + config[0] + ':' + config[1] + ')')
else:
    query = str(
        'MEAS:VOLT:DC? ' + config[6] + ',' + config[7] + ',(@' + config[0] + ':' + config[1] + ',' + config[2] + ':' +
        config[3] + ',' + config[4] + ':' + config[5] + ')')


# create a csv with the column headers as defined by the config file.
basename = "voltage_monitoring"
suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
filename = "_".join([basename, suffix, ".csv"])

# The following lines compose the column headers for the csv file that will be produced.
c1_start = int(config[0])
c1_end = (int(config[1]) + 1)
c2_start = int(config[2])
c2_end = (int(config[3]) + 1)
c3_start = int(config[4])
c3_end = (int(config[5]) + 1)
card1_channels = list(range(c1_start, c1_end))
card2_channels = list(range(c2_start, c2_end))
card3_channels = list(range(c3_start, c3_end))
card1_channels = ([str(x) for x in card1_channels])
card2_channels = ([str(x) for x in card2_channels])
card3_channels = ([str(x) for x in card3_channels])
prefix = 'CH-'
card1_channels = [prefix + x for x in card1_channels]
card2_channels = [prefix + x for x in card2_channels]
card3_channels = [prefix + x for x in card3_channels]
data_fields = ['Elapsed Seconds']
data_fields.extend(card1_channels)
data_fields.extend(card2_channels)
data_fields.extend(card3_channels)

# Create the csv data file and write out the column headers as composed above.
with open(filename, 'w', newline='') as g:
    writer = csv.writer(g)
    writer.writerow(data_fields)

# Create remote process with a plot window
import pyqtgraph.multiprocess as mp

proc = mp.QtProcess()
rpg = proc._import('pyqtgraph')
plotwin = rpg.plot()
curve = plotwin.plot(pen='b')
curve1 = plotwin.plot(pen='r')
curve2 = plotwin.plot(pen='g')

# create an empty list in the remote process
data = proc.transfer([])
data1 = proc.transfer([])
data2 = proc.transfer([])

# Set up a time variable and describe it as a float.
elapsed_time = 0.0

# Turn off the instrument display.  It only slows down scan times.
dac.write('DISP OFF')
# Write some test to the screen so it indicates there is a test in progress.
dac.write('DISP:TEXT "TEST IN PROGRESS"')
# Start keeping time.
start_time = time.time()
while elapsed_time < float(config[8]):
    v1 = dac.query_ascii_values(query)
    # Get min, max, average values which is all we need to plot.
    minV = min(v1)
    maxV = max(v1)
    avgV = 0 if len(v1) == 0 else sum(v1) / len(v1)
    # See how much time passed from the start_time
    elapsed_time = (time.time() - start_time)
    # Compose a row to be written to the csv data file.
    row = [elapsed_time] + [float(i) for i in v1]
    # Write the data to the csv file.
    with open(filename, 'a', newline='') as g:
        writer = csv.writer(g)
        writer.writerow(row)
    # Send new data to the remote process and plot it
    # We use the special argument _callSync='off' because we do
    # not want to wait for a return value.
    data.append(minV, _callSync='off')
    data1.append(maxV, _callSync='off')
    data2.append(avgV, _callSync='off')
    curve.setData(y=data, _callSync='off')
    curve1.setData(y=data1, _callSync='off')
    curve2.setData(y=data2, _callSync='off')

# Clear the text from the instrument screen.
dac.write('DISP:TEXT:CLE')
# Turn the instrument screen back on.
dac.write('DISP ON')
# Close the visa attachment to the instrument.
rm.close()
