from os import path, chmod
import subprocess as sp
from optparse import OptionParser
from glob import glob
import shlex
from modelNames import getModelNames
from condorFactory import *

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
parser.add_option("-s", "--seed"      ,       dest="seed",    type="int",
                  help  = "the random number seed to use in the GOF test. [default=501337]"     )
(options, args) = parser.parse_args()

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
  options.nToys = 25
  options.seed  = 501337

def getDcardName(category, modelName):
  return "condor/datacard_%s_%s.txt" % (category, modelName)

def makeDatacards(category, inFile):
  print "Will make datacards for all models specified in modelNames.py"
  dcardTemplate = open("datacard_template_antibtag.txt", "r")
  for modelName in getModelNames():
    dcardTemplate.seek(0)
    outDcard    = open(getDcardName(category, modelName), "w")
    for line in dcardTemplate:
      if "shapes background" in line:
        outDcard.write(line.replace("backgroundRootFile", inFile).replace("backgroundPdf", modelName))
      else:
        outDcard.write(line)
    outDcard.close()
    print "  > made datacard for model %s: %s" % (modelName, outDcard.name)

def makeGOFscripts(category, method, nToys, seed):
  for modelName in getModelNames(): 
    dcardName = getDcardName(category, modelName)
    txtFiles = glob("condor/*.txt")
    if not dcardName in txtFiles:
      print "Error: did not find datacard %s in working directory." % dcardName
      exit(1)
    print "Will prepare condor scripts to run GOF test with datacard %s using method %s" % (dcardName, method)
    incantation = "combine -M GoodnessOfFit %s -t %i -s %i --algo=%s --fixedSignalStrength=0" % (
      getDcardName(category, modelName).replace("condor/","")  ,
      nToys                           ,
      seed                            ,
      method
    )
    pName = "cat-%s_meth-%s_model-%s_nToys-%i_seed-%i"%(category, method, modelName, nToys, seed)
    scriptName = "condor/gof_%s.sh" % pName
    jdlName =    "condor/jdl_%s.jdl" % pName
    script = open(scriptName, "w")
    script.write(simpleScript(incantation, "%s/condor" % path.dirname(path.realpath(__file__))))
    chmod(script.name, 0o777)
    jdl    = open(jdlName, "w")
    jdl.write(simpleJdl(script.name.replace("condor/","")))

if options.makeDatacards:
  makeDatacards(options.category, options.inFile)

if options.doGOFtest is None:
  print "Done making datacards. Will not perform GOF test."

if options.doGOFtest is not None:
  makeGOFscripts(options.category, options.doGOFtest, options.nToys, options.seed)
