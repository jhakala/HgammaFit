def getModelNames():
  return [
    "bkg_dijetsimple2",
    "bkg_dijet2",
    "bkg_dijet3",
    "bkg_atlas1",
    "bkg_atlas2",
    "bkg_atlas3",
    "bkg_expow1",
    "bkg_expow2",
    "bkg_expow3",
    "bkg_cheb1",
    "bkg_cheb2",
    "bkg_cheb3",
    "bkg_exp1",
    "bkg_exp3",
    "bkg_pow1",
    "bkg_pow3",
    "bkg_lau1",
    "bkg_lau2",
    "bkg_lau3",
    "bkg_vvdijet1",
    "bkg_vvdijet2"
  ]
def getGoodModelNames(category):
  if not category in ["btag", "antibtag"]:
    print "error: got a bad category in getGoodModelNames: %s" % category
    exit(1)
  elif category == "btag":
    return [
      "bkg_dijetsimple2",
      "bkg_atlas1",
      "bkg_expow1",
      "bkg_exp1",
      #"bkg_lau1",
      "bkg_vvdijet1"
    ]
  elif category == "antibtag":
    return [
      "bkg_atlas1",
      "bkg_dijetsimple2",
      "bkg_exp1",
      "bkg_expow1",
      # FOR TESTING
      #"bkg_exp2",
      "bkg_exp3",
      "bkg_pow1",
      #"bkg_pow2",
      "bkg_pow3",
      "bkg_expow2",
      "bkg_expow3",
      #"bkg_lau1",
      "bkg_vvdijet1"
    ]
