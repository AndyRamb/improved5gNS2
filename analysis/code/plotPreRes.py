import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import math
import statistics
from scipy import stats
import os,sys,inspect

apps = ['VID','LVD','FDO','VIP','SSH']
rejects = ['RVID','RLVD','RFDO','RVIP','RSSH']

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
print(parentdir)

colormap = plt.get_cmap('Set1').colors
# print(colormap)
colorMapping = {
    'VID' : colormap[0],
    'LVD' : colormap[1], 
    'FDO' : colormap[2], 
    'SSH' : colormap[3], 
    'VIP' : colormap[4],
    'cVIP' : colormap[5],
    'all' : colormap[6]
}

def importDF(type, testName):
    # File that will be read
    file_to_read = '../Pre/'+type + '/' + testName + '.csv'
    print("Results from run: " + file_to_read)
    # Read the CSV
    return pd.read_csv(file_to_read)


def plot_ClientAdmission(testName):
    df = importDF('Client_admission', testName)

    fig, ax = plt.subplots()
    for i in range(len(apps)):
        tmp = 0
        for index, row in df.iterrows():
            if row[rejects[i]] > tmp:
                print(row['Time'],row[rejects[i]]-tmp,row[apps[i]], apps[i])
                tmp = row[rejects[i]]
                plt.plot(row['Time'],row[apps[i]], 'ro')
                
    df = df.set_index("Time", inplace=False)
    for app in apps:
        plt.plot(df[app], drawstyle='steps-post' ,label=app, color=colorMapping[app])

    plt.xlim(xmin=0.0, xmax=400)
    plt.ylim(ymin=0.0)
    plt.legend()
    plt.title(testName + ' Client admission')
    plt.xlabel("Time")
    plt.ylabel("Number of clients")
    fig.savefig("../Pre/plots/" + testName + "/CA_" + testName + ".png", dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plot_ResourceAllocation(testName):
    df = importDF('Resource_alloc', testName)
    fig, ax = plt.subplots()

    df = df.set_index("Time", inplace=False)
    for app in apps:
        plt.plot(df[app], drawstyle='steps-post', label=app, color=colorMapping[app])

    plt.xlim(xmin=0.0)
    plt.ylim(ymin=0.0)
    plt.legend()
    plt.title(testName + ' Resource allocation')
    plt.xlabel("Time")
    plt.ylabel("BPS")
    fig.savefig("../Pre/plots/" + testName + "/RA_" + testName + ".png", dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


def plot_all(testName):
    plotPath = '../Pre/plots/' + testName
    if not os.path.exists(plotPath):
        os.makedirs(plotPath)
    plot_ClientAdmission(testName)
    plot_ResourceAllocation(testName)

# plot_all('testingCSVequal')
# plot_all('testingCSVstatic')

if __name__ == "__main__":
    plot_all(sys.argv[1])