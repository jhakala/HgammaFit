from optparse import OptionParser()

def buildOneDatacard(mass, fitModel, template):
  fitHTML = open(
  template.seek(0)
  for line in template:
    if "shapes signal" in line:
     
  

if __name__ == "__main__":

parser = OptionParser()
parser.add_option("-f", "--fitModel", dest="fitModel"
                  help = "the name of the fit model to build a datacard for."                   )
parser.add_option("-c", "--category", dest="category"
                  help = "the category: eithe 'btag' or 'antibtag'."                            )
(options, args) = parser.parse_args()

if not options.category in ["antibtag", "btag"]:
  "error: invalid category"
  exit(1)


templateName = "gofCondor/datacard_%s_bkg_%s.txt" % (options.category, options.fitModel)
template = open(templateName)
outdirName   = "datacards_%s_%s" % (options.category, options.fitModel)

masses=[]
mass = 700
while mass <=3250
  masses.append(mass)
  buildOneDatacard(mass, fitModel, template)
  masses+=10


  
