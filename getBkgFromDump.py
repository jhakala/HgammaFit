from optparse import OptionParser
from forcelink import force_symlink

####
# Script for getting a background prediction pdf from the the dump made by dumpBkgPdfs
# It has an interactive mode where you can look at the pdfs in the dump
# as well as a mode where you can pick one without seeing the prompt.
# For help on the command line options, do
# python getBkgFromDump.py --help
#
# John Hakala 12/28/2016
####


from ROOT import *
def getPdfFromDump(category, inWorkspace, pdfName, makePlot, rooHistData, outSuffix, batch) :
  if batch:
    gROOT.SetBatch()
  
  extLibs = ['libdiphotonsUtils', 'libHiggsAnalysisCombinedLimit', 'libdiphotonsRooUtils', 'libflashggFinalFitBackground']
  for lib in extLibs:
    gSystem.Load(lib)
  rooWS = RooWorkspace("Vg")
  print "going to try to get pdf with name %s from this workspace" % pdfName
  pdfFromDump = inWorkspace.pdf(pdfName)
  origName = pdfName
  
  nBackground=RooRealVar("%s_norm" % origName, "nbkg", rooHistData.sumEntries())
  
  
  varset   = pdfFromDump.getVariables()
  varIt    = varset.iterator()
  paramVar = varIt.Next()
  var = inWorkspace.var("x")
  #var.setRange("hackRange", 725., 3000.)

  while paramVar:
    print "looking at paramVar %s" % paramVar.GetName()
    if paramVar.GetName() != var.GetName(): # don't remove the range from the "x" variable
      inWorkspace.var(paramVar.GetName()).removeRange()
      print "removed range from pdf %s with name %s" % (pdfName, paramVar.GetName())
      print "parameter with name %s had initial value %f" % (paramVar.GetName(), paramVar.getValV())
    paramVar = varIt.Next()
    
  # it seems fitTo is recommended against... ?
  #result = pdfFromDump.fitTo(rooHistData, RooFit.Minimizer("Minuit2", "minimize"), RooFit.Range(700, 4700), RooFit.Strategy(2), RooFit.SumW2Error(kTRUE), RooFit.Save(1), RooFit.Offset(kTRUE))
  #result = pdfFromDump.fitTo(rooHistData, RooFit.Minimizer("Minuit2"),RooFit.SumW2Error(kTRUE), RooFit.Strategy(2), RooFit.Hesse(0), RooFit.Save(kTRUE) )
  #result = pdfFromDump.fitTo(rooHistData, RooFit.Minimizer("Minuit2"),RooFit.SumW2Error(kTRUE), RooFit.Save())
  
  status = 1
  result = RooFitResult()
  nll = RooNLLVar("nll", "nll", pdfFromDump, rooHistData)
  #nll = RooNLLVar("nll", "nll", pdfFromDump, rooHistData, RooFit.Range("hackRange") )
  minuit = RooMinimizer(nll)
  minuit.setOffsetting(kTRUE)
  minuit.setStrategy(2)
  minuit.setEps(0.0001)
  #minuit.minimize("GSL")
  nTries = 0
  rand = TRandom()
  def doFit(refs):

    maxTries = 10+refs["tries"]
    while stat != 0 :
      minuit.minimize("Minuit", "minimize")
      refs["fitTest"] =  refs["minimizer"].save("fitTest", "fitTest")
      offset = refs["negLogLikelihood"].offset()
      minnll_woffset = refs["fitTest"].minNll()
      minnll = -offset-minnll_woffset
      refs["stat"] = refs["fitTest"].status()
      print "try %i:\n status: %i  minnll_woffset: %f, minnll: %f, offset: %f" % (refs["tries"], refs["fitTest"].status(), minnll_woffset, minnll, offset)
      refs["tries"] += 1
      if refs["tries"] == maxTries or refs["stat"] == 0:
        break
        # if refs["stat"] == 0 and not refs["passedOnce"]:
        #   refs["passedOnce"] = True
        #   print "found minimum, will run improve"
        #   refs["stat"]=-1
        #   #for i in range(0, 5):
        #   #  minuit.improve()
        #   #  print "just ran improve, going to re-minimize"
        # else:
        #   break
  references = {}
  references["passedOnce"] = False
  references["negLogLikelihood"]   = nll
  references["fitTest"]           = result
  references["stat"]              = int(status)
  references["minimizer"]         = minuit
  references["tries"]             = int(nTries)
  doFit(references)
  print "after %i tries, fit status was %i" % (references["tries"], references["stat"])
  if references["stat"] == 0:
    print "attempting to reset varIt"
    varIt.Reset()
    paramVar = varIt.Next()
    while paramVar:
      print "looking at paramVar %s" % paramVar.GetName()
      if paramVar.GetName() != var.GetName(): # only print the actual shape variables
        print "parameter with name %s had final value %f" % (paramVar.GetName(), paramVar.getValV())
        paramVar.setConstant(kFALSE)
      paramVar = varIt.Next()
      
  else:
    while references["stat"] != 0:
      references["fitTest"].randomizePars() # try to get out of the danga zone
      varIt.Reset()
      paramVar = varIt.Next()
      while paramVar:
        print "resetting %s's value"%paramVar.GetName()
        paramVar.setVal((rand.Rndm()-0.5)*10**(rand.Rndm()))
        paramVar = varIt.Next()
      print "retrying fit"
      doFit(references) # TODO: test
      if references["tries"] == 10000:
        print "fit failed after %i tries"  % references["tries"]
        exit(0)
        
  #references["fitTest"].Print()
  var = inWorkspace.var("x")
  frame = var.frame()

  rooHistData.plotOn(frame)
  ### HERE: for error bands on background fit
  pdfFromDump.plotOn(frame, RooFit.VisualizeError(references["fitTest"], 2, kFALSE), RooFit.FillColor(kOrange))
  pdfFromDump.plotOn(frame, RooFit.VisualizeError(references["fitTest"], 1, kFALSE), RooFit.FillColor(kGreen+2))
  pdfFromDump.plotOn(frame)
  can = TCanvas()
  can.cd()
  frame.Draw()
  
  #contourPlot = minuit.contour(inWorkspace.var("bkg_dijetsimple2_lin2"), inWorkspace.var("bkg_dijetsimple2_lin2"),  2.3/float(2) )
  #raw_input("Press Enter to continue...")
  if makePlot:
    can.Print("fitFromFtest_%s_%s_%s.pdf" % (category, origName, outSuffix))
  getattr(rooWS, 'import')(pdfFromDump, RooCmdArg())
  getattr(rooWS, 'import')(rooHistData, RooCmdArg())
  getattr(rooWS, 'import')(nBackground, RooCmdArg())

  fitResultFile = TFile("fitRes_%s.root" % category, "RECREATE")
  fitResultFile.cd()
  rooWS.Write()
  references["fitTest"].Write()
  can.Write()
  fitResultFile.Close()

  return {"rooWS" : rooWS, "pdfFromDump": pdfFromDump, "origName" : origName}
  
  

