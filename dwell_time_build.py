# This script is designed to use csv data containing stop locations and csv data containing GPS traces to estimate vehicle dwell times at those stops.

import os
import time
import calendar
import csv
from math import radians, cos, sin, asin, sqrt
import datetime

AVG_EARTH_RADIUS = 6371  # in km
NEAR_DIST = 0.05 #km
SPEED_MAX = 5 #kph speed defined as maximum to be considered stationary/dwelling. 
GMT_OFFSET = -5 #to convert localtime to GMT

writefilemode = "w"
getagency = "ttc"
getroute = "501"
requestime = str(calendar.timegm(time.gmtime()))
stopdata = []
currdate = time.strftime("%d-%b-%Y")
currtime = time.strftime("%H%Mh")
rootdir = os.path.dirname(os.path.realpath(__file__))
writedir = rootdir + "/write/auxdata" #write results to auxdata.
readdir = rootdir + "/read" #data is under /data, stops are stops.csv

def main():   
    print("Dwell time Estimator... Loading!")     
    if not os.path.isdir(writedir):
        os.makedirs(writedir)
        
    stopsfile = readdir + "/STOPS.csv"
    stopslist = []
    with open(stopsfile) as csvfile:
        csvparse = csv.reader(csvfile, delimiter = ',', quotechar='|')
        # title, lon, lat, stopid, tag
        for row in csvparse:
            if(row[0] == "title"):
                continue
            else:
                stopitem = {'title':row[0], 'lon':float(row[1]), 'lat':float(row[2]), 'stopID':row[3], 'tag':row[4], 'dir':row[5], 'nearby':{}, "dwells":[]}
                stopslist.append(stopitem)
                             
    transitdata = readdir + "/data"
    print("    Loading GPS Files...") 
    for files in os.listdir(transitdata):
        print("        ..." + files) 
        iterator = 0 #used to determine direction by saving the fifth point.
        prevLon = 0 #used to determine direction by saving longitude
        currDirection = False
        fileloc = transitdata + "/" + files
        if files.endswith(".csv"):
            streetcar_num = files.split('-')[3].split('.')[0] #hacky way to get the last item of the file title which is the streetcar number.
            with open(fileloc) as csvfile:
                csvparse = csv.reader(csvfile, delimiter = ',', quotechar='|')
                # posix, lon, lat
                for row in csvparse:
                    if (not row[0].isdigit()): #check for numeric on the posix column.
                        continue
                    datapoint = {'posix':int(row[0]), 'lon':float(row[1]), 'lat':float(row[2])}
                    #setup to check point
                    currDirection = 'E' if (datapoint['lon'] - prevLon < 0) else 'W'
                    if (iterator % 5 == 0):
                        prevLon = datapoint['lon']
                        
                    #check list
                    for stopitem in stopslist:
                        if (currDirection == stopitem['dir'] and
                            haversine((datapoint['lat'], datapoint['lon']), (stopitem['lat'], stopitem['lon'])) < NEAR_DIST):
                            if streetcar_num in stopitem['nearby']:
                                stopitem['nearby'][streetcar_num].append(datapoint)
                            else:
                                stopitem['nearby'][streetcar_num] = [datapoint]
                            break;
                    iterator += 1
    print("    Analysing Dwell Times...") 
    for stops in stopslist:
        for streetcar, streetcarstopped in stops['nearby'].items():
            prv = None
            dwell = 0
            append = False
            for entry in streetcarstopped:
                append = False
                if(prv == None):
                    prv = entry
                    continue
                time = entry['posix'] - prv['posix']
                if (time < 180 and time >= 0): #assume that 180 is reasonable for GPS speed update. 180s dwell time is also upper of reasonable.
                    speed = haversine((entry['lat'], entry['lon']), (prv['lat'], prv['lon'])) / (time/3600) #kph
                    if (speed < SPEED_MAX):
                        dwell += time
                    elif (dwell != 0): #the previous entry no longer is a dwell time.
                        stops['dwells'].append({"posix":entry['posix'], "time":dwell})
                        append = True
                        dwell = 0
                else: #append whatever dwelltime has been saved, even if zero (still contrinbutes to avg)
                    stops['dwells'].append({"posix":entry['posix'], "time":dwell})
                    append = True
                    dwell = 0
                prv = entry #advance the previous pointer.
            
            #save the last dwell time    
            if (append):
                stops['dwells'].append({"posix":entry['posix'], "time":dwell})
    
    print("    Writing Files and Estimating Average Dwell Time...") 
    newwritefile = open(writedir + "/" + currdate + "-DWELLS-" + getroute + ".csv", writefilemode)
    newwritefile.write("Dwell times Data Parsed on " + currdate + "\n")
    newwritefile.write("title,lon,lat,stopid,tag,avg_dwell,am_avg_dwell,pm_avg_dwell," 
                       + "NZavg_dwell,pm_NZzvg,am_NZavg,avg_count,am_count,pm_count,all_zeros,am_zeros,pm_zeros\n")
    for stops in stopslist:  
        #calculate dwell times.
        straight_avg = 0
        straight_NZavg = 0
        straight_count = 0
        straight_zeros = 0
        am_avg = 0
        am_NZavg = 0
        am_count = 0
        am_zeros = 0
        pm_avg = 0
        pm_NZavg = 0
        pm_count = 0
        pm_zeros = 0
        pm_peak_start = datetime.time(15+GMT_OFFSET,30)
        pm_peak_end = datetime.time(18+GMT_OFFSET,30)
        am_peak_start = datetime.time(6+GMT_OFFSET,30)
        am_peak_end = datetime.time(9+GMT_OFFSET,30)
        for dwells in stops["dwells"]:
            entrytime = datetime.datetime.fromtimestamp(dwells["posix"])
            if (entrytime.time() > pm_peak_start and entrytime.time() < pm_peak_end):
                pm_avg += dwells["time"]
                pm_count += 1
                pm_zeros = pm_zeros + 1 if dwells["time"] == 0 else pm_zeros
            if (entrytime.time() > am_peak_start and entrytime.time() < am_peak_end):
                am_avg += dwells["time"]
                am_count += 1
                am_zeros = am_zeros + 1 if dwells["time"] == 0 else am_zeros
                
            straight_avg += dwells["time"]
            straight_count += 1
            straight_zeros = straight_zeros + 1 if dwells["time"] == 0 else straight_zeros
        
        straight_NZavg = straight_avg / (straight_count - straight_zeros) if straight_count > straight_zeros else "NO_ENTRY"
        am_NZavg = am_avg / (am_count - am_zeros) if am_count > am_zeros else "NO_ENTRY"
        pm_NZavg = pm_avg / (pm_count - pm_zeros) if pm_count > pm_zeros else "NO_ENTRY"
            
        straight_avg = straight_avg / straight_count if straight_count != 0 else "NO_ENTRY"
        pm_avg = pm_avg / pm_count if pm_count != 0 else "NO_ENTRY"
        am_avg = am_avg / am_count if am_count != 0 else "NO_ENTRY"
              
        
        newwritefile.write(stops["title"] + "," + str(stops["lon"]) + "," 
                           + str(stops["lat"]) + "," + stops["stopID"] 
                           + "," + stops["tag"] + "," + str(straight_avg) 
                           + "," + str(am_avg) + "," +  str(pm_avg)
                           + "," + str(straight_NZavg) + "," +  str(am_NZavg)
                           + "," + str(pm_NZavg) 
                           + "," + str(straight_count) + "," +  str(am_count)
                           + "," + str(pm_count) 
                           + "," + str(straight_zeros) + "," +  str(am_zeros)
                           + "," + str(pm_zeros) + "\n")
    newwritefile.close()
    print("DONE!")

def haversine(point1, point2, miles=False):
    #from https://pypi.python.org/pypi/haversine
    """ Calculate the great-circle distance bewteen two points on the Earth surface.

    :input: two 2-tuples, containing the latitude and longitude of each point
    in decimal degrees.

    Example: haversine((45.7597, 4.8422), (48.8567, 2.3508))

    :output: Returns the distance bewteen the two points.
    The default unit is kilometers. Miles can be returned
    if the ``miles`` parameter is set to True.

    """
    # unpack latitude/longitude
    lat1, lng1 = point1
    lat2, lng2 = point2

    # convert all latitudes/longitudes from decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))

    # calculate haversine
    lat = lat2 - lat1
    lng = lng2 - lng1
    d = sin(lat * 0.5) ** 2 + cos(lat1) * cos(lat2) * sin(lng * 0.5) ** 2
    h = 2 * AVG_EARTH_RADIUS * asin(sqrt(d))
    if miles:
        return h * 0.621371  # in miles
    else:
        return h  # in kilometers
        
if __name__ == "__main__":
    try:
        main()
        
    except:
        print("Unhandled Error.")            
        raise