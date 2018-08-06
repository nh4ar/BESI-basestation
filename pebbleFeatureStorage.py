from datetime import datetime
# from hbProcUtils import *
from colorama import init
import time
import os
import globalParams
import socket
from parseConfig import parseConfig
import subprocess
import numpy 

# listen at the given port for a connection, and return it if one is made. If no connection is made in timeout seconds, returns none
def connectRecv(host, port, networkNum, timeout):
	# configuration parameters; purpose unknown
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	# Bind the socket to the port
	# if networkNum = 0, connect to relay stations on LAN, if networkNum = 1, connect on Wi-Fi
	#try:
	#    name = socket.gethostbyname_ex(socket.gethostname())[-1][networkNum]
	#except:
	#    name = socket.gethostbyname_ex(socket.gethostname())[-1][1-networkNum]
	name = socket.gethostbyname(host)
	server_address = (name, port)
	#print >>sys.stderr, 'starting up on %s port %s' % server_address
	sock.bind(server_address)
	
	sock.settimeout(timeout)
	# Listen for incoming connections
	sock.listen(1)
	
	
	# Wait for a connection
	#print >>sys.stderr, 'waiting for a connection'
	
	try:
		connection, client_address = sock.accept()
	except:
		return None
	
	#print >>sys.stderr, 'connection from', client_address
	# make connection nonblocking
	connection.settimeout(0)
	
	return connection

# get parameters from the config file  
name, ports, useAccel, useLight, useADC, useWeather, numRelayStat, fileLengthSec, fileLengthDay, DeploymentID, DeploymentToken, networkNum, notiTime = parseConfig()

PORT = 9000

FeatureList = ("timestamp_1,timestamp_2,"
	+"x_mean,x_median,x_max,x_var,x_rms,x_IQR,x_meanXrate,x_meanDiff,x_maxDiff,x_teager_mean,x_teager_std,"
	+"x_teager_max,x_fft_0_1_max,x_fft_mean_0_1,x_fft_1_3_max,x_fft_mean_1_3,x_fft_3_10_max,x_fft_mean_3_10,"
	+"y_mean,y_median,y_max,y_var,y_rms,y_IQR,y_meanXrate,y_meanDiff,y_maxDiff,y_teager_mean,y_teager_std,"
	+"y_teager_max,y_fft_0_1_max,y_fft_mean_0_1,y_fft_1_3_max,y_fft_mean_1_3,y_fft_3_10_max,y_fft_mean_3_10,"
	+"z_mean,z_median,z_max,z_var,z_rms,z_IQR,z_meanXrate,z_meanDiff,z_maxDiff,z_teager_mean,z_teager_std,"
	+"z_teager_max,z_fft_0_1_max,z_fft_mean_0_1,z_fft_1_3_max,z_fft_mean_1_3,z_fft_3_10_max,z_fft_mean_3_10,"
	+"mag_mean,mag_median,mag_max,mag_var,mag_rms,mag_IQR,mag_meanXrate,mag_meanDiff,mag_maxDiff,mag_teager_mean,mag_teager_std,"
	+"mag_teager_max,mag_fft_0_1_max,mag_fft_mean_0_1,mag_fft_1_3_max,mag_fft_mean_1_3,mag_fft_3_10_max,mag_fft_mean_3_10,"
	+"corr_xy,corr_xz,corr_yz"
	+"\n")

FeatureInputArray = numpy.zeros(75)

# pebbleFeature_folder = "PebbleFeature_P2D4/"
pebbleFeature_folder = "PebbleFeature/"
if not os.path.exists(pebbleFeature_folder):
	os.mkdir(pebbleFeature_folder)

try:
	host = socket.gethostbyname(name)
	print "Streaming Pebble Features to: ",host
except socket.gaierror, err:
	print "cannot resolve hostname: ", name, err

while True:
	try:
		currtime = datetime.now()
		pebbleFeatureFileName = "PebbleFeature_{0}-{1:02}-{2:02}_{3:02}.txt".format(
			currtime.year, currtime.month, currtime.day, currtime.hour)
		pebbleFeatureFile = pebbleFeature_folder + pebbleFeatureFileName

		if not os.path.exists(pebbleFeatureFile): #check if the feature file has been created
			with open(pebbleFeatureFile, "w") as File:
				# File.write("timestamp_1,timestamp_2,x_max,x_min,x_mean,x_std,x_fft_mean,x_fft_0_1_max,x_fft_mean_0_1,x_fft_1_3_max,x_fft_mean_1_3,x_fft_3_10_max,x_fft_mean_3_10,x_teager_mean,x_teager_max,y_max,y_min,y_mean,y_std,y_fft_mean,y_fft_0_1_max,y_fft_mean_0_1,y_fft_1_3_max,y_fft_mean_1_3,y_fft_3_10_max,y_fft_mean_3_10,y_teager_mean,y_teager_max,z_max,z_min,z_mean,z_std,z_fft_mean,z_fft_0_1_max,z_fft_mean_0_1,z_fft_1_3_max,z_fft_mean_1_3,z_fft_3_10_max,z_fft_mean_3_10,z_teager_mean,z_teager_max")
				File.write(FeatureList)
				# File.write("\n")
		connection = connectRecv(host, PORT, networkNum, None)
		connection.settimeout(5)
		# Message = connection.recv(1024).split(",")
		Message = connection.recv(2048)
		# print Message
		if len(Message)>= 2: 
			# print "Features received"
			with open(pebbleFeatureFile, "a") as File:
				File.write(Message)
				File.write("\n")

		try: #construct input array
			Message = str(Message)
			Message = Message.split(',')
			Message = numpy.asfarray(Message,float)
			print "Feature Recieved"
			print "length of InputArray = " + str(len(FeatureInputArray))
			# print Message
			if(len(Message) == 77):
				FeatureInputArray = numpy.vstack((FeatureInputArray, Message[2:]))
				# print FeatureInputArray
				if(len(FeatureInputArray) == 40):
					try: #run .exe script
						classifier = ["C:\Nutta\Local_Data\BESI\classifyFeatureArray" + '\\' +"application\classifyFeatureArray.exe"]
						proc = subprocess.Popen(classifier, stdin = subprocess.PIPE, stdout = subprocess.PIPE,)
						print proc.communicate(FeatureInputArray[1:]) #print output of the .exe
					except Exception as err:
						print err
						print "Error in AgitationClassifier"
						pass

		except Exception as err:
			print err
			print "Error in Constructing Input Arrays"
			pass

	except Exception as err:
		print err
		print "continuing..."
		pass