if __name__ == "__main__" :

  parser = OptionParser()
  parser.add_option("-c", "--category"  , dest="category",
                    help = "either 'btag' or 'antibtag'"                                         )
  parser.add_option("-n", "--pdfIndex"   , dest="pdfIndex",
                    help = "the index of the desired pdf in the dump"                            )
  parser.add_option("-i", "--inFileName" , dest="inFileName"     , default="bkg_pdfs.root",
                    help = "the input root file with the workspace containing all pdfs"          )
  parser.add_option("-o", "--outSuffix" , dest="outSuffix"     , default="tmp",
                    help = "the suffix for the of the output : blahblahPdf_OUTSUFFIX.root"       )
  parser.add_option("-a", "--altIndex"   , dest="altIndex"     ,
                    help = "the index of the alternative pdf in the dump (for bias studies)"     )
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
  inFileName = options.inFileName
  
  if not options.category in ["antibtag", "btag"]:
    exit("something went wrong with the categories! \n%s" %
         ("... you picked '%s' but it has to be 'antibtag' or 'btag'" % options.category)
        )
  if options.batch:
    gROOT.SetBatch()
  
  inFile = TFile(inFileName)
  dump = inFile.Get("Vg")
  pdfList = dump.allPdfs()
  nPdfs = pdfList.getSize()
  pdfNames = []
  pdfIt = pdfList.iterator()
  for i in range(0, nPdfs):
    pdfNames.append( pdfIt.Next().GetName() )
  
  dataFile = TFile(dataLinkName)
  dataWS   = dataFile.Get("Vg")
  dataRooHist  = dataWS.data("data_obs")
  
  if options.pdfIndex is None:
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
  
  
  print "about to get background model:"
  backgroundDict     = getPdfFromDump(options.category, dump, pdfNames[int(pdfIndex)], options.makePlot, dataRooHist, options.outSuffix, options.batch)
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
    altDict            = getPdfFromDump(category, dump, pdfNames[int(options.altIndex)], options.makePlot, dataRooHist, options.outSuffix, options.batch)
    altPdfFromDump = altDict["pdfFromDump"]
    altWS              = altDict["rooWS"]
    altFileName        = "%s_%s_%s.root" % (altDict["origName"], options.outSuffix, options.category)
    altFile = TFile(altFileName, "RECREATE")
    altFile.cd()
    
    altWS.Write()
    if options.makeLink:
      altLinkName = "bg_alt_%s.root" % options.category
      force_symlink(altFileName, altLinkName)
  
