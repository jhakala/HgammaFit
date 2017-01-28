from os import path, makedirs, chmod
from optparse import OptionParser
from modelNames import getModelNames
from condorFactory import *
from getBkgFromDump import getPdfFromDump
from runGof import getDcardName, checkForDatacard, makeOneDatacard, makeDatacards

###
# Prepares a bunch of scripts and jdl files
# for running MaxLikelihoodFits in condor
# John Hakala, 1/27/2017
###

def makeMlFitScripts(category, inWorkspace, rooDataHist, nToys, seed, outDir, remakeDatacards):
  print "nToys is %i" % nToys
  print "seed is %i" % seed
  dcardTemplate = open("datacard_template_%s.txt" % category, "r")
  for modelName in getModelNames():
    if not path.exists(outDir):
        makedirs(outDir)
    outBkgFileName = "cat-%s_model-%s.root" % (category, modelName)
    print "Will make background workspace %s for mlfits in dir %s" % (outBkgFileName, outDir)

    bkgPdfDict = getPdfFromDump(category, inWorkspace, modelName, False, rooDataHist, "mlfit", True) 
    outBkgFile = TFile("%s/%s" % (outDir, outBkgFileName), "RECREATE")
    bkgPdfDict["rooWS"].Write()
    outBkgFile.Close()
    
    dcardName = getDcardName(category, modelName, outDir)
    plotsDir = "%s_%s" % (category, modelName)
    print "plotsDir is: %s" % plotsDir
    print "Will prepare mlfitCondor scripts to run MaxLikelihoodFit with datacard %s using background %s in file %s" % (dcardName, modelName, outBkgFile.GetName())
    incantation = "combine -M MaxLikelihoodFit %s -t %i -s %i --expectSignal=0.0 --plots --saveNormalizations --saveShapes --saveWithUncertainties --out %s" % (
      getDcardName(category, modelName, outDir).replace("%s/" % outDir,"")  ,
      nToys                           ,
      seed                            ,
      plotsDir
    )
    if not path.exists(path.join(outDir, plotsDir)):
        makedirs(path.join(outDir, plotsDir))
    pName = "cat-%s_model-%s_nToys-%i_seed-%i"%(category, modelName, nToys, seed)
    scriptName = "%s/mlfit_%s.sh" % (outDir, pName)
    jdlName =    "%s/jdl_%s.jdl" % (outDir, pName)
    script = open(scriptName, "w")
    script.write(simpleScript(incantation, "%s/%s" % (path.dirname(path.realpath(__file__)), outDir)))
    chmod(script.name, 0o777)
    jdl    = open(jdlName, "w")
    jdl.write(simpleJdl(script.name.replace("%s/" % outDir,""))) 
    if remakeDatacards:
      makeOneDatacard(outBkgFileName, dcardTemplate, category, modelName, outDir)
    checkForDatacard(outDir, dcardName)
    

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-c", "--category"  ,       dest="category",
                    help = "either 'btag' or 'antibtag'"                                          )
  parser.add_option("-i", "--inFile"    ,       dest="inFile",
                    help = "the input rootFile containing a workspace %s" %
                           "with all pdfs [default=bkg_pdfs.root]",  default="bkg_pdfs.root"      )
  parser.add_option("-m", action="store_false",  dest="makeDatacards",
                    help = "toggle making datacards [default=True]", default=True                 )
  parser.add_option("-f", action="store_false",  dest="makeFitScripts",
                    help = "toggle making fit scripts [default=True]", default=True               )
  parser.add_option("-t", "--nToys"     ,       dest="nToys",   type="int", default=1,
                    help  = "the number of toys to use in the mlfit test. [default=1]"             )
  parser.add_option("-s", "--seed"      ,       dest="seed",    type="int", default=501337,
                    help  = "the random number seed to use in the GOF test. [default=501337]"     )
  (options, args) = parser.parse_args()

  outDir = "mlfitCondor"
  dataLinkName = "w_data_%s.root" % options.category

  if options.makeFitScripts:
    
    from ROOT import *
    dataFile = TFile(dataLinkName)
    dataWS   = dataFile.Get("Vg")
    dataRooHist  = dataWS.data("data_obs")

    inFile = TFile(options.inFile)
    dump = inFile.Get("Vg")

    makeMlFitScripts(options.category, dump, dataRooHist, options.nToys, options.seed, outDir, options.makeDatacards)



