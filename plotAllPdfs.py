from optparse import OptionParser
from modelNames import getGoodModelNames
#from modelNames import getModelNames

parser = OptionParser()
parser.add_option("-c", "--category" , dest="category" , 
                  help = "the category: either 'btag' or 'antibtag'"          )
parser.add_option("-r", "--rebin"    , dest="rebin"    , 
                  help = "optional rebin factor"                              )
parser.add_option("-x",  action="store_true", dest="chiSquare", default=False, 
                  help = "print out background pdfs' chisquare"               )
parser.add_option("-b", action="store_true", dest="batch"     , default=False,
                  help = "turn on batch mode"                                 )
(options, args) = parser.parse_args()

if not options.category in ["btag", "antibtag"]:
  print "Must choose either 'btag' or 'antibtag' category with -c option."
  exit(1)
cat = options.category
from ROOT import *
if options.batch:
  gROOT.SetBatch()
RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING) ;
#inFiles = [TFile("allpdfs_weighted/env_pdf_0_13TeV_atlas1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_exp1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_expow1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_pow1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_vvdijet1_fix5_%s.root" % cat)]
inFiles = []
for modelName in getGoodModelNames(options.category):
  inFiles.append(TFile('gof_saturated_%s/cat-%s_model-%s.root' % (options.category, options.category, modelName)))

gSystem.Load("libdiphotonsUtils")
gSystem.Load("libHiggsAnalysisCombinedLimit")

pdfs={}
for inFile in inFiles:
  pdfName = inFile.GetName().replace("gof_saturated_%s/cat-%s_model-" % (options.category, options.category),"").replace(".root","")
  pdfs[inFile.GetName()] = inFile.Get("Vg").pdf(pdfName)
  pdfs[inFile.GetName()].Print()

print pdfs
xVar = inFiles[0].Get("Vg").var("x")
frame = xVar.frame()
data = inFiles[0].Get("Vg").data("data_obs")
data.plotOn(frame, RooFit.Name("gData"))
masterCan = TCanvas("masterCan_%s" % options.category, "fits: %s category" % options.category)
can = TCanvas("allPdfs", "raw pdfs")
can.cd()
frame.Draw()

iBlue = -2
invMass = Double()
obs = Double()
nEventsData = data.sumEntries()
intVar = xVar.Clone()
argset = RooArgSet(intVar)
if options.chiSquare:
  chiSquareLog = open("chisquareLog_%s.txt" % options.category, "w")
  diff = 0
pdfHists = []
for pdf in pdfs.keys():
  pdfs[pdf].plotOn(frame, RooFit.LineColor(kBlue + iBlue))
  pdfHists.append(TH1F("hist_%s" % pdfs[pdf].GetName(), pdfs[pdf].GetName(), 4000, 700, 4700))
  if options.chiSquare:
    invMass = Double(0)
    obs = Double(0)
    chiSquare = Double(0)
    #chiSquareLog.write("model %s: chi^2 = %f (RooPlot method)\n" % (pdfs[pdf].GetName(), frame.chiSquare()))
    #chiSquareLog.write("model %s: chi^2 = %f (createChi2 method)\n" % (pdfs[pdf].GetName(), pdfs[pdf].createChi2(data).getVal()))
    #function = pdfs[pdf].asTF(RooArgList(xVar))
    #chiSquareLog.write("model %s: chi^2 = %f (TF1 method)\n" % (pdfs[pdf].GetName(), frame.findObject("gData").Chisquare(function)))
  print "number of data events : %i" % data.sumEntries()
  diffRebin = 0
  obsRebin = 0
  predRebin = 0
  iRebin = 0
  chiSquareRebin = 0
  #for iPt in range(0, can.GetPrimitive("gData").GetN()):
  for iPt in range(0, 2700):
    can.GetPrimitive("gData").GetPoint(iPt, invMass, obs)
    intVar.setRange("range", invMass-0.5, invMass+0.5)
    pred = pdfs[pdf].createIntegral(argset, RooFit.NormSet(argset), RooFit.Range("range")).getVal()*nEventsData
    pdfHists[-1].Fill(invMass, pred)
    diff = obs - pred  
    obsRebin += obs
    predRebin += pred
    iRebin += 1
    #print "pdf %s: invMass %i, obs=%f, prediction=%f, diff=%f" % (pdfs[pdf].GetName(), invMass, obs, pred, diff)
    if obs>0 and options.chiSquare:
      chiSquare+=((obs-pred)*(obs-pred))/can.GetPrimitive("gData").GetErrorY(iPt)
    if iRebin == 50: 
      diffRebin = obs-pred
      print "pdf %s: invMass %i, obs=%f, prediction=%f, diff=%f, diff^2=%f, pChi2=%f" % (pdfs[pdf].GetName(), invMass, obs, pred, diffRebin, diffRebin*diffRebin, diffRebin*diffRebin/pred)
      diffRebin=0
      iRebin=0
      if options.chiSquare:
        chiSquareRebin += (obs-pred)*(obs-pred)/pred
  if options.chiSquare:
    chiSquareLog.write("model %s: chi^2 = %f (manual method), chi2rebin = %f\n\n" % (pdfs[pdf].GetName(), chiSquare, chiSquareRebin))
  iBlue += 1
if options.chiSquare:
  chiSquareLog.close()

frame.Draw()

can.SaveAs("allPdfs.root")

