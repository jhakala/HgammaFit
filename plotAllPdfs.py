from optparse import OptionParser

parser = OptionParser()
parser.add_option("-c", "--category" , dest="category" , 
                  help = "the category: either 'btag' or 'antibtag'"    )
parser.add_option("-r", "--rebin"    , dest="rebin"    , 
                  help = "optional rebin factor"                        )
parser.add_option("-b", action="store_true", dest="batch"     , default=False,
                  help = "turn on batch mode" )
(options, args) = parser.parse_args()

if not options.category in ["btag", "antibtag"]:
  print "Must choose either 'btag' or 'antibtag' category with -c option."
  exit(1)
cat = options.category
from ROOT import *
if options.batch:
  gROOT.SetBatch()

#inFiles = [TFile("allpdfs_weighted/env_pdf_0_13TeV_atlas1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_exp1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_expow1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_pow1_fix5_%s.root" % cat), TFile("allpdfs_weighted/env_pdf_0_13TeV_vvdijet1_fix5_%s.root" % cat)]
if options.category == "btag":
  inFiles = [
    TFile('gofCondor/cat-btag_model-bkg_atlas1.root'),
    TFile('gofCondor/cat-btag_model-bkg_dijetsimple2.root'),
    TFile('gofCondor/cat-btag_model-bkg_exp1.root'),
    TFile('gofCondor/cat-btag_model-bkg_expow1.root'),
    TFile('gofCondor/cat-btag_model-bkg_lau1.root'),
    TFile('gofCondor/cat-btag_model-bkg_vvdijet2.root'),
  ]
else:
  inFiles = [
    TFile('gofCondor/cat-antibtag_model-bkg_atlas1.root'),
    TFile('gofCondor/cat-antibtag_model-bkg_dijetsimple2.root'),
    TFile('gofCondor/cat-antibtag_model-bkg_exp1.root'),
    TFile('gofCondor/cat-antibtag_model-bkg_expow1.root'),
    TFile('gofCondor/cat-antibtag_model-bkg_lau1.root'),
    TFile('gofCondor/cat-antibtag_model-bkg_vvdijet1.root'),
  ]
gSystem.Load("libdiphotonsUtils")
gSystem.Load("libHiggsAnalysisCombinedLimit")

pdfs={}
for inFile in inFiles:
  pdfs[inFile.GetName()] = inFile.Get("Vg").pdf(inFile.GetName().replace("gofCondor/cat-%s_model-" % options.category,"").replace(".root",""))
  pdfs[inFile.GetName()].Print()

print pdfs
xVar = inFiles[0].Get("Vg").var("x")
frame = xVar.frame()
data = inFiles[0].Get("Vg").data("data_obs")
data.plotOn(frame)

iBlue = -2
for pdf in pdfs.keys():
  pdfs[pdf].plotOn(frame, RooFit.LineColor(kBlue + iBlue))
  iBlue += 1

can = TCanvas()
can.cd()
frame.Draw()
can.SaveAs("allPdfs.root")

if options.rebin is not None:
  rebinCan = TCanvas()
  hist = TH1F("rebinned_fit", "Fits (rebinned)", 4000, 700, 4700)
  x = Double()
  y = Double()
  maxY = Double(0)
  maxX = Double(0)
  #print "graph.GetN() returns %i" % can.GetPrimitive("h_data_obs").GetN()
  for iPoint in range(0, can.GetPrimitive("h_data_obs").GetN()+5):
    can.GetPrimitive("h_data_obs").GetPoint(iPoint, x, y)
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
  print "maxX is %f" % maxX
  hist.Rebin(int(options.rebin))
  rebinCan.cd()
  hist.Draw("PE1")
  hist.SetMarkerStyle(20)
  hist.SetLineColor(kBlack)
  hist.GetYaxis().SetRangeUser(0.2, maxY*float(options.rebin)*1.2)
  hist.GetXaxis().SetRangeUser(675, maxX*1.2)
  hist.Draw("PE1")
  hist.SetTitle("%s category: fits" % cat)

  curves = []
  iColor = 0
  colors = [kGreen, kGreen+1, kGreen+2, kBlack, kBlue, kBlue+1, kCyan+3, kCyan+2, kCyan+1, kMagenta+3, kMagenta+2, kMagenta+1, kRed, kRed+1, kOrange, kOrange+1 ]
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
    
  rebinCan.BuildLegend()
  rebinCan.SetLogy()
  rebinCan.SaveAs("rebinnedPdfs_%s.root" % cat)

