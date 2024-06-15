import json, os, sys
import xml.etree.ElementTree as ET
import numpy as np
import math
import qoeEstimation as qoeEst
import csv
import pandas as pd
from algorithm import algorithm



# TODO : qoeEst.ClientQoEEstimator
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

# for app in ['hostVID', 'hostLVD', 'hostFDO', 'hostVIP', 'hostSSH']:
#     print(app)
#     for tQ in [3.0, 3.5, 4.0]:
#         getBandForQoECli(app, tQ)

#print(getBandForQoECli('hostcVIP', 3.5)*100/1000)
# default: ceilMultiplier = 1.25; guaranteeMultiplier = 1.0

#New generation of admission times
def generate_poisson_events(rate, time_duration):
    num_events = np.random.poisson(rate * time_duration)
    event_times = np.sort(np.random.randint(1, time_duration, num_events))
    inter_arrival_times = np.diff(event_times)
    return num_events, event_times, inter_arrival_times

def clientAdmissionHost(simTime, arrivalRate, serviceRate, type):
    startTimes=generate_poisson_events(arrivalRate,simTime-1)[1]
    #startTime=np.random.randint(1,8,clients)
    numClients=len(startTimes)
    #print(startTimes)
    #print(numClients)

    serviceTimes=np.random.poisson(serviceRate,numClients)
    endTimes=startTimes+serviceTimes+1
    #numApps = np.arange(numClients)
    for i,endTime in enumerate(endTimes):
        if endTime > simTime-1:
            endTimes[i] = simTime-1
    
    for i, startTime in enumerate(startTimes):
        if type == 'VID' and startTime > simTime-150:
            startTimes = startTimes[:i]
            endTimes = endTimes[:i]
            break
        if type == 'LVD' and startTime > simTime-100:
            startTimes = startTimes[:i]
            endTimes = endTimes[:i]
            break
        elif startTime > simTime-50:
            startTimes = startTimes[:i]
            endTimes = endTimes[:i]
            break
    print(type, startTimes, endTimes)

    return np.vstack((startTimes, endTimes))

#Do something like 320s for video,200s live, 250s FD, 300 VoIP, 150s SSH, make arrival rates match to get same application % split
def allHostTypesAdmission(simTime):
    ssh = clientAdmissionHost(simTime, 0.05, 150, 'SSH') # SSH: 7.5 in 400s 7.5/150 = 0.05
    vip = clientAdmissionHost(simTime, 0.15, 300, 'VIP') # VIP: 45 in 400s 45/300 = 0.15
    vid = clientAdmissionHost(simTime, 0.1875, 320, 'VID') # VID: 60 in 400s 60/320 = 0.1875  Start only before 300s and no new after 300s
    lvd = clientAdmissionHost(simTime, 0.15, 200, 'LVD') # LVD: 30 in 400s 30/200 = 0.15
    fdo = clientAdmissionHost(simTime, 0.03, 250, 'FDO') # FDO: 7.5 in 400s 7.5/250 = 0.03
    return {"SSH": ssh,"VIP": vip, "VID": vid,"LVD": lvd,"FDO": fdo}

# left = 100
# present =  {"SSH": 10,"VIP": 40,"VID": 50,"LVD": 28,"FDO": 5}
# tmp = [{'sliceSSH': left/5, 'sliceVIP': left/5, 'sliceVID': left/5, 'sliceLVD': left/5, 'sliceFDO': left/5}]
# print(recalc(present, tmp[0], left))

#ssh, vip, vid, lvd, fdo = allHostTypesAdmission(10)
#print(ssh)


#print(np.unique(np.concatenate((ssh[0], ssh[1], vip[0], vip[1], vid[0], vid[1], lvd[0], lvd[1], fdo[0], fdo[1]))))

def recalc(present, last, left):
    sliceResources = algorithm({'sliceSSH' : {'hostSSH' : present["SSH"]}, 'sliceVIP' : {'hostVIP' : present["VIP"]}, 'sliceVID' : {'hostVID' : present["VID"]}, 'sliceLVD' : {'hostLVD' : present["LVD"]}, 'sliceFDO' : {'hostFDO' : present["FDO"]}}, {'sliceSSH' : last['sliceSSH'], 'sliceVIP' : last['sliceVIP'], 'sliceVID' : last['sliceVID'], 'sliceLVD' : last['sliceLVD'], 'sliceFDO' : last['sliceFDO']}, 1000, 0.0, 0, 1000, left, False)
    return sliceResources

