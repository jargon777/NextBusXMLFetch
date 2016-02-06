#Fetch XML and write to csv

import os
import time
import urllib.request
import calendar
import threading
import xml.etree.cElementTree as cET

writefilemode = "a"
getagency = "ttc"
getroute = "501"
requestime = str(calendar.timegm(time.gmtime()))
datawritefile = {}
unwrittenvehicles = {}
currdate = time.strftime("%d-%b-%Y")
currtime = time.strftime("%H%Mh")
rootdir = os.path.dirname(os.path.realpath(__file__))
writedir = rootdir + "/write" 

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
    if not os.path.isdir(writedir):
        os.makedirs(writedir)
        
    
    
    #extra thread that runs, checking if input has been made to the console. If so, it sets a variable to be True, indicating that the main loop should cleanup.
    thread1 = windowThread(1, "Thread-1", 1)
    thread1.start()
    
    loop_flag = threading.Event()
    event_count = 0
    while not (loop_flag.wait(timeout=3)):
        requestime = str(calendar.timegm(time.gmtime()))
        event_count += 1
        #print("http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=" + getagency + "&r=" + getroute + "&t=" + requestime)
        try:
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
                            pass #bad programmatic practice, I know.
                print(unwrittenvehicles)
        except:
            print("Contact with electronic resource lost...") #well we've failed.
        
        #every so often, write the data that's been collected to file.    
        if event_count % 100 == 0:
            print("Flushing to file...")
                    
            for idtag, elem in unwrittenvehicles.items():
                if not idtag in datawritefile:
                    newwritefile = open(writedir + "/" + currdate + "-" + idtag + ".csv", writefilemode)
                    datawritefile.update({idtag:newwritefile})
                    datawritefile[idtag].write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
                    datawritefile[idtag].write("POSIX,lon,lat\n")
                    
                while len(elem) > 1: #don't write the last item, save it for reference.
                    item = elem.pop(0)
                    datawritefile[idtag].write(item["posix"] + "," + item["lon"] + "," + item["lat"] + "\n")
        
        #check if the flag has been made, clean up by closing all open file handles.
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
        if not datawritefile:
            try:
                print("Flushing to file...")        
                for id, elem in unwrittenvehicles.items():
                    if not id in datawritefile:
                        newwritefile = open(writedir + "/" + currdate + "-" + id + ".csv", writefilemode)
                        datawritefile.update({id:newwritefile})
                        datawritefile[id].write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
                        datawritefile[id].write("POSIX,lon,lat\n")
                        
                    while len(elem) > 0: #don't write the last item, save it for reference.
                        item = elem.pop(0)
                        datawritefile[id].write(item["posix"] + "," + item["lon"] + "," + item["lat"] + "\n")
                
                print("Flushing files")
                for activefile in datawritefile:
                    datawritefile[activefile].close()
            except:
                print("Failed to flush!")
            
        raise