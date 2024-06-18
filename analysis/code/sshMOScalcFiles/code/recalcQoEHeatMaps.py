import numpy as np
import pandas
import matplotlib
import re
import json
import os
import math
import sys
import pandas as pd
import statistics
import csv

file_dir = os.path.dirname(os.path.abspath(__file__))

import sshMOS as sshMC

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    print(scenName)
    return scenName

def makeNodeIdentifier(nodeType, nodeNum):
    if nodeNum < 0:
        return nodeType
    else:
        return nodeType + str(nodeNum)

# Function that imports node information into a dataframe
#   - testName - name of the test
#   - numCLI - total number of clients in the test
#   - nodeSplit - number of nodes running certain applications in the test
#       [numVID, numFDO, numSSH, numVIP]
#   - nodeType - type of the node to import (String), curr. used
#       hostVID, hostFDO, hostSSH, hostVIP, links, serverSSH
#   - nodeNum - number of the node to import, omitted if -1
def importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, tp, delay):
    # File that will be read
    fullScenarioExportName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    fileToRead = '../../../' + str(testName) + '/' + fullScenarioExportName  + '/' + testName + '_tp' + str(tp) + '_del' + str(delay) + '_' + makeNodeIdentifier(nodeType, nodeNum) + '_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pandas.read_csv(fileToRead)

def calcSSHnodeMOS(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, tp, delay): #returns mean mos per client 
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, tp, delay)

    if not df.filter(like='roundTripTime').empty:
        colNoTS = df.columns.get_loc(df.filter(like='roundTripTime').columns[0])
        tempDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        print(tempDF)
        tempDF.rename(columns={tempDF.columns[0]: 'rtt TS', tempDF.columns[1]: 'rtt Values'}, inplace = True)
        
        rtts = tempDF['rtt Values'].dropna().tolist()
        mos = []
        print(rtts)
        for rtt in rtts:
            print(sshMC.predictSSHmos(rtt))
            mos.append(sshMC.predictSSHmos(rtt).tolist()) #in each client there may be multiple mos scores
            print(mos)
        return statistics.mean(mos)
    else:
        print()
        return 1.0


def recalculateQoEsimulationRun(testName, numCLI, nodeTypes, nodeSplit, nodeType, tps, delays):
    resDF = pandas.DataFrame()
    mosMap = []
    
    xAxis = []
    yAxis = []
    for x in delays:
        if x not in xAxis:
            xAxis.append(x)
        for y in tps:
            yAxis.append(y)
            mosMap.append([])
            mosVals=[]
            for numN in range(nodeSplit[nodeTypes.index(nodeType)]):
                mosVals.append(calcSSHnodeMOS(testName, numCLI, nodeTypes, nodeSplit, nodeType, numN, y, x)) #contains mean mos for EACH of the clients, one value is added any time in for loop 
                print("next line is mosvals")
                print(mosVals)
                #dummyTS = [1.0 * x + 5.0 for x in range(len(mosVals))]
                #resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + "tp" + str(y) + ' Mos TS' : dummyTS})], axis=1)
                #resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + "tp" + str(y) + ' Mos Val' : mosVals})], axis=1)
            
            mosMap[yAxis.index(y)].append(statistics.mean(mosVals))
            #print(file_dir) 
            print(mosMap)
            if not os.path.exists('../../../exports/heatMap/'):
                os.makedirs('../../../exports/heatMap/')
                
            with open('../../../exports/heatMap/'+ makeFullScenarioName(testName,numCLI,nodeTypes,nodeSplit) + '.csv', mode='w') as writeFile:
                print('../../../exports/heatMap/'+ makeFullScenarioName(testName,numCLI,nodeTypes,nodeSplit) + '.csv')
                fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                fw.writerow(xAxis)
                fw.writerow(yAxis)
                fw.writerow(mosMap)
            # if not os.path.exists('../tempResults/'):
            #     os.makedirs('../tempResults/')
            # with open('../tempResults/'+testName+nodeType+'.csv', mode='w') as writeFile:
            #     fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            #     fw.writerow(xAxis)
            #     fw.writerow(yAxis)
            #     fw.writerow(mosMap)


    #         if not os.path.isfile(os.path.join(file_dir,'../tempResults/'+testName+nodeType+'.csv')):
    #             mosMap.to_csv(os.path.join(file_dir,'../tempResults/'+testName+nodeType+'.csv'), index=True)
    #         else:
    #             csv_input = pd.read_csv(os.path.join(file_dir,'../tempResults/'+testName+nodeType+'.csv'))
    #             csv_input.append(resDF)
    #             resDF.to_csv(os.path.join(file_dir,'../tempResults/'+testName+nodeType+'.csv'), index=True)

    # if not os.path.exists('../exports/heatMap/'):
    #     os.makedirs('../exports/heatMap/')
    # with open('../exports/heatMap/'+makeFullScenarioName(testName,nodeSplit)+'.csv', mode='w') as writeFile:
    #     fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    #     fw.writerow(xAxis)
    #     fw.writerow(yAxis)
    #     fw.writerow(mosMap)



if __name__ == "__main__":
    name = sys.argv[2]
    print(name)
    numVID = int(name.split('_VID')[1].split('_LVD')[0])
    numLVD = int(name.split('_LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('_FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('_SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_HVIP')[0])
    numHVIP = int(name.split('_HVIP')[1])
   # print(name.split('_HVIP')[1])
    numCLI = numVID + numLVD + numFDO + numSSH + numVIP + numHVIP
    if (numSSH!=0):
        tps = [x for x in range (5*numSSH, 11*numSSH, 1*numSSH)] #in kbps
        delays = [20] #ms
        recalculateQoEsimulationRun(sys.argv[1], numCLI, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostHVIP'],  [numVID, numLVD, numFDO, numSSH, numVIP, numHVIP], 'hostSSH', tps, delays)