def calculateEvents(hosts, maxThroughput, desiredQoE, algo, maxSimTime, configName):
    # CNSM PAPER:
    #tmp = [{'sliceSSH': 0.053, 'sliceVIP': 0.964, 'sliceVID': 47.991, 'sliceLVD': 38.993, 'sliceFDO': 11.997}]
    #sliceRates = {"sliceSSH": [0.053],"sliceVIP": [0.964],"sliceVID": [47.991],"sliceLVD": [38.993],"sliceFDO": [11.997]}


    tmp = {'sliceSSH': 20, 'sliceVIP': 20, 'sliceVID': 20, 'sliceLVD': 20, 'sliceFDO': 20}
    present =  {"SSH": 0,"VIP": 0,"VID": 0,"LVD": 0,"FDO": 0}
    sliceRates = {"sliceSSH": [],"sliceVIP": [],"sliceVID": [],"sliceLVD": [],"sliceFDO": []}

    # Default:
    # tmp = [{'sliceSSH': 20, 'sliceVIP': 20, 'sliceVID': 20, 'sliceLVD': 20, 'sliceFDO': 20}]
    # present =  {"SSH": 1,"VIP": 1,"VID": 1,"LVD": 1,"FDO": 1}
    #sliceRates = {"sliceSSH": [20],"sliceVIP": [20],"sliceVID": [20],"sliceLVD": [20],"sliceFDO": [20]}


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
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.50)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.6)
        elif host == 'FDO':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.25)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 1.0)
        elif host == 'VIP':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 2.0)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.8)
        elif host == 'SSH':
            ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 1.0)
            assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.5)
        
        # elif host == 'cVIP':
        #     ceilBitrates['host'+host] = int(reqBitratesPerType[host] * 2.0)
        #     assuredBitrates['host'+host] = int(reqBitratesPerType[host] * 0.7)
        print('For a QoE of ' + str(desiredQoE) + ' ' + str(host) + ' needs ' + str(reqBitratesPerType[host]) + ' kbps. It translates to a GBR of ' + str(assuredBitrates['host'+host]) + ' kbps and a MBR of ' + str(ceilBitrates['host'+host]) + 'kbps.')

    newChangeTimes = []
    totalStatic = {"SSH": 53,"VIP": 964,"VID": 47991,"LVD": 38993,"FDO": 11997}
    
    rejected =  {"SSH": 0,"VIP": 0,"VID": 0,"LVD": 0,"FDO": 0}
    total = maxThroughput * 1000
    # with open('/mnt/data/analysis/Client_admission/'+configName+'.csv', 'a+', newline="") as file:
    #         csvwriter = csv.writer(file)
    #         csvwriter.writerow(['Type', 'Clients'])
    #         csvwriter.writerow(present)
    header = ['Time', 'VID', 'LVD', 'FDO', 'VIP', 'SSH', 'RVID', 'RLVD', 'RFDO', 'RVIP', 'RSSH']
    header2 = ['Time', 'VID', 'LVD', 'FDO', 'VIP', 'SSH']
    data=[]
    resourceAllocdata=[]

    print('tester changeTimes: '+ str(len(changeTimes)))
    for t in changeTimes:
        print(t)
        if t >= maxSimTime-1: #Maxtime reached
            break
        print("Generating " + str(np.where(changeTimes==t)[0]/len(changeTimes) * 100) + "%")
        for host in hosts:
            x=0
            if algo == "static":
                #COMING
                for a in np.arange(len(hosts[host][0])):
                    #print(a, a-x)
                    if hosts[host][0][a-x] == t:
                        if totalStatic[host] > assuredBitrates['host'+host]:
                            present[host]+=1
                            totalStatic[host] -= assuredBitrates['host'+host]
                        else:
                            rejected[host] += 1
                            hosts[host] = np.delete(hosts[host], a-x, axis=1)
                            print('#####################')
                            print('tester rejected: ' + str(host)+ str(a-x) + ' at changetime ' + str(t) )
                            x+=1
                #LEAVING
                for a in np.arange(len(hosts[host][0])):
                    if hosts[host][1][a] == t:
                        present[host]-=1
                        totalStatic[host] += assuredBitrates['host'+host]
            else:
                #COMING
                for a in np.arange(len(hosts[host][0])):
                    #print(a, a-x)
                    if hosts[host][0][a-x] == t:
                        if total > assuredBitrates['host'+host]:
                            present[host]+=1
                            total -= assuredBitrates['host'+host]
                        else:
                            rejected[host] += 1
                            hosts[host] = np.delete(hosts[host], a-x, axis=1)
                            print('#####################')
                            print('tester rejected: ' + str(host)+ str(a-x) + ' at changetime ' + str(t) )
                            x+=1      
                #LEAVING
                for a in np.arange(len(hosts[host][0])):
                    if hosts[host][1][a] == t:
                        present[host]-=1
                        total += assuredBitrates['host'+host]
        print(present)
        match algo:
            case "equal":
                #print("equal split of "+ str(total))
                for type in present:
                    tmp["slice" + type] = math.floor(present[type] * assuredBitrates['host'+type] + total/5)
                #print(tmp)
            case "weighted":
                #print("weigheted split")
                for type in present:
                    split = present[type]/sum(present.values())
                    #print(type, split)
                    tmp["slice" + type] = math.floor(present[type] * assuredBitrates['host'+type] + total * split)
                #print(tmp)
            case "CNSM":
                print("CNSM split function")
                fagbr = {}
                for type in present:
                    fagbr[type] = present[type]/sum(present.values())*assuredBitrates['host'+type]
                    # print(fagbr[type])
                multiplier = maxThroughput * 1000/sum(fagbr.values())
                # print(multiplier)
                for type in present:
                    tmp["slice" + type] = math.floor(multiplier * fagbr[type])
            case "static":
                print("static reosurce allocation, no change needed")
        
        for sli in tmp:
            if (algo != "static"):
                sliceRates[sli].append(tmp[sli])
        resourceAllocdata.append([t, tmp['sliceVID'],tmp['sliceLVD'],tmp['sliceFDO'],tmp['sliceVIP'],tmp['sliceSSH']])
        if (t != 1 and algo != "static"):
            newChangeTimes.append(t)
        data.append([t, present['VID'],present['LVD'],present['FDO'],present['VIP'],present['SSH'],rejected['VID'],rejected['LVD'],rejected['FDO'],rejected['VIP'],rejected['SSH']])
        

    if(algo == "static"):
        sliceRates={"sliceSSH": [53],"sliceVIP": [964],"sliceVID": [47991],"sliceLVD": [38993],"sliceFDO": [11997]}
        resourceAllocdata = [[0, sliceRates['sliceVID'][0],sliceRates['sliceLVD'][0],sliceRates['sliceFDO'][0],sliceRates['sliceVIP'][0],sliceRates['sliceSSH'][0]],[400, sliceRates['sliceVID'][0],sliceRates['sliceLVD'][0],sliceRates['sliceFDO'][0],sliceRates['sliceVIP'][0],sliceRates['sliceSSH'][0]]]
    
    data = pd.DataFrame(data, columns=header)
    data.to_csv('/mnt/data/analysis/Pre/Client_admission/'+configName+'.csv', index=False)

    
    #print(resourceAllocdata)
    resourceAllocdata = pd.DataFrame(resourceAllocdata, columns=header2)
    resourceAllocdata.to_csv('/mnt/data/analysis/Pre/Resource_alloc/'+configName+'.csv', index=False)
        #old = tmp[0]
        # tmp = recalc(present, tmp[0])
        # #print(tmp[0])
        # if tmp[0] != old:
        #     newChangeTimes.append(t)
        #     for sli in tmp[0]:
        #         sliceRates[sli].append(tmp[0][sli])
    print(rejected)            
    return hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates


# hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(allHostTypesAdmission(400), 100, 3.5, "equal")
# print(sliceRates)


# hosts = {"SSH": np.vstack(([1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399])),
#             "VIP": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399])),
#             "VID": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200])),
#             "LVD": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399])),
#             "FDO": np.vstack(([1,1,1,1,1],[399,399,399,399,399]))
#             }
# hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(hosts, 100, 3.5, "CNSM")
# print(sliceRates)
# hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(hosts, 100, 3.5)
# print(sliceRates, newChangeTimes)

#print(recalc(present, tmp[0]))
# hosts = allHostTypesAdmission(50)
# hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected = calculateEvents(hosts, 100, 3.5)
#print([a["sliceSSH"] for a in sliceRates])
# reshapedRates = {}
# for d in sliceRates:
#     for key in d:
#         reshapedRates[key].append(d[key])
#print(sliceRates)

def simpleAdmission(availBand, desiredQoE, cliTypes, maxNumCliType, ceilMultiplier, guaranteeMultiplier):
    usedBand = 0
    numHostsPerType = {}
    reqBitratesPerType = {}
    for host in cliTypes:
        reqBitratesPerType[host] = getBandForQoECli(host, desiredQoE)
        print('For a QoE of', desiredQoE, host, 'needs', reqBitratesPerType[host])
        numHostsPerType[host] = 0
    ceilBitrates = {}
    assuredBitrates = {}
    for host in cliTypes:
        ceilBitrates[host] = reqBitratesPerType[host] * ceilMultiplier
        assuredBitrates[host] = reqBitratesPerType[host] * guaranteeMultiplier
    numSameRes = 0
    oldBand = 0
    while usedBand < availBand:
        for host in cliTypes:
            tryAdd = usedBand + assuredBitrates[host]
            if tryAdd <= availBand and numHostsPerType[host] < maxNumCliType:
                usedBand = tryAdd
                numHostsPerType[host] += 1
        if oldBand == usedBand:
            numSameRes += 1
        else:
            numSameRes = 0
        oldBand = usedBand
        if numSameRes > 10:
            break
    
    print('Hosts admitted for desired QoE of', desiredQoE, 'and link bitrate of', availBand, 'Kbps is :', numHostsPerType)
    print('This allocation will use', usedBand, 'Kbps out of available', availBand, 'Kbps')

    return numHostsPerType, assuredBitrates, ceilBitrates

# print(simpleAdmission(100000, 3, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50))
# simpleAdmission(200000, 3.5, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50)
# simpleAdmission(200000, 4, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50)

#print(simpleAdmission(100000, 2.5, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50, 2.0, 1.0))

# getBandForQoECli('hostFDO', 3)

