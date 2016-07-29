# fetch XML of stops and convert to EXCEL.
# It is designed to work with NextBus's AVL data feed, and has been tested for the TTC.

import os
import time
import urllib.request
import calendar
import xml.etree.cElementTree as cET

writefilemode = "w"
getagency = "ttc"
getroute = "501"
requestime = str(calendar.timegm(time.gmtime()))
stopdata = []
currdate = time.strftime("%d-%b-%Y")
currtime = time.strftime("%H%Mh")
rootdir = os.path.dirname(os.path.realpath(__file__))
writedir = rootdir + "/write/auxdata" 
rm = True

def main():        
    if not os.path.isdir(writedir):
        os.makedirs(writedir)
    
    event_count = 0
    requestime = str(calendar.timegm(time.gmtime()))
    event_count += 1
    print("http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=" + getagency + "&r=" + getroute)
    try:
        with urllib.request.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=" + getagency + "&r=" + getroute) as response:
            xmlRESP = response.read()
            root = cET.fromstring(xmlRESP)
            for child in root:
                #print(child.tag)
                if child.tag == "route":
                    for baby in child:
                        if baby.tag == "stop":
                            for attrib in baby.attrib:
                                print(attrib)
                            if "stopId" in baby.attrib:
                                stopID = baby.attrib["stopId"] #stopID not guarunteed.
                            else:
                                stopID = ""
                            stop = {"name":baby.attrib["title"], "stopID":stopID, "lat":baby.attrib["lat"], "lon":baby.attrib["lon"], "tag":baby.attrib["tag"]}
                            stopdata.append(stop)
                
            print(stopdata)
    except:
        print("Contact with electronic resource lost...") #well we've failed.
    
    print("Flushing to file...")
                
    newwritefile = open(writedir + "/" + currdate + "-STOPS-" + getroute + ".csv", writefilemode)
    newwritefile.write("XML Data Parsed for " + currdate + "Starting at: " + currtime + "\n")
    newwritefile.write("title,lon,lat,stopid,tag\n")
    for elem in stopdata:    
        newwritefile.write(elem["name"] + "," + elem["lon"] + "," + elem["lat"] + "," + elem["stopID"] + "," + elem["tag"] + "\n")
    newwritefile.close()
    
    
    print("Successful termination")
if __name__ == "__main__":
    try:
        main()
        
    except:
        print("Unhandled Error.")
        '''
        if not stopdata:
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
                '''
            
        raise