#!/usr/local/anaconda/bin/python

# This script takes in the direct RBM output files, creates a subdirectory under the RBM output directory, and put RBM results of each stream segment (each stream node has 2 segments; confluence grid cells have multiple nodes, while non-confluence grid cells have one node).
# Output file names: <lat>_<lon>_reach<reach#>_seg<seg#>
#    where <lat>, <lon> are lat and lon of the grid cell;
#          <reach#> is the reach number defined in RBM (this can be helpful when trying to look at confluence grid cells);
#          <seg#> is the segment number (1 or 2)
# The columns of each file: <year> <month> <day> <streamflow (cfs)> <stream T (degC)>

# The script takes two command line arguments: ./rbm_output_process.py lat lon

import numpy as np
import datetime as dt
import os
import sys

#=======================================================
# Parameter setting
#=======================================================
#=== input ===#
# We assume that direct RBM output files are: $rbm_output_dir/$run_code.Temp/.Spat
# A directory named $rbm_run_code will be made under the RBM output directory; formatted files will be under this directory
run_code = 'Tennessee_1949_2010'
rbm_output_dir = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/RBM/Maurer_8th/Tennessee'  # RBM output directory
lat_to_extract = float(sys.argv[1])  # grid cell to extract
lon_to_extract = float(sys.argv[2])
precision = 4   # number of decimal points of grid cell
nseg_nday_path = rbm_output_dir + '/' + run_code + '.nseg_nday'  # a text file; first line: total # all stream segments; second line: total # days of the run

#=== output ===#
output_dir = rbm_output_dir + '/' + run_code + '%.*f_%.*f' %(precision, lat_to_extract, precision, lon_to_extract)

#=========================================================
# Extracting grid cell data
#=========================================================
temp = rbm_output_dir + '/' + run_code + '.Temp'  # .Temp file
spat = rbm_output_dir + '/' + run_code + '.Spat'  # .Spat file
nseg_nday = np.loadtxt(nseg_nday_path)
nseg = int(nseg_nday[0])  # total number of all segments
nday = int(nseg_nday[1])  # total number of days

#=== identify which lines in .Spat are corresponding to the target grid cell ===#
f = open(spat, 'r')
line_count = 0
cell_info = {}  # a dictionary; keys are line numbers of the target grid cell (int); element isa list with 2 elements: [reach_ind, seg_ind]

while 1:  # loop over each line in the .Spat file
	line = f.readline().rstrip("\n")
	line_count = line_count + 1  # current line number
	if line=="":
		break
	lat = float(line.split()[4])
	lon = float(line.split()[5])
	if lat==lat_to_extract and lon==lon_to_extract:  # if this line corresponds to the target grid cell
		reach_ind = int(line.split()[0])  # reach index, defined by RBM
		seg_ind = int(line.split()[6])  # seg index within a node, 1 or 2
		dict = {}  # create a new element in the dictionary
		cell_info[line_count] = [reach_ind, seg_ind]
f.close()

#=== read .Temp file and extract target grid cells ===#
f = open(temp, 'r')
line_count = 0
data = {}   # final data to write; this is a dictionary whose keys are line numbers in the .Spat file (each key is one stream seg), and dicrionary content is corresponding data (np array, [year] [month] [day] [flow(cfs) [T_stream(degC)]]);
for i in cell_info:
	data[i] = []
while 1:  # loop over each line in the .Temp file
	line = f.readline().rstrip("\n")
	line_count = line_count + 1
	if line=="":
		break
	line_num_in_spat = line_count%nseg  # corresponding line number in the .Spat file

	if line_num_in_spat in cell_info:  # if the current line in the .Temp file is corresponding to the target grid cell, save this line
		decimal_year = line.split()[0]
		year = int(decimal_year.split('.')[0])
		day_of_year = int(line.split()[1])
		if day_of_year > 360 and decimal_year.split('.')[1] == '0013':  # correct bad decimal year integer part
			year = year - 1
		date = dt.datetime(year, 1, 1) + dt.timedelta(days=day_of_year-1)  # convert day of year to date
		flow = float(line.split()[8])
		T_stream = float(line.split()[5])
		data[line_num_in_spat].append([year, date.month, date.day, flow, T_stream])
		print 'Processing', year, date.month, date.day, '...'

for i in data:  # convert to np.array
	data[i] = np.asarray(data[i])

#=========================================================
# Save data to files
#=========================================================
#=== make directory ===%
if not os.path.exists(output_dir):
	os.makedirs(output_dir)

#=== write data ===#
for line_num in cell_info:
	f = open('%s/%.*f_%.*f_reach%d_seg%d' %(output_dir, precision, lat_to_extract, precision, lon_to_extract, cell_info[line_num][0], cell_info[line_num][1]), 'w')
	data_current = data[line_num]
	for i in range(nday):
		f.write('%d %d %d %.1f %.2f\n' %(data_current[i,0], data_current[i,1], data_current[i,2], data_current[i,3], data_current[i,4]))
	f.close()