sampleDict = {
    "id": "sample",
    "parentId": "NULL",
    "rate": 0,
    "ceil": 0,
    "burst": 2000,
    "cburst": 2000,
    "level": 1,
    "quantum": 1500,
    "mbuffer": 60
}
# {leafName:[assuredRate, ceilRate, priority, queueNum]}
def genHTBconfig(configName, linkSpeed, leafClassesConfigs):
    data = []

    fh = open('../simulations/configs/htbTree/'+configName+ ".json", "a+")

    root = sampleDict.copy()
    root["id"] = "root"
    root["rate"] = linkSpeed
    root["ceil"] = linkSpeed
    data.append(root)


    for leaf in leafClassesConfigs:
        tempDict = sampleDict.copy()
        tempDict["id"] = 'leaf' + leaf
        tempDict["parentId"] = "root"
        tempDict["rate"] = leafClassesConfigs[leaf][0]
        tempDict["ceil"] = leafClassesConfigs[leaf][1]
        tempDict["burst"] = 1600
        tempDict["cburst"] = 1600
        tempDict["level"] = 0
        tempDict["quantum"] = 1600
        tempDict["mbuffer"] = 60
        tempDict["priority"] = leafClassesConfigs[leaf][2]
        tempDict["queueNum"] = leafClassesConfigs[leaf][3]
        
        data.append(tempDict)

    fh.write(json.dumps(data))
    fh.close


#genHTBConfig('Andytest', 10000, {'One':[4000, 7000, 0, 0], 'Two':[2000, 5000, 0, 1]})

def genHTBconfigWithInner(configName, linkSpeed, leafClassesConfigs, innerClassesConfigs, numLevels, sliceRates): #Creates two layer HTB config in data array, root, inner and leaf classes, writes to json file
    data = []
    
    fh = open('../simulations/configs/htbTree/'+configName+ '.json', 'a+')

    root = sampleDict.copy()
    root["id"] = "root"
    root["level"] = numLevels
    root["rate"] = linkSpeed
    root["ceil"] = linkSpeed
    data.append(root)

    for inner in innerClassesConfigs:
        tempDict = sampleDict.copy()
        tempDict["id"] = 'inner' + inner
        tempDict["parentId"] = innerClassesConfigs[inner][2]
        
        tmp = 0
        for x in range(len(sliceRates["slice"+inner])):
            if x == 0:
                tempDict["rate"] = int(sliceRates["slice"+inner][0])
            else:
                if sliceRates["slice"+inner][x] != tmp:
                    tmp = sliceRates["slice"+inner][x]
                    tempDict["rate"+str(x)] = int(sliceRates["slice"+inner][x])

        # tempDict["rate"] = sliceRates["slice"+inner][0] * 1000
        # i = 1
        # for rate in sliceRates["slice"+inner]:
        #     if rate != tmp:
        #         tmp = rate
        #         tempDict["rate"+str(i)] = rate*1000
        #     i+=1
        tmp = 0
        for x in range(len(sliceRates["slice"+inner])):
            if x == 0:
                tempDict["ceil"] = int(sliceRates["slice"+inner][0])
            else:
                if sliceRates["slice"+inner][x] != tmp:
                    tmp = sliceRates["slice"+inner][x]
                    tempDict["ceil"+str(x)] = int(sliceRates["slice"+inner][x])

        # tempDict["ceil"] = sliceRates["slice"+inner][0] * 1000
        # i = 1
        # for ceil in sliceRates["slice"+inner]:
        #     if ceil != tmp:
        #         tmp = ceil
        #         tempDict["ceil"+str(i)] = ceil*1000
        #     i+=1
        tempDict["burst"] = 2000
        tempDict["cburst"] = 2000
        tempDict["level"] = innerClassesConfigs[inner][3]
        tempDict["quantum"] = 1500
        tempDict["mbuffer"] = 60
        
        data.append(tempDict)

    for leaf in leafClassesConfigs:
        tempDict = sampleDict.copy()
        tempDict["id"] = 'leaf' + leaf
        tempDict["parentId"] = leafClassesConfigs[leaf][4]
        tempDict["rate"] = leafClassesConfigs[leaf][0]
        tempDict["ceil"] = leafClassesConfigs[leaf][1]
        tempDict["burst"] = 2000
        tempDict["cburst"] = 2000
        tempDict["level"] = 0
        tempDict["quantum"] = 1500
        tempDict["mbuffer"] = 60
        tempDict["priority"] = leafClassesConfigs[leaf][2]
        tempDict["queueNum"] = leafClassesConfigs[leaf][3]
        
        data.append(tempDict)

    fh.write(json.dumps(data))
    fh.close

# {leafName:[assuredRate, ceilRate, priority, queueNum, parentId, level]}
# {innerName:[assuredRate, ceilRate, parentId, level]}


