#Fetch XML and write to csv

import os
import time
import urllib.request
import calendar
import threading

writefilemode = "w"
getagency = "ttc"
getroute = "511"
requestime = str(calendar.timegm(time.gmtime()))


def main():
    rootdir = os.path.dirname(os.path.realpath(__file__))
    writedir = rootdir + "/write" 
    currdate = time.strftime("%d-%b-%Y")
    currtime = time.strftime("%H%Mh")
        
    if not os.path.isdir(writedir):
        os.makedirs(writedir)
        
    datawritefile = open(writedir + "/" + currdate + ".csv", writefilemode)
    datawritefile.write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
    
    loop_flag = threading.Event()
    while not (loop_flag.wait(timeout=5)):
        with urllib.request.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=" + getagency + "&r=" + getroute + "&t=" + requestime) as response:
            xmlRESP = response.read()
            print(xmlRESP)
    
    

if __name__ == "__main__":
    try:
        main()
        
    except:
        print("Unhandled Error.")
        raise