if options.rebin is not None:
  rebinCan = TPad("dataFit_%s" % cat, "%s: fits" % cat, 0, 0.3, 1, 1.0)
  hist = TH1F("rebinned_fit", "Fits (rebinned)", 4000, 700, 4700)
  x = Double()
  y = Double()
  maxY = Double(0)
  maxX = Double(0)
  #print "graph.GetN() returns %i" % can.GetPrimitive("h_data_obs").GetN()
  for iPoint in range(0, can.GetPrimitive("gData").GetN()+5):
    can.GetPrimitive("gData").GetPoint(iPoint, x, y)
    #if (y > 0):
      #print "checking point %i: (%f, %f)" % (iPoint, x, y)
    histBin = hist.GetXaxis().FindBin(x)
    hist.SetBinContent(histBin, y)
    #if (y > 0):
      #print "set bin %i at %f to %f" % (histBin, hist.GetXaxis().GetBinCenter(histBin), y)
    if y>Double(maxY):
      #print "%f is greater than %f for y coordinate" % (y, maxY)
      maxY = Double(y)
    if y>=Double(1) and x>Double(maxX):
      maxX = Double(x)
      #print "%f is greater than %f for x coordinate where y is %f" % (x, maxX, y)
  #print "maxY is %f" % maxY
  #print "maxX is %f" % maxX
  hist.Rebin(int(options.rebin))
  for pdfHist in pdfHists:
    pdfHist.Rebin(int(options.rebin))
  rebinCan.cd()
  hist.SetStats(kFALSE)
  hist.Draw("PE1")
  hist.SetMarkerStyle(20)
  hist.SetLineColor(kBlack)
  hist.GetYaxis().SetRangeUser(0.2, maxY*float(options.rebin)*1.2)
  hist.GetXaxis().SetRangeUser(675, maxX*1.1)
  hist.GetXaxis().SetTitle("m_{j#gamma} (GeV)")
  hist.Draw("PE1")
  hist.SetTitle("%s category: fits" % cat)
  hist.GetYaxis().SetTitle("Events / %i GeV" % int(options.rebin))

  curves = []
  iColor = 0
  colors = [kBlue, kBlue+1, kGreen, kGreen+1, kGreen+2, kBlack,  kCyan+3, kCyan+2, kCyan+1, kMagenta+3, kMagenta+2, kMagenta+1, kRed, kRed+1, kOrange, kOrange+1, kRed-2, kRed, kRed+2, kViolet-2, kViolet, kViolet+2]
  #widths = [7, 5, 3, 3, 3]
  for prim in can.GetListOfPrimitives():
    if "RooCurve" in prim.IsA().GetName():
      curves.append(prim)
  for curve in curves:
    for iPoint in range(0, curve.GetN()):
      curve.GetPoint(iPoint, x, y)
      curve.SetPoint(iPoint, x, y*float(options.rebin))
    curve.RemovePoint(0)
    curve.RemovePoint(1)
    curve.Draw("SAME")
    curve.SetLineColor(colors[iColor])
    #curve.SetLineWidth(widths[iColor])
    curve.SetFillColor(kWhite)
    iColor += 1
  masterCan.cd()
  rebinCan.Draw()
    

  rebinCan.BuildLegend()
  rebinCan.SetLogy()
  #rebinCan.SaveAs("rebinnedPdfs_%s.root" % cat)
  #ratioCan = TCanvas()
  ratioCan = TPad("ratioPad_%s" % cat, "%s: Data/Fit" % cat, 0, 0.05, 1, 0.3) 
  ratioCan.cd()
  first = True
  histClones = []
  for i in range(0, len(pdfHists)):
    histClones.append(hist.Clone())
    histClones[-1].SetName("pdfHist_%i" % i)
    histClones[-1].Sumw2()
    histClones[-1].Divide(pdfHists[i])
    histClones[-1].SetMarkerColor(colors[i])
    histClones[-1].SetMarkerSize(0.5)
    histClones[-1].SetLineColor(colors[i])
    histClones[-1].GetYaxis().SetRangeUser(0,2)
    histClones[-1].GetYaxis().SetRangeUser(0,2)
    histClones[-1].GetYaxis().SetTitle("data/fit")
    histClones[-1].GetYaxis().SetTitleOffset(0.3)
    histClones[-1].GetYaxis().SetTitleSize(.12)
    histClones[-1].SetStats(kFALSE)
    histClones[-1].GetXaxis().SetLabelSize(0.10)
    histClones[-1].GetXaxis().SetTitleSize(0.13)
    histClones[-1].GetXaxis().SetTitleOffset(2)
    if first:
      histClones[-1].GetYaxis().SetLabelSize(0.1)
      histClones[-1].GetYaxis().SetNdivisions(405)
      histClones[-1].SetTitle("")
      histClones[-1].Draw("PE1")
      first = False
    else:
      histClones[-1].Draw("SAME PE1")
    i+=1
  #ratioCan.SaveAs("ratios_%s.root" % cat)
    
  masterCan.cd()
  ratioCan.Draw()
  masterCan.SaveAs("rebinnedPdfs_%s.root" % cat)
     

if options.chiSquare:
  print "\n\n\n----- chisquares log -----" 
  chiSquareReadback = open("chisquareLog_%s.txt" % options.category, "r")
  print chiSquareReadback.read()
  chiSquareReadback.close()
