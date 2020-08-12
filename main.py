import calendar, datetime

import numpy as np
import netCDF4

from scipy.io import wavfile
from matplotlib import pyplot as plt

'''
Code developed with help from http://cdip.ucsd.edu/themes/media/docs/documents/html_pages/dw_timeseries.html
'''

# Find nearest value in numpy array
def find_nearest(array,value):
	idx = (np.abs(array-value)).argmin()
	return(array[idx])

# Convert human readable (MM/DD/YYYY HH:MM) to unix timestamp
def getUnixTimestamp(humanTime,dateFormat):
	unixTimestamp = int(calendar.timegm(datetime.datetime.strptime(humanTime, dateFormat).timetuple()))
	return(unixTimestamp)

# Convert unix time stamp to human readable (MM/DD/YYYY HH:MM)
def getHumanTimestamp(unixTimestamp, dateFormat):
	humanTimestamp = datetime.datetime.utcfromtimestamp(int(unixTimestamp)).strftime(dateFormat)
	return(humanTimestamp)

def getTime(stn, deploy, dtFormat): 
	'''
	Gathering netCDF4 variables for station, stn, in deployment, deploy.
	'''
	url = 'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/' + stn + 'p1/' + stn + 'p1_d' + deploy + '.nc'
	with netCDF4.Dataset(url) as nc:
		ncTime = nc.variables['waveTime'][:]
		starttime = nc.variables['xyzStartTime'][:] # Variable that gives start time for buoy data collection
		sampleRate = nc.variables['xyzSampleRate'][:] # Variable that gives rate (frequency, Hz) of sampling

	# checking deployment start and end dates
	
	StartDate = getHumanTimestamp(ncTime[0],dtFormat)
	EndDate = getHumanTimestamp(ncTime[-1],dtFormat)
	print("Start of deployment " + deploy + " for station " + stn + ": " + StartDate)
	print("End of deployment " + deploy + " for station " + stn + ": " + EndDate)
	

	# Create time array for the z data using above variables
	time = np.arange((starttime),(ncTime[-1]),(1/(sampleRate)))
	return(time, sampleRate)

def getZ(stn, deploy, start, end, qc): 
	'''
	Gathering netCDF4 variables for station, stn, in deployment, deploy.
	'''
	url = 'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/' + stn + 'p1/' + stn + 'p1_d' + deploy + '.nc'
	with netCDF4.Dataset(url) as nc:
		z = nc.variables['xyzZDisplacement'][start:end]
		#qcFlag = nc.variables['xyzFlagPrimary'][start:end]

	#z = np.ma.masked_where(qcFlag >= qc,z)

	return(z.data)

def z2audio(z, stnSampleRate):
	wavSampleRate = 44100 # [Hz]
	print("Time-multiplicative scale factor is: " + str(round(wavSampleRate/stnSampleRate)))
	z = z/np.amax(z) # normalize the waveform to amplitude 1 (we are encoding float32)
	wavfile.write('output.wav', wavSampleRate, z)



if __name__ == "__main__":
	# this is Torry Pines Outer Bouy from CDIP
	stn = '100' # this is Torry Pines Outer Bouy from CDIP
	# the most recent deployment number found here: http://thredds.cdip.ucsd.edu/thredds/catalog/cdip/archive/catalog.html
	deployment = '16'
	duration  = (24*60*60)*100 # Set length of timeseries [seconds]
	qc_level = 2 # Filter data with qc flags above this number 

	dateTimeFormat = "%m/%d/%Y %H:%M" # human readable datetime format

	startDate = "10/4/2018 00:00" # date we will start on
	unixStart = getUnixTimestamp(startDate, dateTimeFormat)
	unixEnd = unixStart + duration

	time, stnSampleRate = getTime(stn, deployment, dateTimeFormat)

	startIndex = time.searchsorted(unixStart)
	endIndex = time.searchsorted(unixEnd)

	# slice the desired times from the time array
	time = time[startIndex:endIndex]


	z = getZ(stn, deployment, startIndex, endIndex, qc_level)

	plt.plot(time,z)
	plt.savefig('zDisp_plot.png')

	# get rid of unreasonabley bad data
	z = z[z > -100]

	z2audio(z, stnSampleRate)