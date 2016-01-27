#Fetch XML and write to csv

import os
import time
import urllib.request
import calendar
import threading
import xml.etree.cElementTree as cET

writefilemode = "w"
getagency = "ttc"
getroute = "511"
requestime = str(calendar.timegm(time.gmtime()))

class windowThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.sigterm = False
    def run(self):
        sigterm = input("Pressing enter at any time suspends the program...\n")
        self.sigterm = True
        return

def main():
    rootdir = os.path.dirname(os.path.realpath(__file__))
    writedir = rootdir + "/write" 
    currdate = time.strftime("%d-%b-%Y")
    currtime = time.strftime("%H%Mh")
        
    if not os.path.isdir(writedir):
        os.makedirs(writedir)
        
    datawritefile = open(writedir + "/" + currdate + ".csv", writefilemode)
    datawritefile.write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
    datawritefile = {}
    unwrittenvehicles = {}
    
    thread1 = windowThread(1, "Thread-1", 1)
    thread1.start()
    
    loop_flag = threading.Event()
    event_count = 0
    while not (loop_flag.wait(timeout=3)):
        requestime = str(calendar.timegm(time.gmtime()))
        event_count += 1
        #print("http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=" + getagency + "&r=" + getroute + "&t=" + requestime)
        with urllib.request.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=" + getagency + "&r=" + getroute + "&t=" + requestime) as response:
            xmlRESP = response.read()
            root = cET.fromstring(xmlRESP)
            for child in root:
                if child.tag == "vehicle":
                    try:
                        if not child.attrib["id"] in unwrittenvehicles:
                            append_data = {"lon":child.attrib["lon"], "lat":child.attrib["lat"], "posix":requestime}
                            unwrittenvehicles.update({child.attrib["id"]:[append_data]})
                        elif (child.attrib["lon"] != unwrittenvehicles[child.attrib["id"]][-1]["lon"]) and (child.attrib["lat"] != unwrittenvehicles[child.attrib["id"]][-1]["lat"]):
                            append_data = {"lon":child.attrib["lon"], "lat":child.attrib["lat"], "posix":requestime}
                            unwrittenvehicles[child.attrib["id"]].append(append_data)
                    except:
                        pass
            print(unwrittenvehicles)
            
        if event_count % 100 == 0:
            print("Flushing to file...")
                    
            for id, elem in unwrittenvehicles.items():
                if not id in datawritefile:
                    newwritefile = open(writedir + "/" + currdate + "-" + id + ".csv", writefilemode)
                    datawritefile.update({id:newwritefile})
                    datawritefile[id].write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
                    datawritefile[id].write("POSIX,lon,lat\n")
                    
                while len(elem) > 1: #don't write the last item, save it for reference.
                    item = elem.pop(0)
                    datawritefile[id].write(item["posix"] + "," + item["lon"] + "," + item["lat"] + "\n")
            
        if (thread1.sigterm):
            print("Terminating")
            for activefile in datawritefile:
                datawritefile[activefile].close()
            break
    
    print("Successful termination")
if __name__ == "__main__":
    try:
        main()
        
    except:
        print("Unhandled Error.")
        raise