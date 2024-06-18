import pandas as pd
import csv
import statistics
from termcolor import colored
import sys
import os
from matplotlib import pyplot as plt
import numpy as np
maxSimTime = 400
DEBUG = 0

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']

def makeFullScenarioName(testName,nodeSplit):
    scenName = str(testName)
    numCLI=sum(nodeSplit)
    #return scenName
  
    return str(testName) + '_' + str(numCLI) + '_VID' + str(nodeSplit[0]) + '_FDO' + str(nodeSplit[2]) + '_SSH' + str(nodeSplit[3]) + '_VIP' + str(nodeSplit[4])

def makeNodeIdentifier(tp, delay):
    return 'tp' + str(tp) + '_del' + str(delay)

# Function that imports node information into a dataframe
#   - testName - name of the test
#   - numCLI - total number of clients in the test
#   - nodeSplit - number of nodes running certain applications in the test
#       [numVID, numFDO, numSSH, numVIP]
#   - nodeType - type of the node to import (String), curr. used
#       hostVID, hostFDO, hostSSH, hostVIP, links, serverSSH
#   - nodeNum - number of the node to import, omitted if -1
def importDF(testName, tp, delay,nodeSplit,host):
    # File that will be read
    print(host)
    fullScenarioExportName = makeFullScenarioName(testName,nodeSplit)
    # fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_hostVID0_vec.csv'
    #fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_hostFDO0_vec.csv'
    # fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_vec.csv'
    #fileToRead = '../' + str(testName) + "/heatMapTest_VoIP_scalability10_10_VID0_FDO0_SSH0_VIP10" + "/heatMapTest_VoIP_scalability10"  + '_' + makeNodeIdentifier(tp, delay) + '_hostVIP0_vec.csv'
    fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + str(testName)  + '_' + makeNodeIdentifier(tp, delay) + '_' + host + '_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pd.read_csv(fileToRead)

def filterDFType(df, filterType):
    return df.filter(like=filterType)

def getFilteredDFtypeAndTS(df, filterType):
    filteredDF = filterDFType(df, filterType)
    if len(filteredDF.columns):
        colNoTS = df.columns.get_loc(df.filter(filteredDF).columns[0])
        newDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        newDF.rename(columns={str(newDF.columns[0]) : "TS", str(newDF.columns[1]) : filterType + " Val"})
        return newDF.rename(columns={str(newDF.columns[0]) : "TS", str(newDF.columns[1]) : filterType + " Val"})
    else:
        return pd.DataFrame(columns=['ts', filterType + 'Val'])

def mapApplicationToInteger(host):
    if host == "hostVIP":
        return 4
    elif host == "hostLVD":
        return 1
    elif host == "hosVID":
        return 0
    elif host == "hostFDO":
        return 2
    elif host == "hostSSH":
        return 3
    elif host == "hostFDO":
        return 4
    elif host == "hostcVIP"  : 
        return 5

