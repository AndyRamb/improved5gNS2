import numpy as np
rates= [{'sliceSSH': 17, 'sliceVIP': 20, 'sliceVID': 23, 'sliceLVD': 20, 'sliceFDO': 20}, {'sliceSSH': 12, 'sliceVIP': 20, 'sliceVID': 28, 'sliceLVD': 20, 'sliceFDO': 20}, {'sliceSSH': 7, 'sliceVIP': 20, 'sliceVID': 33, 'sliceLVD': 20, 'sliceFDO': 20}, {'sliceSSH': 6, 'sliceVIP': 12, 'sliceVID': 42, 'sliceLVD': 20, 'sliceFDO': 20}, {'sliceSSH': 6, 'sliceVIP': 8, 'sliceVID': 46, 'sliceLVD': 20, 'sliceFDO': 20}]
for t in np.arange(len(rates)):
    print(rates[t]["sliceSSH"])