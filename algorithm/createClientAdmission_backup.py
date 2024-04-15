import numpy as np
from algorithm import algorithm

def generate_poisson_events(rate, time_duration):
    num_events = np.random.poisson(rate * time_duration)
    event_times = np.sort(np.random.randint(0, time_duration, num_events))
    inter_arrival_times = np.diff(event_times)
    return num_events, event_times, inter_arrival_times

def clientAdmissionHost(simTime, arrivalRate, serviceRate):
    startTimes=generate_poisson_events(arrivalRate,simTime-1)[1]
    #startTime=np.random.randint(1,8,clients)
    numClients=len(startTimes)
    #print(startTimes)
    #print(numClients)

    serviceTimes=np.random.poisson(serviceRate,numClients)
    endTimes=startTimes+serviceTimes+1
    #numApps = np.arange(numClients) 

    return np.vstack((startTimes, endTimes))

def allHostTypesAdmission(simTime):
    ssh = clientAdmissionHost(simTime, 5, 50) #1
    vip = clientAdmissionHost(simTime, 2, 60) #2
    vid = clientAdmissionHost(simTime, 1, 70) #3
    lvd = clientAdmissionHost(simTime, 0.3, 85) #4
    fdo = clientAdmissionHost(simTime, 0.2, 100) #5
    return {"ssh": ssh,"vip": vip, "vid": vid,"lvd": lvd,"fdo": fdo}

#print(allHostTypesAdmission(10))

#ssh, vip, vid, lvd, fdo = allHostTypesAdmission(10)
#print(ssh)


#print(np.unique(np.concatenate((ssh[0], ssh[1], vip[0], vip[1], vid[0], vid[1], lvd[0], lvd[1], fdo[0], fdo[1]))))



def recalc(present, last):
    sliceResources = algorithm({'sliceSSH' : {'hostSSH' : present[0]}, 'sliceVIP' : {'hostVIP' : present[1]}, 'sliceVID' : {'hostVID' : present[2]}, 'sliceLVD' : {'hostLVD' : present[3]}, 'sliceFDO' : {'hostFDO' : present[4]}}, {'sliceSSH' : last['sliceSSH'], 'sliceVIP' : last['sliceVIP'], 'sliceVID' : last['sliceVID'], 'sliceLVD' : last['sliceLVD'], 'sliceFDO' : last['sliceFDO']}, 1000, 0.0, 0, 1000, 100, False)
    return sliceResources

def calculateEvents(hosts, maxThroughput):
    tmp = [{'sliceSSH': 20, 'sliceVIP': 20, 'sliceVID': 20, 'sliceLVD': 20, 'sliceFDO': 20}]
    changeTimes = np.unique(np.concatenate((hosts["ssh"][0], hosts["ssh"][1], hosts["vip"][0], hosts["vip"][1], hosts["vid"][0], hosts["vid"][1], hosts["lvd"][0], hosts["lvd"][1], hosts["fdo"][0], hosts["fdo"][1])))
    newChangeTimes = []
    rates = []
    present = [1,1,1,1,1]
    rejected = 0
    total = maxThroughput * 1000
    for t in changeTimes:
        print("Generating " + str(np.where(changeTimes==t)[0]/len(changeTimes) * 100) + "%")
        #COMING
        x=0
        for a in np.arange(len(ssh[0])):
            if ssh[0][a-x] == t:
                if total > 10:
                    present[0]+=1
                    total -= 10
                else:
                    rejected += 1
                    ssh = np.delete(ssh, a-x, axis=1)
                    x+=1
                                 
        x=0   
        for b in np.arange(len(vip[0])):
            if vip[0][b-x] == t:
                if total > 30:
                    present[1]+=1
                    total -= 30
                else:
                    rejected += 1
                    vip = np.delete(vip, b-x, axis=1)
                    x+=1
                
        x=0
        for c in np.arange(len(vid[0])):
            if vid[0][c-x] == t:
                if total > 1120:
                    present[2]+=1
                    total -= 1120
                else:
                    rejected += 1
                    vid = np.delete(vid, c-x, axis=1)
                    x+=1
                
        x=0        
        for d in np.arange(len(lvd[0])):
            if lvd[0][d-x] == t:
                if total > 1820:
                    present[3]+=1
                    total -= 1820
                else:
                    rejected += 1
                    lvd = np.delete(lvd, d-x, axis=1)
                    x+=1
                
        x=0        
        for e in np.arange(len(fdo[0])):
            if fdo[0][e-x] == t:
                if total > 2240:
                    present[4]+=1
                    total -= 2240
                else:
                    rejected += 1
                    fdo = np.delete(fdo, e-x, axis=1)
                    x+=1
                
                

        #LEAVING
        for a in np.arange(len(ssh[0])):
            if ssh[1][a] == t:
                present[0]-=1
                total += 10
                
                
        for b in np.arange(len(vip[0])):
            if vip[1][b] == t:
                present[1]-=1
                total += 30
                

        for c in np.arange(len(vid[0])):
            if vid[1][c] == t:
                present[2]-=1
                total += 1120
                
                
        for d in np.arange(len(lvd[0])):
            if lvd[1][d] == t:
                present[3]-=1
                total += 1820
                
                
        for e in np.arange(len(fdo[0])):
            if fdo[1][e] == t:
                present[4]-=1
                total +=  2240
                
        old = tmp[0]
        tmp = recalc(present, tmp[0])
        #print(tmp[0])
        if tmp[0] != old:
            newChangeTimes.append(t)
            rates.append(tmp[0])
            
    return ssh, vip, vid, lvd, fdo, newChangeTimes, rates, rejected


