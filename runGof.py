from os import path, chmod, makedirs
import subprocess as sp
from optparse import OptionParser
from glob import glob
import shlex
from modelNames import getModelNames
from condorFactory import *

####
# prepares a bunch of scripts and jdl files
# for running goodness-of-fit tests
# John Hakala 1/27/2017
####

def getDcardName(category, modelName, outDir):
  return "%s/datacard_%s_%s.txt" % (outDir, category, modelName)

def makeOneDatacard(inFile, dcardTemplate, category, modelName, outDir):
  dcardTemplate.seek(0)
  outDcard    = open(getDcardName(category, modelName, outDir), "w")
  for line in dcardTemplate:
    if "shapes background" in line:
      outDcard.write(line.replace("backgroundRootFile", inFile).replace("backgroundPdf", modelName))
    else:
      outDcard.write(line)
  outDcard.close()
  print "  > made datacard for model %s: %s" % (modelName, outDcard.name)

def makeDatacards(category, inFile, outDir, fit):
  print "Will make datacards for all models specified in modelNames.py"
  if not path.exists(outDir):
      makedirs(outDir)
  dcardTemplate = open("datacard_template_%s.txt" % category, "r")

  for modelName in getModelNames():
    bkgFileName = "cat-%s_model-%s.root" % (category, modelName)
    if fit:
      dataLinkName = "w_data_%s.root" % options.category
      dataFile = TFile(dataLinkName)
      dataWS   = dataFile.Get("Vg")
      dataRooHist  = dataWS.data("data_obs")

      inTfile = TFile(inFile)
      dump = inTfile.Get("Vg")
      bkgPdfDict = getPdfFromDump(category, dump, modelName, False, dataRooHist, "gof", True) 

      outBkgFile = TFile("%s/%s" % (outDir, bkgFileName), "RECREATE")
      bkgPdfDict["rooWS"].Write()
      outBkgFile.Close()

    makeOneDatacard(bkgFileName, dcardTemplate, category, modelName, outDir)

def checkForDatacard(outDir, dcardName):
  txtFiles = glob("%s/*.txt" % outDir)
  if not dcardName in txtFiles:
    print "Error: did not find datacard %s in working directory." % dcardName
    exit(1)

def makeGOFscripts(category, method, nToys, seed, outDir):
  for modelName in getModelNames(): 
    dcardName = getDcardName(category, modelName, outDir)
    checkForDatacard(outDir, dcardName)
    print "Will prepare gofCondor scripts to run GOF test with datacard %s using method %s" % (dcardName, method)
    incantation = "combine -M GoodnessOfFit %s -t %i -s %i --algo=%s --fixedSignalStrength=0" % (
      getDcardName(category, modelName, outDir).replace("%s/" % outDir,"")  ,
      nToys                           ,
      seed                            ,
      method
    )
    pName = "cat-%s_meth-%s_model-%s_nToys-%i_seed-%i"%(category, method, modelName, nToys, seed)
    scriptName = "%s/gof_%s.sh" % (outDir, pName)
    jdlName =    "%s/jdl_%s.jdl" % (outDir, pName)
    script = open(scriptName, "w")
    script.write(simpleScript(incantation, "%s/%s" % (path.dirname(path.realpath(__file__)), outDir)))
    chmod(script.name, 0o777)
    jdl    = open(jdlName, "w")
    jdl.write(simpleJdl(script.name.replace("%s/" % outDir,"")))

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-c", "--category"  ,       dest="category",
                    help = "either 'btag' or 'antibtag'"                                          )
  parser.add_option("-i", "--inFile"    ,       dest="inFile",
                    help = "the input rootFile containing a workspace %s" %
                           "with all pdfs [default=bkg_pdfs.root]",  default="bkg_pdfs.root"      )
  parser.add_option("-m", action="store_false",  dest="makeDatacards",
                    help = "toggle making datacards [default=True]", default=True                 )
  parser.add_option("-g", "--doGOFtest" ,       dest="doGOFtest",
                    help = "perform GOF test on all models specified in %s" % 
                           "modelNames.py using method 'saturated' or 'KS'"                       )
  parser.add_option("-t", "--nToys"     ,       dest="nToys",   type="int",
                    help  = "the number of toys to use in the GOF test. [default=25]"             )
  parser.add_option("-f", action="store_true",  dest="fit",
                    help = "toggle fitting the backgrounds [default=False]", default=False        )
  parser.add_option("-s", "--seed"      ,       dest="seed",    type="int",
                    help  = "the random number seed to use in the GOF test. [default=501337]"     )
  (options, args) = parser.parse_args()
  

  outDir = "gofCondor"
  if options.category is None:
    parser.error("please specify 'btag' or 'antibtag' as the -c option")
  if not options.doGOFtest in [None, "saturated", "KS"]:
    parser.error("invalid GOF test specified: must be either 'saturated' or 'KS'")
  if options.doGOFtest is None:
    if options.nToys is not None:
      print "error: -t or --nToys was specified, but not running GOF test."
      exit(1)
    if options.seed is not None:
      print "error: -s or --seed was specified, but not running GOF test."
      exit(1)
    elif not options.makeDatacards:
      print "neither making datacards nor running GOF test... which means this does nothing."
      exit(2)
  else:
    if options.nToys is None:
      options.nToys = 25
    if options.seed is None:
      options.seed  = 501337

  from ROOT import *
  from getBkgFromDump import getPdfFromDump
  if options.makeDatacards:
    makeDatacards(options.category, options.inFile, outDir, options.fit)
  
  if options.doGOFtest is None:
    print "Done making datacards. Will not perform GOF test."
  
  if options.doGOFtest is not None:
    makeGOFscripts(options.category, options.doGOFtest, options.nToys, options.seed, outDir)
