from optparse import OptionParser
from forcelink import force_symlink

####
# Script for getting a background prediction pdf from the results of the fTest
# It has an interactive mode where you can look at the pdfs in the multipdf
# as well as a mode where you can pick one without seeing the prompt.
# For help on the command line options, do
# python getBkgFromFtest.py --help
#
# John Hakala 12/28/2016
####

parser = OptionParser()
#parser.add_option("-i", "--inFtest", dest="inFtest", 
#                  help = "the input mlfit rootfile")
parser.add_option("-c", "--category"  , dest="category",
                  help = "either 'btag' or 'antibtag'"                                         )
parser.add_option("-n", "--pdfIndex"   , dest="pdfIndex",
                  help = "the index of the desired pdf in the dump"                        )
parser.add_option("-o", "--outSuffix" , dest="outSuffix"     , default="tmp",
                  help = "the suffix for the of the output : blahblahPdf_OUTSUFFIX.root"       )
parser.add_option("-a", "--altIndex"   , dest="altIndex"     ,
                  help = "the index of the alternative pdf in the dump (for bias studies)" )
parser.add_option("-b", action="store_true", dest="batch"    , default=False,
                  help = "turn on batch mode"                                                  )
parser.add_option("-p", action="store_true", dest="makePlot" , default=False,
                  help = "toggle generating a plot in pdf form"                                )
parser.add_option("-l", action="store_true", dest="makeLink" , default=False,
                  help = "make symlink 'bkg_CATEGORY.root' to the output file"                 )
parser.add_option("-d", action="store_true", dest="linkData" , default=False,
                  help = "make symlink 'w_data_CATEGORY.root' to w_data in fitFiles dir"       )
(options, args) = parser.parse_args()
if options.outSuffix is None:
  parser.error("output histogram filename not given")
if options.category is None:
  parser.error("please specify 'btag' or 'antibtag' as the -c option")

dataLinkName = "w_data_%s.root" % options.category
if options.linkData:
  force_symlink("../../../../CMSSW_7_1_5/src/dataFiles/w_data_%s.root" % options.category, dataLinkName)

from ROOT import *
if options.batch:
  gROOT.SetBatch()

extLibs = ['libdiphotonsUtils', 'libHiggsAnalysisCombinedLimit', 'libdiphotonsRooUtils', 'libflashggFinalFitBackground']
for lib in extLibs:
  gSystem.Load(lib)
def getPdfFromDump(inWorkspace, pdfName, makePlot, rooHistData) :
  rooWS = RooWorkspace("Vg")
  inWorkspace.Print()
  print "going to try to get pdf with name %s from this workspace" % pdfName
  pdfFromDump = inWorkspace.pdf(pdfName)
  origName = pdfName
  print " --->origName: %s" % origName 
  pdfFromDump.SetName("bg_%s" % options.category)
  
  nBackground=RooRealVar("bg_%s_norm" % options.category, "nbkg", rooHistData.sumEntries())
  
  getattr(rooWS, 'import')(pdfFromDump)
  getattr(rooWS, 'import')(rooHistData)
  getattr(rooWS, 'import')(nBackground)
  
  varset   = pdfFromDump.getVariables()
  varIt    = varset.iterator()
  paramVar = varIt.Next()
  #while paramVar:
  #  if paramVar.GetName() != var.GetName(): # don't remove the range from the "x" variable
  #    print "about to remove range from parameter with name %s" % paramVar.GetName()
  #    rooWS.var(paramVar.GetName()).removeRange()
  #    print "removed range from pdf with name %s" % (paramVar.GetName())
  #  paramVar = varIt.Next()
  
  result = pdfFromDump.fitTo(rooHistData, RooFit.Minimizer("Minuit2", "minimize"), RooFit.Range(700, 4700), RooFit.Strategy(2), RooFit.SumW2Error(kTRUE), RooFit.Save(1), RooFit.Offset(kTRUE))
  rooHistData.plotOn(frame)
  pdfFromDump.plotOn(frame)
  can = TCanvas()
  can.cd()
  frame.Draw()
  if makePlot:
    can.Print("fitFromFtest_%s_%s_%s.pdf" % (options.category, origName, options.outSuffix))
  return {"rooWS" : rooWS, "pdfFromDump": pdfFromDump, "origName" : origName}

inFileName = "bkg_pdfs.root"

if not options.category in ["antibtag", "btag"]:
  exit("something went wrong with the categories! \n%s" %
       ("... you picked '%s' but it has to be 'antibtag' or 'btag'" % options.category)
      )

inFile = TFile(inFileName)
dump = inFile.Get("Vg")
pdfList = dump.allPdfs()

dataFile = TFile(dataLinkName)
dataWS   = dataFile.Get("Vg")
dataRooHist  = dataWS.data("data_obs")

if options.pdfIndex is None:
  nPdfs = pdfList.getSize()
  pdfNames = []
  pdfIt = pdfList.iterator()
  for i in range(0, nPdfs):
    pdfNames.append( pdfIt.Next().GetName() )
  ans=True
  while ans:
    print "please pick a pdf:"
    for i in range( 0, len(pdfNames) ):
      print "  %i. %s " % (i, pdfNames[i])
    pdfIndex = raw_input()
    if int(pdfIndex) in range(0, len(pdfNames)): 
      ans=False
else:
  pdfIndex = options.pdfIndex

var = dump.var("x")
frame = var.frame()

print "about to get background model:"
backgroundDict     = getPdfFromDump(dump, pdfNames[int(pdfIndex)], options.makePlot, dataRooHist)
bkgPdfFromDump = backgroundDict["pdfFromDump"]
backgroundWS       = backgroundDict["rooWS"]
outFileName        = "%s_%s_%s.root" % (backgroundDict["origName"], options.outSuffix, options.category)
outFile = TFile(outFileName, "RECREATE")
outFile.cd()

backgroundWS.Write()
if options.makeLink:
  bkgLinkName = "bg_%s.root" % options.category
  force_symlink(outFileName, bkgLinkName)

if options.altIndex is not None:
  print "about to get alternate background model:"
  altDict            = getPdfFromDump(dump, pdfNames[int(options.altIndex)], options.makePlot, dataRooHist)
  altPdfFromDump = altDict["pdfFromDump"]
  altWS              = altDict["rooWS"]
  altFileName        = "%s_%s_%s.root" % (altDict["origName"], options.outSuffix, options.category)
  altFile = TFile(altFileName, "RECREATE")
  altFile.cd()
  
  altWS.Write()
  if options.makeLink:
    altLinkName = "bg_alt_%s.root" % options.category
    force_symlink(altFileName, altLinkName)

