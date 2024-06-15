import numpy as np
from algorithm import algorithm
import qoeEstimation as qoeEst

def getBandForQoECli(host, desQoE):
    qoeEstimator = qoeEst.ClientQoeEstimator(host)
    qoe = np.array([qoeEstimator.estQoEb(x) for x in qoeEstimator.yAxis])
    # print(qoe)
    if host == 'hostLVD':
        desQoE += 0.1
    idx = np.abs(qoe - desQoE).argmin()
    while qoe[idx] < desQoE:
        idx += 1
    # print('\t-> Target:', desQoE, '; Selected:', qoe[idx], '; Bitrate:', qoeEstimator.yAxis[idx])
    return int(qoeEstimator.yAxis[idx])


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
    ssh = clientAdmissionHost(simTime, 0.084, 60) #1
    vip = clientAdmissionHost(simTime, 0.5, 60) #2
    vid = clientAdmissionHost(simTime, 0.67, 60) #3
    lvd = clientAdmissionHost(simTime, 0.34, 60) #4
    fdo = clientAdmissionHost(simTime, 0.084, 60) #5
    return {"SSH": ssh,"VIP": vip, "VID": vid,"LVD": lvd,"FDO": fdo}

#print(allHostTypesAdmission(10))

#ssh, vip, vid, lvd, fdo = allHostTypesAdmission(10)
#print(ssh)


#print(np.unique(np.concatenate((ssh[0], ssh[1], vip[0], vip[1], vid[0], vid[1], lvd[0], lvd[1], fdo[0], fdo[1]))))



def recalc(present, last):
    sliceResources = algorithm({'sliceSSH' : {'hostSSH' : present["SSH"]}, 'sliceVIP' : {'hostVIP' : present["VIP"]}, 'sliceVID' : {'hostVID' : present["VID"]}, 'sliceLVD' : {'hostLVD' : present["LVD"]}, 'sliceFDO' : {'hostFDO' : present["FDO"]}}, {'sliceSSH' : last['sliceSSH'], 'sliceVIP' : last['sliceVIP'], 'sliceVID' : last['sliceVID'], 'sliceLVD' : last['sliceLVD'], 'sliceFDO' : last['sliceFDO']}, 1000, 0.0, 0, 1000, 100, False)
    return sliceResources

def calculateEvents(hosts, maxThroughput, desiredQoE):
    tmp = [{'sliceSSH': 20, 'sliceVIP': 20, 'sliceVID': 20, 'sliceLVD': 20, 'sliceFDO': 20}]
    changeTimes = np.unique(np.concatenate((hosts["SSH"][0], hosts["SSH"][1], hosts["VIP"][0], hosts["VIP"][1], hosts["VID"][0], hosts["VID"][1], hosts["LVD"][0], hosts["LVD"][1], hosts["FDO"][0], hosts["FDO"][1])))
    reqBitratesPerType={}
    ceilBitrates = {}
    assuredBitrates = {}
    for host in hosts:
        reqBitratesPerType[host] = int(getBandForQoECli('host'+host, desiredQoE))
        if host == 'VID':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.25)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.85)
        elif host == 'LVD':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.25)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.55)
        elif host == 'FDO':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.25)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 1.0)
        elif host == 'SSH':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.0)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.5)
        elif host == 'VIP':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 2.0)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.7)
        elif host == 'cVIP':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 2.0)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.7)
        print('For a QoE of ' + str(desiredQoE) + ' ' + str(host) + ' needs ' + str(reqBitratesPerType[host]) + ' kbps. It translates to a GBR of ' + str(assuredBitrates['host'+host]) + ' kbps and a MBR of ' + str(ceilBitrates['host'+host]) + 'kbps.')

    newChangeTimes = []
    sliceRates = {"sliceSSH": [],"sliceVIP": [],"sliceVID": [],"sliceLVD": [],"sliceFDO": [],}
    present =  {"SSH": 1,"VIP": 1,"VID": 1,"LVD": 1,"FDO": 1,}
    rejected = 0
    total = maxThroughput * 1000
    for t in changeTimes:
        print("Generating " + str(np.where(changeTimes==t)[0]/len(changeTimes) * 100) + "%")
        print(present)
        for host in hosts:
            x=0
            #COMING
            for a in np.arange(len(hosts[host][0])):
                #print(a, a-x)
                if hosts[host][0][a-x] == t:
                    if total > assuredBitrates[host]:
                        present[host]+=1
                        total -= assuredBitrates[host]
                    else:
                        rejected += 1
                        hosts[host] = np.delete(hosts[host], a-x, axis=1)
                        x+=1      
            #LEAVING
            for a in np.arange(len(hosts[host][0])):
                if hosts[host][1][a] == t:
                    present[host]-=1
                    total += assuredBitrates[host]
        # if t > maxTime:




            # break

        old = tmp[0]
        tmp = recalc(present, tmp[0])
        #print(tmp[0])
        if tmp[0] != old:
            newChangeTimes.append(t)
            for sli in tmp[0]:
                sliceRates[sli].append(tmp[0][sli])
    print(rejected)            
    return hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected


hosts = allHostTypesAdmission(10)
hosts, req, newChangeTimes, rates, rejected = calculateEvents(hosts, 100, 3.5)

print(rates)


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