def makeIPhostNum(ipPrefix, hostNum):
    ipString = ipPrefix + '.'
    ipString += str(hostNum // 64) + '.'
    ipString += str(4*hostNum % 256)
    return ipString

def genBaselineRoutingConfig(configName, hostTypes, hostNums, hostIPprefixes, serverTypes, serverIPprefixes):
    configElem = ET.Element('config')
    for host,nums in zip(hostTypes, hostNums):
        for num in range(nums):
            interfaceElem = ET.SubElement(configElem, 'interface')
            interfaceElem.set('hosts', host+'['+str(num)+']')
            interfaceElem.set('names', 'ppp0')
            interfaceElem.set('address', makeIPhostNum(hostIPprefixes[host],num))
            interfaceElem.set('netmask', '255.255.255.252')
        interfaceElem = ET.SubElement(configElem, 'interface')
        interfaceElem.set('hosts', 'router0')
        interfaceElem.set('towards', host+'[*]')
        interfaceElem.set('address', hostIPprefixes[host]+'.x.x')
        interfaceElem.set('netmask', '255.255.255.252')
    
    for server in serverTypes:
        interfaceElem = ET.SubElement(configElem, 'interface')
        interfaceElem.set('hosts', server)
        interfaceElem.set('names', 'ppp0')
        interfaceElem.set('address', serverIPprefixes[server]+'.0.0')
        interfaceElem.set('netmask', '255.255.255.252')
    

    interfaceElem = ET.SubElement(configElem, 'interface')
    interfaceElem.set('hosts', '**')
    interfaceElem.set('address', '10.x.x.x')
    interfaceElem.set('netmask', '255.x.x.x')
    


    # create a new XML file with the results
    mydata = ET.tostring(configElem)
    myfile = open('../simulations/configs/routing/'+configName+"Routing.xml", "wb")
    myfile.write(mydata)
    # shutil.copy2(configName+"Routing.xml", '../simulations/configs/baseQoS')


# genBaselineRoutingConfig('stasTest10a', ['hostFDO'], [2], {'hostFDO':'10.3'}, ['serverFDO'],  {'serverFDO':'10.6'})

def startStopTimes(confName, hosts, changeTimes):
    configStringStartStop = ""
    
    for a in np.arange(len(hosts["SSH"][0])):
        configStringStartStop += '**.hostSSH['+ str(a) +'].app[0].startTime = ' + str(hosts["SSH"][0][a]) + 's\n' 
        configStringStartStop += '**.hostSSH['+ str(a) +'].app[0].stopTime = ' + str(hosts["SSH"][1][a]) + 's\n'
    
    for a in np.arange(len(hosts["VIP"][0])):
        configStringStartStop += '**.serverVIP.app['+ str(a) +'].startTime = ' + str(hosts["VIP"][0][a]) + 's\n' 
        configStringStartStop += '**.serverVIP.app['+ str(a) +'].stopTime = ' + str(hosts["VIP"][1][a]) + 's\n'

    for a in np.arange(len(hosts["VID"][0])):
        configStringStartStop += '**.hostVID['+ str(a) +'].app[0].startTime = ' + str(hosts["VID"][0][a]) + 's\n' 
        configStringStartStop += '**.hostVID['+ str(a) +'].app[0].stopTime = ' + str(hosts["VID"][1][a]) + 's\n'
    
    for a in np.arange(len(hosts["LVD"][0])):
        configStringStartStop += '*.hostLVD['+ str(a) +'].app[0].startTime = ' + str(hosts["LVD"][0][a]) + 's\n' 
        configStringStartStop += '*.hostLVD['+ str(a) +'].app[0].stopTime = ' + str(hosts["LVD"][1][a]) + 's\n'
    
    for a in np.arange(len(hosts["FDO"][0])):
        configStringStartStop += '*.hostFDO['+ str(a) +'].app[0].startTime = ' + str(hosts["FDO"][0][a]) + 's\n' 
        configStringStartStop += '*.hostFDO['+ str(a) +'].app[0].stopTime = ' + str(hosts["FDO"][1][a]) + 's\n'
    
    configStringStartStop += "*.router*.ppp[0].queue.scheduler.changeTimes = [" + ', '.join(str(c) for c in changeTimes) + "]\n"

    f = open('../simulations/configs/startStop/' + confName + 'StartStop.ini', 'a')
    f.write(configStringStartStop)
    f.close()

def genBaselineIniConfig(confName, base, numHostsPerType, hostIPprefixes, availBand, ceilMultiplier, guaranteeMultiplier, hosts, changeTimes, rejected):
    sumHosts = 0

    #packFilters = '\"'
    packDataFiltersR0 = '['
    packDataFiltersR1 = '['

    for host in numHostsPerType:
        numHostsType = numHostsPerType[host]
        sumHosts += numHostsType
        for num in range(numHostsType):
            #packFilters += '*;'
            packDataFiltersR0 += 'expr(ipv4.srcAddress.str() =~ \"' + makeIPhostNum(hostIPprefixes[host],num) + '\"),'
            packDataFiltersR1 += 'expr(ipv4.destAddress.str() =~ \"' + makeIPhostNum(hostIPprefixes[host],num) + '\"),'


    #packFilters = packFilters[:-1]
    packDataFiltersR0 = packDataFiltersR0[:-1]
    packDataFiltersR1 = packDataFiltersR1[:-1]

    #packFilters += ']'
    packDataFiltersR0 += ']'
    packDataFiltersR1 += ']'
    

    configString = '[Config ' + confName + ']\n'
    configString += 'description = \"Configuration for ' + confName + '. All five applications. QoS employed. Guarantee Multiplier: ' + str(guaranteeMultiplier) + '; Ceil multiplier: ' + str(ceilMultiplier) +'\"\n\n'
    configString += 'extends = ' + base + '\n\n'
    configString += '*.configurator.config = xmldoc(\"configs/routing/' + confName + 'Routing.xml\")\n\n'
    configString += 'include ./configs/startStop/'+ confName +'StartStop.ini\n\n'
    if 'hostVID' in numHostsPerType:
        configString += '*.nVID = ' + str(numHostsPerType['hostVID']) + ' # Number of video clients\n'
    else: 
        configString += '*.nVID = 0 # Number of video clients\n'
    if 'hostLVD' in numHostsPerType:
        configString += '*.nLVD = ' + str(numHostsPerType['hostLVD']) + ' # Number of live video client\n'
    else: 
        configString += '*.nLVD = 0 # Number of live video client\n'
    if 'hostFDO' in numHostsPerType:
        configString += '*.nFDO = ' + str(numHostsPerType['hostFDO']) + ' # Number of file download clients\n'
    else: 
        configString += '*.nFDO = 0 # Number of file download clients\n'
    if 'hostSSH' in numHostsPerType:
        configString += '*.nSSH = ' + str(numHostsPerType['hostSSH']) + ' # Number of SSH clients\n'
    else: 
        configString += '*.nSSH = 0 # Number of SSH clients\n'
    if 'hostVIP' in numHostsPerType:
        configString += '*.nVIP = ' + str(numHostsPerType['hostVIP']) + ' # Number of VoIP clients\n\n'
    else: 
        configString += '*.nVIP = 0 # Number of VoIP clients\n\n'
    if 'hostcVIP' in numHostsPerType:
        configString += '*.ncVIP = ' + str(numHostsPerType['hostcVIP']) + ' # Number of VoIP clients\n\n'
    else: 
        configString += '*.ncVIP = 0 # Number of critical VoIP clients\n\n'

    configString += '*.router*.ppp[0].queue.typename = \"HtbQueue\"\n'
    configString += '*.router*.ppp[0].queue.numQueues = ' + str(sumHosts) + '\n'
    configString += '*.router*.ppp[0].queue.queue[*].typename = \"DropTailQueue\"\n'
    configString += '*.router*.ppp[0].queue.packetCapacity = -1\n'
    configString += '*.router*.ppp[0].queue.htbHysterisis = false\n'
    configString += '*.router*.ppp[0].queue.scheduler.adjustHTBTreeValuesForCorectness = false\n'
    configString += '*.router*.ppp[0].queue.scheduler.checkHTBTreeValuesForCorectness = false\n'
    configString += '*.router*.ppp[0].queue.htbTreeConfig = readJSON(\"configs/htbTree/'+confName+'.json\")\n' # xmldoc(\"configs/htbTree/' + confName + 'HTB.xml\")\n'
    configString += '*.router*.ppp[0].queue.classifier.defaultGateIndex = 0\n'
    configString += '*.router0.ppp[0].queue.classifier.packetFilters = ' + packDataFiltersR0 + '\n'
    configString += '*.router1.ppp[0].queue.classifier.packetFilters = ' + packDataFiltersR1 + '\n\n'

    configString += '**.connFIX0.datarate = ' + str(math.ceil(availBand)) + 'Mbps\n'
    configString += '**.connFIX0.delay = 40ms\n\n\n'



    f2 = open('../simulations/DynamicStudyConfig.ini', 'a')
    f2.write(configString)
    f2.close()
    # print(configString)
    configString += 'Rejected: ' + str(rejected) + '\n'
    f = open(confName+".txt", "w")
    f.write(configString)
    f.close()
    
    startStopTimes(confName, hosts, changeTimes)

    



def genAllSliConfigsHTBRun(configName, baseName, availBand, desiredQoE, types, hostToSlice, sliceNames, maxNumCliType, baseNumCli, ceilMultiplier, guaranteeMultiplier, differentiatePrios, hosts, algo, maxsimtime):
    cliTypes = ['host'+x for x in types]
    serverTypes = ['server'+x for x in types]
    #numHostsPerType, reqBitratesPerType, ceilBitrates = simpleAdmission(availBand*1000, desiredQoE, ['host'+x for x in types], maxNumCliType, ceilMultiplier, guaranteeMultiplier)
    
    hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(hosts, availBand, 3.5, algo, maxsimtime, configName)
    print(str(rejected) + " Amount of clients got rejected because of limited bandwidth")
    print(hosts["LVD"][0])
    numHostsPerType = {}

    for host in hosts:
        numHostsPerType["host"+host] = len(hosts[host][0])
        #ceilBitrates[host] = reqBitratesPerType[host] * ceilMultiplier
        #assuredBitrates[host] = reqBitratesPerType[host] * guaranteeMultiplier

    hostIPprefixes = {}
    serverIPprefixes = {}
    leafClassesConfigs = {}
    innerClassConfigs = {}
    queueInt = 0
    # {leafName:[assuredRate, ceilRate, priority, queueNum, parentId, level]}
    # {innerName:[assuredRate, ceilRate, parentId, level]}
    numLev = 2
    for sliNum in range(len(hostToSlice)):
        sumGuaranteesBandSli = 0
        parentName = 'inner'+sliceNames[sliNum]
        if sliceNames[sliNum] == 'connFIX0':
            parentName = 'root'
            numLev = 1
        for hType in hostToSlice[sliNum]:
            host = 'host'+hType
            priority = 0
            if differentiatePrios == True and host != 'hostVIP' and host != 'hostSSH':
                priority = 1
            for num in range(numHostsPerType[host]):
                leafClassesConfigs[host+str(num)] = [assuredBitrates[host], ceilBitrates[host], priority, queueInt, parentName, 0]
                queueInt += 1
            #defaultBitrateHost = getBandForQoECli(host, desiredQoE)
            # print(defaultBitrateHost)
            # sumGuaranteesBandSli += baseNumCli * defaultBitrateHost
            # if sumGuaranteesBandSli < reqBitratesPerType[hType] * numHostsPerType[hType]:
            #     print(sumGuaranteesBandSli, reqBitratesPerType[hType] * numHostsPerType[hType])
            #     print("bitrates:")
            #     print(defaultBitrateHost, reqBitratesPerType[hType])
            #     print("numberCli:")
            #     print(baseNumCli, numHostsPerType[hType])
            #     raise ValueError('Slice GBR does not match!!')
            #print(maxNumCliType, numHostsPerType[host], reqBitratesPerType[hType], guaranteeMultiplier, sumGuaranteesBandSli, reqBitratesPerType[hType] * numHostsPerType[host])
        if sliceNames[sliNum] != 'connFIX0':
            # For inner class: assured, guaranteed, parent, level
            innerClassConfigs[sliceNames[sliNum]] = [sumGuaranteesBandSli, sumGuaranteesBandSli, 'root', 1]

                
        # print(list(leafClassesConfigs.keys())[0],':',leafClassesConfigs[list(leafClassesConfigs.keys())[0]])
        # print(list(innerClassConfigs.keys())[0],':',innerClassConfigs[list(innerClassConfigs.keys())[0]])
        

    prefIPno = 0
    for host in cliTypes:
        hostIPprefixes[host] = '10.'+str(prefIPno)
        prefIPno += 1
    prefIPno = 0
    for server in serverTypes:
        serverIPprefixes[server] = '10.'+str(prefIPno+10)
        prefIPno += 1

    genHTBconfigWithInner(configName, availBand*1000, leafClassesConfigs, innerClassConfigs, numLev, sliceRates)
    hostNums = [numHostsPerType[x] for x in numHostsPerType]
    genBaselineRoutingConfig(configName, cliTypes, hostNums, hostIPprefixes, serverTypes, serverIPprefixes)
    genBaselineIniConfig(configName, baseName, numHostsPerType, hostIPprefixes, availBand, ceilMultiplier, guaranteeMultiplier, hosts, newChangeTimes, rejected)
    print('../simulations/'+configName.split('-')[0]+'.txt')
    f2 = open('../simulations/'+configName.split('-')[0]+'.txt', 'a+')
    f2.write('./runAndExportHeatMaps.sh -i DynamicStudyConfig.ini -c ' + configName + ' -s 5\n')
    f2.close()


###########################
# Dynamic runs with four different Resource allocations
# offset = 1

# maxsimtime = 400
# for i in range(1):
#     orighosts = allHostTypesAdmission(maxsimtime)

#     #hosts, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(hosts, 100, 3.5, 'equal', maxsimtime)
#     genAllSliConfigsHTBRun('Final'+str(i+offset)+'-static_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "static", maxsimtime)
#     genAllSliConfigsHTBRun('Final'+str(i+offset)+'-equal_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "equal", maxsimtime)
#     genAllSliConfigsHTBRun('Final'+str(i+offset)+'-weighted_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "weighted", maxsimtime)
#     genAllSliConfigsHTBRun('Final'+str(i+offset)+'-cnsm_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "CNSM", maxsimtime)


##########################
#Static slice with dynamic clients 
# orighosts = allHostTypesAdmission(400)
# hosts3, reqBitratesPerType, newChangeTimes, sliceRates, rejected, assuredBitrates, ceilBitrates = calculateEvents(orighosts.copy(), 100, 3.5, 'static', 400, 'testingCSVstatic')
# hosts4, reqBitratesPerType, newChangeTimes, sliceRates, rejected2, assuredBitrates, ceilBitrates = calculateEvents(orighosts.copy(), 100, 3.5, 'equal', 400, 'testingCSVequal')
# print(str(rejected) + " Amount of clients got rejected because of limited bandwidth")
# print(str(rejected2) + " Amount of clients got rejected because of limited bandwidth")

#genAllSliConfigsHTBRun('Testrun-static_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, hosts.copy(), "static", 400)
#genAllSliConfigsHTBRun('Testrun-equal_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, hosts.copy(), "equal", 400)

##########################
#Extra long
# hosts = allHostTypesAdmission(800)
# genAllSliConfigsHTBRun('DynamicExtraLong-equal_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, hosts.copy(), "equal", 800)

#########################
# CNSM but halway half the video clients leave

# orighosts = {"SSH": np.vstack(([1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399])),
#            "VIP": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399])),
#            "VID": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200])),
#            "LVD": np.vstack(([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399,399])),
#            "FDO": np.vstack(([1,1,1,1,1],[399,399,399,399,399]))
#            }
# maxsimtime = 400

# genAllSliConfigsHTBRun('HalfCNSMFinal-static_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "static", maxsimtime)
# genAllSliConfigsHTBRun('HalfCNSMFinal-equal_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "equal", maxsimtime)
# genAllSliConfigsHTBRun('HalfCNSMFinal-weighted_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "weighted", maxsimtime)
# genAllSliConfigsHTBRun('HalfCNSMFinal-cnsm_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "CNSM", maxsimtime)

# genllSliConfigsHTBRun('CNSM_halfVidFinal', 'liteCbaselineTestTokenQoS_base', 60, 3.5, ['SSH','VIP','FDO'], [['SSH'],['VIP'],['FDO']], ['SSH','VIP','FDO'], 100, 100, 2, 1, False)


#########################
# TESTING:
orighosts = {"SSH": np.vstack(([1,1],[399,399])),
           "VIP": np.vstack(([1,1],[399,399])),
           "VID": np.vstack(([1,1],[399,399])),
           "LVD": np.vstack(([1,1],[399,399])),
           "FDO": np.vstack(([1,1],[399,399]))
           }
maxsimtime = 400

genAllSliConfigsHTBRun('2Clients5slice-static_R100_Q35_M100_C100_PFalse', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 1, 1, False, orighosts.copy(), "static", maxsimtime)


#genAllSliConfigsHTBRun('LastTest1', 'liteCbaselineTestTokenQoS_base', 100, 3.5, ['SSH','VIP','VID','LVD','FDO'], [['SSH'],['VIP'],['VID'],['LVD'],['FDO']], ['SSH','VIP','VID','LVD','FDO'], 100, 100, 2, 1, False, hosts, "equal")


#"SSH": ssh,"VIP": vip, "VID": vid,"LVD": lvd,"FDO": fdo

#hei = algorithm({'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 20, 'sliceVIP' : 20, 'sliceVID' : 20, 'sliceLVD' : 20, 'sliceFDO' : 20}, 1000, 0.0, 0, 1000, 100, False)
#print("********")
#print(hei[0])

##################################
#FDO client
# targetQoE = [3.5]
# assuredMulti = [1.0]
# # assuredMulti = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
# rates = [100]
# defaultNumClients = 100
# ceils = [2.0]
# # ceils = [1.0, 1.5, 2.0]
# dPrio = [False]
# client = 'FDO'
# studyName = 'FDODynamic'

# counter = 0
# for rate in rates:
#     for qoE in targetQoE:
#         for ceil in ceils:
#             rate = getBandForQoECli('host'+client, qoE)*defaultNumClients/1000
#             # for mult1 in assuredMulti:
#             #     maxCli = int(defaultNumClients/mult1)
#             #     for mult in [x for x in assuredMulti if x < mult1]:
#             #         # print(int(defaultNumClients/mult1))
#             #         for dp in dPrio:
#             #             print(maxCli, mult, ceil)
#             #             # genAllSliConfigsHTBRun(studyName+'-maxCli'+str(maxCli)+'_R'+str(int(rate))+'_Q'+str(int(qoE*10))+'_M'+str(int(mult*100))+'_C'+str(int(ceil*100))+'_P'+str(dp), 'liteCbaselineTestTokenQoS_base', rate, qoE, [client], [[client]], ['connFIX0'], maxCli, defaultNumClients, ceil, mult, dp)
#             #             counter += 1
#             #print("rate:" + str(rate))
#             for mult in assuredMulti:
#                 maxCli = int(defaultNumClients/mult)
#                 for dp in dPrio:
#                     print(maxCli, mult, ceil)
#                     # counter+=1
#                     genAllSliConfigsHTBRun(studyName+'-maxCli'+str(maxCli)+'_R'+str(int(rate))+'_Q'+str(int(qoE*10))+'_M'+str(int(mult*100))+'_C'+str(int(ceil*100))+'_P'+str(dp), 'liteCbaselineTestTokenQoS_base', rate, qoE, [client], [[client]], ['connFIX0'], maxCli, defaultNumClients, ceil, mult, dp)
#                     counter += 1
# print(counter)

# name = sys.argv[1]
# slices = sys.argv[2]

# print(name)
# if os.path.isfile("./" + str(name) + ".json"):
#     print("Config already exists with this name!")

# else:
#     numVID = int(name.split('VID')[1].split('_LVD')[0])
#     numLVD = int(name.split('LVD')[1].split('_FDO')[0])
#     numFDO = int(name.split('FDO')[1].split('_SSH')[0])
#     numSSH = int(name.split('SSH')[1].split('_VIP')[0])
#     numVIP = int(name.split('VIP')[1].split('/')[0])

#     genHTBConfig(numVID, numLVD, numFDO, numSSH, numVIP)