hosts = allHostTypesAdmission(10)
ssh, vip, vid, lvd, fdo, newChangeTimes, rates, rejected = calculateEvents(hosts, 100)

def startStopTimes(ssh, vip, vid, lvd, fdo, changeTimes, rates):
    configString = ""
    for a in np.arange(len(ssh[0])):
        configString += '**.hostSSH[*].app['+ str(a) +'].startTime = ' + str(ssh[0][a]) + 's\n' 
        configString += '**.hostSSH[*].app['+ str(a) +'].stopTime = ' + str(ssh[1][a]) + 's\n'
    
    for a in np.arange(len(vip[0])):
        configString += '**.serverVIP.app['+ str(a) +'].startTime = ' + str(vip[0][a]) + 's\n' 
        configString += '**.serverVIP.app['+ str(a) +'].stopTime = ' + str(vip[1][a]) + 's\n'

    for a in np.arange(len(vid[0])):
        configString += '**.hostVID[*].app['+ str(a) +'].startTime = ' + str(vid[0][a]) + 's\n' 
        configString += '**.hostVID[*].app['+ str(a) +'].stopTime = ' + str(vid[1][a]) + 's\n'
    
    for a in np.arange(len(lvd[0])):
        configString += '*.hostLVD[*].app['+ str(a) +'].startTime = ' + str(lvd[0][a]) + 's\n' 
        configString += '*.hostLVD[*].app['+ str(a) +'].stopTime = ' + str(lvd[1][a]) + 's\n'
    
    for a in np.arange(len(fdo[0])):
        configString += '*.hostFDO[*].app['+ str(a) +'].startTime = ' + str(fdo[0][a]) + 's\n' 
        configString += '*.hostFDO[*].app['+ str(a) +'].stopTime = ' + str(fdo[1][a]) + 's\n'
    
    configString += ".hostFDO[0].ppp[0].queue.scheduler.changeTimes = [" + ', '.join(str(c) for c in changeTimes) + "]\n"
    
    for t in np.arange(len(rates)):
        print(" Rate" + str(t+1) + ": "+ str(rates[t]["sliceSSH"]))
        #print(rates[i]["sliceSSH"])


    return configString

#print(startStopTimes(ssh, vip, vid, lvd, fdo, newChangeTimes, rates))


#print(generate_poisson_events(1, 10)[1])

#print(clientAdmissionHost(20,1,1))
#print(np.random.exponential(scale=3,size=10))
#print(np.random.normal(loc=0,scale=1,size=10))
# liteCbaselineTestTokenQoS_base:
#*.hostFDO[*].app[0].startTime = uniform(0.01s,1s) # time first session begins
#*.hostFDO[*].app[0].stopTime = -1s # time of finishing sending, negative values mean forever



# Starttimes
# Stoptimes

# Changetimes
# Present appnr + hosttype