def extractMosVal(testName, tp, delay, nodeSplit, host):
    
    mosListAllClientsAvg = []
    for i in range (0,nodeSplit[mapApplicationToInteger(host)]):
        hostNumber=host+str(i)
        
        df = importDF(testName, tp, delay,nodeSplit,hostNumber) #read a file for each client
        mosDF = getFilteredDFtypeAndTS(df, 'mos') #voipTalkspurtNumPackets
        # print(mosDF)
        mosList = mosDF['mos Val'].tolist() #all MOS values for one client   voipTalkspurtNumPackets
        # if tp == 1000 : #or tp==1000
        #     if i == 4 or i==87 or i == 45 or  i==77 or i==66:
        #         x=np.sort(mosList)
        #         print(mosList)
        #         y=np.arange(len(mosList))/float(len(mosList))
        #         plt.plot( x,y,label=str(int(tp/100)) + "kbps" + "_host" + str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
        #         plt.xlabel("MOS")
        #         plt.ylabel("CDF")
        #         plt.legend()
        #         plt.savefig("../exports/plots/new_" + testName + "_" + str(tp)  + ".png")
        line = hostNumber + "," + str(tp) + "," + str(len(mosList))+ "\n"
        f = open('countMos1.txt', 'a')

        # create the csv writer
        f.write(line)
        # close the file
        f.close()
        if len(mosList) > 0:
            mosListAllClientsAvg.append(statistics.mean(mosList))  #save avg for each client      
            #mosListAllClientsAvg.append(len(mosList))
            #mosListAllClientsAvg.append(mosList[0]) 
        #return mosList[0]
        else:
            return 1.0
    # if tp == 900 or tp==1000:
    #     x=np.sort(mosListAllClientsAvg)
    #     y=np.arange(len(mosListAllClientsAvg))/float(len(mosListAllClientsAvg))
    #     plt.plot( x,y,label=str(int(tp/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 
    #     plt.xlabel("MOS")
    #     plt.ylabel("CDF")
    #     plt.legend()
    #     plt.savefig("../exports/plots/CdfMos_" + testName + "_" + str(tp)  + ".png")
    print(mosListAllClientsAvg)
    return mosListAllClientsAvg

def countMOS():
    df =  pd.read_csv('countMos1.csv')
    df.columns =['Host', 'TP', 'count']
    
    for i in range(5,50):
        hostName="hostVIP"
        hostName=hostName + str(i) #for each host
        count =[]
        for i in range(0,25):
            print(len(list(df.loc[df["Host"] == hostName, "count"])))
            count.append(list(df.loc[df["Host"] == hostName, "count"])[i]) #get values for first 5 BW
        plt.plot([x for x in range(5,30,1)],count,label=hostName)
    plt.xlabel("Throughput [kbps]")
    plt.ylabel("CountMOS")
    plt.legend()

    plt.savefig("../exports/plots/count.png")


