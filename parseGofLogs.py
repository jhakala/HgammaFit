from glob import glob
import re
from pprint import pprint
methods = ["saturated", "KS"]
categories = ["antibtag", "btag"]

debug = False
for method in methods:
  for category in categories:
    gofMap = {}
    inDir = "gof_%s_%s" % (method, category)
    gofLogNames = glob("%s/condorLogs/*.stdout" % inDir)
    if debug:
      print gofLogNames
    for gofLogName in gofLogNames:
      testStatistic = None
      lowerBound = None
      upperBound = None
      modelName = gofLogName.split("bkg_")[-1].split("_nToys")[0]
      if debug:
        print modelName
      gofLog = open(gofLogName, "r")
      for line in gofLog:
        if debug:
          print line,
        if "mean" in line and "expected limit" in line:
          testStatistic = line.split()[5]
          if debug:
            print "test statistic:", testStatistic
        if "68%" in line:
          lowerBound = line.split()[4]
          if debug:
            print "lower Bound:", lowerBound
          
          upperBound = line.split()[8]
          if debug:
            print "upper Bound:", upperBound
        #gofMap[modelName] = {"testStatistic": testStatistic}
        gofMap[modelName] = {"testStatistic": testStatistic, "lowerBound":lowerBound, "upperBound":upperBound}
    if debug:
      pprint(gofMap)
    gofTable = open("gofTable_%s_%s.txt" % (method, category), "w")
    gofTable.write("{:<15} & {:<7} & {:<20} & {:<20} & {:<20}\\\\ \n".format("Model", "Order", "Lower Bound", "Test Statistic", "Upper Bound"))
    gofTable.write("\\hline\n")
    #for modelName in gofMap:
    #from operator import itemgetter
    for modelName in sorted(gofMap, key=lambda x:gofMap[x]['testStatistic']): 
      modelTitle =re.split('(\d+)', modelName)[0]
      order =re.split('(\d+)', modelName)[1]
      gofTable.write("{:<15} & {:<7} & {:<20} & {:<20} & {:<20}\\\\ \n".format(modelTitle, order, gofMap[modelName]["lowerBound"], gofMap[modelName]["testStatistic"], gofMap[modelName]["upperBound"]))
    gofTable.close()
      

