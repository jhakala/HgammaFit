# macro to simplify background fitting procedures
from ROOT import *

printInfo = True

extLibs = ['libdiphotonsUtils', 'libHiggsAnalysisCombinedLimit', 'libdiphotonsRooUtils', 'libflashggFinalFitBackground']
for lib in extLibs:
  gSystem.Load(lib)
pdfFactory = PdfModelBuilder()

xVar = RooRealVar("x", "x", 800, 4800)
xVar.setBins(4000)

pdfFactory.setObsVar(xVar)

def getPdfTypes():
  return ["DijetSimple", "Dijet" , "VVdijet" , "Atlas" , "Expow" , "Chebychev" , "Exponential", "PowerLaw" , "Laurent"] 

def getPdf(name, ext, order):
  if name=="DijetSimple":
    return pdfFactory.getDijetSimple(       "%s_dijetsimple%i" % (ext, order), order) 
  if name=="Dijet":
    return pdfFactory.getDijet(             "%s_dijet%i"       % (ext, order), order) 
  if name=="VVdijet":
    return pdfFactory.getVVdijet(           "%s_vvdijet%i"     % (ext, order), order) 
  if name=="Atlas":
    return pdfFactory.getAtlas(             "%s_atlas%i"       % (ext, order), order) 
  if name=="Expow":
    return pdfFactory.getExpow(             "%s_expow%i"       % (ext, order), order) 
  if name=="Chebychev":
    return pdfFactory.getChebychev(         "%s_cheb%i"        % (ext, order), order) 
  if name=="Exponential":
    return pdfFactory.getExponentialSingle( "%s_exp%i"         % (ext, order), order) 
  if name=="PowerLaw":
    return pdfFactory.getPowerLawSingle(    "%s_pow%i"         % (ext, order), order) 
  if name=="Laurent":
    return pdfFactory.getLaurentSeries(     "%s_lau%i"         % (ext, order), order) 

pdfs=[]
for name in getPdfTypes():
  for order in range(1, 4):
    if getPdf(name, "bkg", order):
      pdfs.append(getPdf(name, "bkg", order))

if printInfo:
  print "\n\n\n"
  print "-------  Info about the Vgamma background pdfs -------"
  xVar.Print()
  for pdf in pdfs:
    pdf.Print()
    print " --> this object has name %s" % pdf.GetName()
  print "------------------------------------------------------"

outWorkspace = RooWorkspace("Vg")
getattr(outWorkspace, 'import')(xVar, RooCmdArg()) # https://sft.its.cern.ch/jira/browse/ROOT-6785
for pdf in pdfs:
  getattr(outWorkspace, 'import')(pdf, RooCmdArg())
outWorkspace.SaveAs("bkg_pdfs.root")