def plotMosCdf(testNames, tps, delay,nodeSplit):
    mosValues = {} #initialize array and save all points in there
    tpsOriginal=tps

    for testName in testNames:
        if testName == "heatMapTest_VoIP_scalability10s1":
            nodeSplit = [0, 0, 0, 0, 1,0]
            tps[:] = [int(x / 10) for x in tps]
            print(tps)
        if testName == "heatMapTest_VoIP_scalability1s100":
            nodeSplit = [0, 0, 0, 0, 100,0]
            tps[:] = [int(x * 100) for x in tps]
        mosValues[testName]=[]
        for i in tps:
            mosValues[testName] = []
            if i == 900 or i == 1000:
                mosValues[testName].extend(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))

                x=np.sort(mosValues[testName])
                y=np.arange(len(mosValues[testName]))/float(len(mosValues[testName]))
                plt.plot( x,y,label=testName + "_" + str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 


        print(tpsOriginal)
        #plt.plot( [x for x in range(5,30,1)],mosValues[testName],label=testName.split("_")[2].replace("scalability",""))
        plt.xlabel("Throughput [kbps]")
        plt.ylabel("MOS")
        plt.legend()

    plt.savefig("../exports/plots/comparisson_" + testNames[0]+ ".png") # + "_" + testNames[1] 

def extracte2ed(testName, tp, delay):
    df = importDF(testName, tp, delay)
    mosDF = getFilteredDFtypeAndTS(df, 'endToEndDelay')
    print(mosDF['endToEndDelay Val'])
    return mosDF['endToEndDelay Val']

# extractMosVal('heatMapTest_VoIPnewSettings', 540, 0)
# extracte2ed('singleAppDelayTest_VoIP_1cli', 10000, 50)

def prepareMosValsForHeatmap(testName, tps, delays,nodeSplit):
    xAxis = []
    yAxis = []
    mosMap = []
    for x in delays:
        print(x)
        if x not in xAxis:
            xAxis.append(x)
        for y in tps:
            if y not in yAxis:
                yAxis.append(y)
                mosMap.append([])
            mosMap[yAxis.index(y)].append(extractMosVal(testName, y, x, nodeSplit, "hostVIP"))
    if not os.path.exists('../exports/heatMap/'):
        os.makedirs('../exports/heatMap/')
    with open('../exports/heatMap/'+makeFullScenarioName(testName,nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(xAxis)
        fw.writerow(yAxis)
        fw.writerow(mosMap)

def plotMeanMosForEachClient(testNames, tps, delay,nodeSplit):
    mosValues = {} #initialize array and save all points in there
    tpsOriginal=tps

    for testName in testNames:
        if testName == "heatMapTest_VoIP_scalability10s1Queue10000":
            nodeSplit = [0, 0, 0, 0, 1,0]
            tps[:] = [int(x / 10) for x in tps]
            print(tps)
        if  testName=="heatMapTest_VoIP_scalability10s100Queue10000" or testName=="heatMapTest_VoIP_scalability1s100NoOffset200ms": #testName == "heatMapTest_VoIP_scalability1s100" or heatMapTest_VoIP_scalability1s100Queue500
            nodeSplit = [0, 0, 0, 0, 100,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        if  testName=="heatMapTest_VoIP_scalability10s1000Queue10000": 
            nodeSplit = [0, 0, 0, 0, 1000,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        
        for i in tps:
            if i == 900 or i == 1000: 
                print("TP=" + str(i) +  "\n\n")
                mosValues[testName]=[]
                mosValues[testName].append(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))
                #mosValues[testName].extend(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))
                print(mosValues)
                #x=np.sort(mosValues[testName])
                #y=np.arange(len(mosValues[testName]))/float(len(mosValues[testName]))
                #plt.plot( x,y,label=str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
                #print(tpsOriginal)
                arr1 = np.array(mosValues[testName])
                arr1 = arr1.transpose()
                plt.plot([x for x in range(0,100,1)],arr1,label=str(i)+ "kbps")


        #plot CDF of all values for some clients 
        hostNumbers = [1,2]
        for i in tps:
            if i == 900 or i == 1000: 
                print("TP=" + str(i) +  "\n\n")
                mosValues[testName]=[]
                #mosValues[testName].append(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))
                mosValues[testName].extend(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))
                print(mosValues)
                #x=np.sort(mosValues[testName])
                #y=np.arange(len(mosValues[testName]))/float(len(mosValues[testName]))
                #plt.plot( x,y,label=str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
                #print(tpsOriginal)
                arr1 = np.array(mosValues[testName])
                arr1 = arr1.transpose()
                plt.plot([x for x in range(0,100,1)],arr1,label=str(i)+ "kbps")





        plt.xlabel("Throughput [kbps]")
        plt.ylabel("MOS")
        plt.legend()
    plt.savefig("../exports/plots/comparisson900_" + testNames[0] + ".png") #+ "_" + testNames[1] 
    # if not os.path.exists('../exports/heatMap/'):
    #     os.makedirs('../exports/heatMap/')
    # with open('../exports/heatMap/'+makeFullScenarioName(testName,nodeSplit)+'.csv', mode='w') as writeFile:
    #     fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    #     fw.writerow(xAxis)
    #     fw.writerow(yAxis)
    #     fw.writerow(mosMap)
    # for i in testNames:
    #     mosValues = [] #initialize array and save all points in there
    #     for i in tps:
    #     mosValues.append(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))

    #     plt.plot(tps,mosValues)
    #     plt.savefig("../exports/plots/" + makeFullScenarioName(testName,nodeSplit) +".png")

# prepareMosValsForHeatmap('heatMapTest_SSH', [5,10,150,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620])
# prepareMosValsForHeatmap('heatMapTest_VoIP', [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620,640,660,680,700,720,740,760,780,800,820,840,860,880,900,920,940,960,980])
# prepareMosValsForHeatmap('heatMapTest_VoIPnewSettings', [540,542,544,546,548,550,552,554,556,558,560,562,564,566,568,570,572,574,576,578,580,582,584,586,588,590,592,594,596,598,600], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620,640,660,680,700,720,740,760,780,800])
# prepareMosValsForHeatmap('heatMapTest_Video', [250,290,330,370,410,450,490,530,570,610,650,690,730,770,810,850,890,930,970,1010,1050,1090,1130,1170,1210,1250,1290,1330,1370,1410,1450,1490,1530], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_VideoV2', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoV2', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_NewLiveVideoClient', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_NewLiveVideoClient', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoV2', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideo', [250,290,330,370,410,450,490,530,570,610,650,690,730,770,810,850,890,930,970,1010,1050,1090,1130,1170,1210,1250,1290,1330,1370,1410,1450,1490,1530], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_FileDownload', [250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,3750,4000,4250,4500,4750,5000,5250,5500,5750,6000,6250,6500,6750,7000,7250,7500,7750,8000], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_FileDownload2-5MB', [250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,3750,4000,4250,4500,4750,5000,5250,5500,5750,6000,6250,6500,6750,7000,7250,7500,7750,8000], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])

# prepareMosValsForHeatmap('heatMapTest_VideoFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_FileDownloadFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_VideoLong', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoFineLong', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineShort', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineLong', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoShort', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoLong', [50+i*300 for i in range(33)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_VoIP_corrected', [x for x in range(5,56)], [x*20 for x in range(0,50)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineLongV2', [100+x*20 for x in range(226)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoFineLongV2', [100+x*20 for x in range(226)], [i*20 for i in range(31)])
#prepareMosValsForHeatmap('heatMapTest_FileDownloadFineV3', [100+x*20 for x in range(226)], [i*20 for i in range(31)])

#prepareMosValsForHeatmap('heatMapTest_VoIP_scalability100',[x for x in range(500,5100,100)], [x for x in range(0,1000,20)])
#prepareMosValsForHeatmap('heatMapTest_VoIP_scalability10s10',[x for x in range(50,510,10)], [x for x in range(0,1000,20)],[0, 0, 0, 0, 10,0])


#prepareMosValsForHeatmap('heatMapTest_VoIP_scalability1s10',[x for x in range(50,510,10)], [x for x in range(0,1000,20)],[numVID, numLVD, numFDO, numSSH, numVIP,numcVP, numcF, numcLV])
#prepareMosValsForHeatmap('heatMapTest_VoIP_scalability1s10',[x for x in range(50,510,10)], [x for x in range(0,1000,20)],[0, 0, 0, 0, 10,0])
#prepareMosValsForHeatmap('heatMapTest_VoIP_scalability1s100',[x for x in range(500,3000,100)], [20],[0,ss 0, 0, 0, 100,0])
#countMOS()
#'heatMapTest_VoIP_scalability1s10','heatMapTest_VoIP_scalability10s10',"heatMapTest_VoIP_scalability10s1","heatMapTest_VoIP_scalability1s1"
#plotMosVsBw(['heatMapTest_VoIP_scalability1s100Queue500',"heatMapTest_VoIP_scalability1s100NoOffset","heatMapTest_VoIP_scalability10s1000Queue10000"],[x for x in range(50,300,10)],20,[0, 0, 0, 0, 10,0])


#plotMosVsBw(["heatMapTest_VoIP_scalability10s1Queue10000","heatMapTest_VoIP_scalability10s100Queue10000","heatMapTest_VoIP_scalability10s1000Queue10000"],[x for x in range(50,300,10)],20,[0, 0, 0, 0, 10,0])

#plotMosVsBw(["heatMapTest_VoIP_scalability1s100NoOffset200ms","heatMapTest_VoIP_scalability1s100NoOffset","heatMapTest_VoIP_scalability1s100NoOffsetBuffer40"],[x for x in range(50,300,10)],20,[0, 0, 0, 0, 10,0])

#plotMosVsBw(["heatMapTest_VoIP_scalability20msTesting"],[x for x in range(500,3000,100)],20,[0, 0, 0, 0, 100,0])
#plotMeanMosForAllClients(["heatMapTest_VoIP_scalability20msTesting"],[x for x in range(500,3000,100)],20,[0, 0, 0, 0, 100,0])

def plotMosCountCdf(testNames, tps, delay,nodeSplit):
    countMosValues = {} #initialize array and save all points in there
    countTalkspurtValues = {}
    countMissingTalkspurt = {}
    difference = {}
    tpsOriginal=tps
    tps=[900,1000]
    for testName in testNames:
        for i in tps:
            countMosValues[testName]=[]
            countMosValues[testName].extend(countMosVal(testName, i, delay, nodeSplit, "hostVIP","mos"))
            countTalkspurtValues[testName]=[]
            countTalkspurtValues[testName].extend(countMosVal(testName, i, delay, nodeSplit, "hostVIP","talkspurtId"))
            difference[testName]=[]
            print(countMosValues[testName])
            print(countTalkspurtValues[testName])
            for a, b in zip(countMosValues[testName],countTalkspurtValues[testName]):
                difference[testName].append(a - b)


            x=np.sort(difference[testName])
            y=np.arange(len(difference[testName]))/float(len(difference[testName]))
            plt.plot( x,y,label=str(int(i/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 


            # x=np.sort(difference[testName])
            # y=np.arange(len(difference[testName]))/float(len(difference[testName]))
            # plt.plot( x,y,label=str(int(i/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 

            # countMissingTalkspurt[testName]=[]
            # countMissingTalkspurt[testName].extend(countMosVal(testName, i, delay, nodeSplit, "hostVIP","missedTalkspurtId"))

            # x=np.sort(countMissingTalkspurt[testName])
            # y=np.arange(len(countMissingTalkspurt[testName]))/float(len(countMissingTalkspurt[testName]))
            # plt.plot( x,y,label="missing talkspurts" + str(900) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 

            



            plt.plot( x,y,label=str(int(i/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 
        plt.xlabel("CDF")
        plt.xlabel("Not recorded talkspurts (Mos count - Talkspurt count)")
        plt.legend()
        plt.savefig("../exports/plots/MosCountCdf_" + testNames[0] + ".png")


def countMosVal(testName, tp, delay, nodeSplit, host, filter):
    
    mosCountAllClients = []
    for i in range (0,nodeSplit[mapApplicationToInteger(host)]):
        hostNumber=host+str(i)
        
        df = importDF(testName, tp, delay,nodeSplit,hostNumber) #read a file for each client
        mosDF = getFilteredDFtypeAndTS(df, filter)
        mosList = mosDF[filter+' Val'].tolist() #all MOS values for one client
        if len(mosList) > 0:
            mosCountAllClients.append(len(mosList))  #save count for each client     
        else:
            mosCountAllClients.append(0.0)
    return mosCountAllClients


#plotMosCountCdf(["heatMapTest_VoIP_scalability20msTesting"],[x for x in range(500,3000,100)],20,[0, 0, 0, 0, 100,0])


def plotMeanMosForAllClients(testNames, tps, delay,nodeSplit):
    mosValues = {} #initialize array and save all points in there
    tpsOriginal=tps

    for testName in testNames:
        if testName == "heatMapTest_VoIP_scalability10s1Queue10000":
            nodeSplit = [0, 0, 0, 0, 1,0]
            tps[:] = [int(x / 10) for x in tps]
            print(tps)
        if  testName=="heatMapTest_VoIP_scalability10s100Queue10000" or testName=="heatMapTest_VoIP_scalability1s100NoOffset200ms": #testName == "heatMapTest_VoIP_scalability1s100" or heatMapTest_VoIP_scalability1s100Queue500
            nodeSplit = [0, 0, 0, 0, 100,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        if  testName=="heatMapTest_VoIP_scalability10s1000Queue10000": 
            nodeSplit = [0, 0, 0, 0, 1000,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        mosValues[testName]=[]
        for i in tps:
            mosValues[testName].append(extractMeanMosPerClient(testName, i, delay, nodeSplit, "hostVIP"))
            #mosValues[testName].extend(extractMosVal(testName, i, delay, nodeSplit, "hostVIP"))
            
            #x=np.sort(mosValues[testName])
            #y=np.arange(len(mosValues[testName]))/float(len(mosValues[testName]))
            #plt.plot( x,y,label=str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
            #print(tpsOriginal)
            #arr1 = np.array(mosValues[testName])
            #arr1 = arr1.transpose()
        print(mosValues)    
        plt.plot([x for x in range(500,3000,100)],mosValues[testName],label=testName)
        plt.xlabel("Throughput [kbps]")
        plt.ylabel("MOS")
        plt.legend()
    plt.savefig("../exports/plots/meanMosForAllClients_" + testNames[0] + ".png") #+ "_" + testNames[1] 


def extractMeanMosPerClient(testName, tp, delay, nodeSplit, host):
    
    mosListAllClientsAvg = []
    for i in range (0,nodeSplit[mapApplicationToInteger(host)]):
        hostNumber=host+str(i)
        
        df = importDF(testName, tp, delay,nodeSplit,hostNumber) #read a file for each client
        mosDF = getFilteredDFtypeAndTS(df, 'mos') #voipTalkspurtNumPackets
        # print(mosDF)
        mosList = mosDF['mos Val'].tolist() #all MOS values for one client   voipTalkspurtNumPackets
        # if tp == 1000 : #or tp==1000
        #     if i == 4 or i==87 or i == 45 or  i==77 or i==66:
        #         x=np.sort(mosList)
        #         print(mosList)
        #         y=np.arange(len(mosList))/float(len(mosList))
        #         plt.plot( x,y,label=str(int(tp/100)) + "kbps" + "_host" + str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
        #         plt.xlabel("MOS")
        #         plt.ylabel("CDF")
        #         plt.legend()
        #         plt.savefig("../exports/plots/new_" + testName + "_" + str(tp)  + ".png")
        line = hostNumber + "," + str(tp) + "," + str(len(mosList))+ "\n"
        f = open('countMos1.txt', 'a')

        # create the csv writer
        f.write(line)
        # close the file
        f.close()
        if len(mosList) > 0:
            mosListAllClientsAvg.append(statistics.mean(mosList))  #save avg for each client      
            #mosListAllClientsAvg.append(len(mosList))
            #mosListAllClientsAvg.append(mosList[0]) 
        #return mosList[0]
        else:
            return 1.0
    # if tp == 900 or tp==1000:
    #     x=np.sort(mosListAllClientsAvg)
    #     y=np.arange(len(mosListAllClientsAvg))/float(len(mosListAllClientsAvg))
    #     plt.plot( x,y,label=str(int(tp/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 
    #     plt.xlabel("MOS")
    #     plt.ylabel("CDF")
    #     plt.legend()
    #     plt.savefig("../exports/plots/CdfMos_" + testName + "_" + str(tp)  + ".png")
    #print(mosListAllClientsAvg)
    return statistics.mean(mosListAllClientsAvg)


#plotMeanMosForAllClients(["heatMapTest_VoIP_scalability20msTesting", "heatMapTest_VoIP_scalability20msLong"],[x for x in range(500,3000,100)],20,[0, 0, 0, 0, 100,0])



def plotLossCdfForAllClients(testNames, tps, delay,nodeSplit,data):
    mosValues = {} #initialize array and save all points in there
    tpsOriginal=tps

    for testName in testNames:
        if testName == "heatMapTest_VoIP_scalability10s1Queue10000":
            nodeSplit = [0, 0, 0, 0, 1,0]
            tps[:] = [int(x / 10) for x in tps]
            print(tps)
        if  testName=="heatMapTest_VoIP_scalability10s100Queue10000" or testName=="heatMapTest_VoIP_scalability1s100NoOffset200ms": #testName == "heatMapTest_VoIP_scalability1s100" or heatMapTest_VoIP_scalability1s100Queue500
            nodeSplit = [0, 0, 0, 0, 100,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        if  testName=="heatMapTest_VoIP_scalability10s1000Queue10000": 
            nodeSplit = [0, 0, 0, 0, 1000,0]
            tps[:] = [int(x * 10) for x in tpsOriginal]
        mosValues[testName]=[]
        for i in tps:
            mosValues[testName]=[]
            if i == 900 or i==1000 or i==1100 or i == 1200:
                
            #mosValues[testName].append(extractMeanMosPerClient(testName, i, delay, nodeSplit, "hostVIP"))
                mosValues[testName].extend(extractLossPerClient(testName, i, delay, nodeSplit, "hostVIP",data))
                print ("------------Sum for " + str(i) + " is " + str(sum(mosValues[testName])))
                x=np.sort(mosValues[testName])
                y=np.arange(len(mosValues[testName]))/float(len(mosValues[testName]))
                plt.plot( x,y,label=data + str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
            #print(tpsOriginal)
            #arr1 = np.array(mosValues[testName])
            #arr1 = arr1.transpose()
        print(mosValues)    
        #plt.plot([x for x in range(500,3000,100)],mosValues[testName],label=testName)
        plt.xlabel(data)# NumPackets in Talskspurts (@receivier)
        #plt.xlim(0,250)
        plt.ylabel("CDF")
        plt.legend()
    plt.savefig("../exports/plots/" + data + "CdfForAllClients_" + testNames[0] + ".png") #+ "_" + testNames[1] 


def extractLossPerClient(testName, tp, delay, nodeSplit, host,data):
    
    mosListAllClientsAvg = []
    for i in range (0,nodeSplit[mapApplicationToInteger(host)]):
        hostNumber=host+str(i)
        
        df = importDF(testName, tp, delay,nodeSplit,hostNumber) #read a file for each client
        mosDF = getFilteredDFtypeAndTS(df, data) #voipTalkspurtNumPackets packetLossRate
        # print(mosDF)
        mosList = mosDF[data +  ' Val'].tolist() #all MOS values for one client   voipTalkspurtNumPackets
        # if tp == 1000 : #or tp==1000
        #     if i == 4 or i==87 or i == 45 or  i==77 or i==66:
        #         x=np.sort(mosList)
        #         print(mosList)
        #         y=np.arange(len(mosList))/float(len(mosList))
        #         plt.plot( x,y,label=str(int(tp/100)) + "kbps" + "_host" + str(i))#testName.split("_")[2].replace("scalability","")+ "_" + 
        #         plt.xlabel("MOS")
        #         plt.ylabel("CDF")
        #         plt.legend()
        #         plt.savefig("../exports/plots/new_" + testName + "_" + str(tp)  + ".png")
        line = hostNumber + "," + str(tp) + "," + str(len(mosList))+ "\n"
        f = open('countMos1.txt', 'a')

        # create the csv writer
        f.write(line)
        # close the file
        f.close()
        if len(mosList) > 0:
            #mosListAllClientsAvg.append(statistics.mean(mosList))  #save avg for each client      
            mosListAllClientsAvg.extend(mosList)
            #mosListAllClientsAvg.append(mosList[0]) 
        #return mosList[0]
        else:
            return 1.0
    # if tp == 900 or tp==1000:
    #     x=np.sort(mosListAllClientsAvg)
    #     y=np.arange(len(mosListAllClientsAvg))/float(len(mosListAllClientsAvg))
    #     plt.plot( x,y,label=str(int(tp/100)) + "kbps")#testName.split("_")[2].replace("scalability","")+ "_" + 
    #     plt.xlabel("MOS")
    #     plt.ylabel("CDF")
    #     plt.legend()
    #     plt.savefig("../exports/plots/CdfMos_" + testName + "_" + str(tp)  + ".png")
    #print(mosListAllClientsAvg)
    return mosListAllClientsAvg


plotLossCdfForAllClients(["heatMapTest_VoIP_scalability20msTest"],[x for x in range(500,3000,100)],20,[0, 0, 0, 0, 100,0],"mos")