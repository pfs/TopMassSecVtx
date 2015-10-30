#!/usr/bin/env python

import ROOT
import os,sys,re,pickle
import optparse
import math
from CMS_lumi import CMS_lumi
from runPlotter import openTFile
from makeSVLMassHistos import LUMI
from fitSecVtxProperties import normalizeDistribution

VARIABLES = ["mass", "pt", "eta", "ptfrac", "pzfrac", "ptrel", "pfrac", "ptchfrac", "pzchfrac", "dr", "wgt"]
XAXIS = {
	"D0":   "m(K^{+}#pi^{-}) [GeV]",
	"Dpm":  "m(K^{+}#pi^{-}#pi^{-}) [GeV]",
	"JPsi": "m(#mu^{+}#mu^{-}) [GeV]",
	"Dsm":  "m(K^{+}#pi^{-}#pi^{-}) - m(K^{+}#pi^{-}) [GeV]",
}

"""
builds a canvas with the unfolded distributions and saves the distributions to a file (if given)
"""
def showUnfolded(sigData,bkgData,var=None,outD='unfolded',outF=None,postfixForOutputs=''):

	if var is None: return
	name=var.GetName()

	#create canvas
	c=ROOT.TCanvas(name,name,500,500)
	c.cd()
	frame = var.frame()
	bkgData.plotOn(frame,
						ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
						ROOT.RooFit.Name(name+'_bckg'),
						ROOT.RooFit.MarkerColor(419),
						ROOT.RooFit.MarkerStyle(24),
						ROOT.RooFit.LineWidth(2),
						ROOT.RooFit.LineColor(419) )
	sigData.plotOn(frame,
						ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2),
						ROOT.RooFit.Name(name+'_signal'),
						ROOT.RooFit.MarkerColor(1),
						ROOT.RooFit.MarkerStyle(20),
						ROOT.RooFit.LineWidth(2),
						ROOT.RooFit.LineColor(1) )
	frame.Draw()
	frame.GetYaxis().SetTitle('Candidates')
	frame.GetYaxis().SetTitleOffset(1.5)
	frame.GetYaxis().SetTitleSize(0.05)
	frame.GetYaxis().SetLabelSize(0.04)
	frame.GetXaxis().SetTitle(var.GetTitle())
	frame.GetXaxis().SetTitleSize(0.05)
	frame.GetXaxis().SetLabelSize(0.04)
	frame.GetXaxis().SetTitleOffset(0.9)

	#show a legend
	leg=ROOT.TLegend(0.6,0.75,0.9,0.9,"","brNDC")
	leg.SetFillStyle(0)
	leg.SetBorderSize(0)
	leg.SetTextFont(42)
	leg.SetTextSize(0.04)
	leg.AddEntry(name+"_signal", "Signal","p")
	leg.AddEntry(name+"_bckg","Background","p")
	leg.Draw()

	#save plot
	for ext in ['.pdf', '.png', '.C']:
	#for ext in ['.pdf']:
		c.SaveAs(os.path.join(outD, name+"_unfolded%s%s"%(postfixForOutputs,ext)))

	#save also distributions if output file is given
	if outF is None: return
	outF.cd()

	#get unfolded distributions
	signalGr=c.GetPrimitive(name+'_signal')
	signalGr.Clone().Write()

	bkgGr=c.GetPrimitive(name+'_bckg')
	bkgGr.Clone().Write()

	#prepare normalized distributions as well
	for gr in [signalGr,bkgGr]:
		norm_gr=normalizeDistribution(gr)
		norm_gr.Write()


"""
do the mass fit and display the result
"""
def doTheMassFit(ws,data=None,
                 CandTypes=None,
                 showResult=False,
                 outD='unfolded',
                 postfixForOutputs=''):

	#fit the mass spectrum
	ws.pdf('model').fitTo(data,ROOT.RooFit.Extended())

	if not showResult: return

	#get the main parameters of the fit
	nsig     = ws.var("nsig").getVal()
	nsigErr  = ws.var("nsig").getError()
	nbkg     = ws.var("nbkg").getVal()
	nbkgErr  = ws.var("nbkg").getError()
	mass     = ws.var("sig_mu").getVal()
	massErr  = ws.var("sig_mu").getError()
	try:
		width    = ws.var("sig_sigma").getVal()
		widthErr = ws.var("sig_sigma").getError()
	except:
		width    = ws.var("sig_Gauss1_sigma").getVal()
		widthErr = ws.var("sig_Gauss1_sigma").getError()

	#show result of the fit
	cfit=ROOT.TCanvas("cfit","cfit",500,500)
	cfit.cd()
	frame=ws.var("mass").frame()#ROOT.RooFit.Bins(50))
	data.plotOn(frame,ROOT.RooFit.DrawOption("p"),ROOT.RooFit.MarkerStyle(20),ROOT.RooFit.Name("data"))
	ws.pdf("model").plotOn(frame, ROOT.RooFit.FillStyle(0), ROOT.RooFit.MoveToBack(), ROOT.RooFit.Name("total"))
	# ws.pdf("model").plotOn(frame,
 #                           ROOT.RooFit.Components('sig_model'),
 #                           ROOT.RooFit.LineColor(5),
 #                           ROOT.RooFit.LineWidth(1),
 #                           ROOT.RooFit.FillStyle(1001),
 #                           ROOT.RooFit.FillColor(5),
 #                           ROOT.RooFit.DrawOption("LF"),
 #                           ROOT.RooFit.MoveToBack(),
 #                           ROOT.RooFit.Name("sig"))
	ws.pdf("model").plotOn(frame,
                           ROOT.RooFit.Components('bkg_model'),
                           ROOT.RooFit.LineColor(1),
                           ROOT.RooFit.LineWidth(2),
                           ROOT.RooFit.FillStyle(1001),
                           ROOT.RooFit.FillColor(920),
                           ROOT.RooFit.DrawOption("LF"),
                           ROOT.RooFit.MoveToBack(),
                           ROOT.RooFit.Name("bkg"))
	frame.Draw()

	try:
		bkg_lambda=ws.var('bkg_lambda').getVal()
		ymin=nbkg*math.exp(frame.GetXaxis().GetXmax()*bkg_lambda)*0.2;
		ymax=1.4*frame.GetMaximum()
	except TypeError:
		ymin=0
		ymax=1.1*frame.GetMaximum()

	frame.GetYaxis().SetRangeUser(ymin,ymax)
	frame.GetYaxis().SetTitle("Candidates")
	frame.GetYaxis().SetTitleOffset(1.6)
	if '411' in str(CandTypes):
		frame.GetXaxis().SetTitle(XAXIS['Dpm'])
	if '421' in str(CandTypes):
		frame.GetXaxis().SetTitle(XAXIS['D0'])
	if '443' in str(CandTypes):
		frame.GetXaxis().SetTitle(XAXIS['JPsi'])
	if '413' in str(CandTypes):
		frame.GetXaxis().SetTitle(XAXIS['Dsm'])
	frame.GetXaxis().SetTitleOffset(0.9)
	frame.GetYaxis().SetTitleSize(0.05)
	frame.GetYaxis().SetLabelSize(0.04)
	frame.GetXaxis().SetTitleSize(0.05)
	frame.GetXaxis().SetLabelSize(0.04)
	cfit.Modified()
	cfit.Update()

	#build a legend
	leg=ROOT.TLegend(0.7,0.79,0.9,0.94,"","brNDC")
	# leg=ROOT.TLegend(0.7,0.72,0.9,0.95,"","brNDC")
	leg.SetFillStyle(0)
	leg.SetBorderSize(0)
	leg.SetTextFont(42)
	leg.SetTextSize(0.04)
	leg.AddEntry("data",  "Data",       "p")
	leg.AddEntry("bkg",   "Background", "f")
	# leg.AddEntry("sig",   "Signal",     "f")
	leg.AddEntry("total", "Total",      "f")
	leg.Draw()

	#display fit results on the canvas
	CMS_lumi(cfit,2,10)
	if not '413' in str(CandTypes):
		pt=ROOT.TPaveText(0.17,0.85,0.5,0.6,"brNDC")
	else:
		pt=ROOT.TPaveText(0.50,0.77,0.89,0.52,"brNDC")
	pt.SetFillStyle(0)
	pt.SetBorderSize(0)
	pt.SetTextFont(42)
	pt.SetTextAlign(12)
	pt.SetTextSize(0.04)

	if not '413' in str(CandTypes):
		pt.AddText("m = %3.4f #pm %3.4f GeV"%(mass,massErr))
		pt.AddText("#sigma = %3.4f #pm %3.4f GeV"%(width,widthErr))
		pt.AddText("N_{signal} = %3.0f #pm %3.0f"%(nsig,nsigErr))
		pt.AddText("N_{bkg} = %3.0f #pm %3.0f"%(nbkg,nbkgErr))
	else:
		pt.AddText("dm = %3.2f #pm %3.2f MeV"%(mass*1000,massErr*1000))
		pt.AddText("#sigma = %3.2f #pm %3.2f MeV"%(width*1000,widthErr*1000))
		pt.AddText("N_{signal} = %3.0f #pm %3.0f"%(nsig,nsigErr))
		pt.AddText("N_{bkg} = %3.0f #pm %3.0f"%(nbkg,nbkgErr))
	pt.Draw()

	#save to file
	outF='cfit%s'%postfixForOutputs

	for ext in ['.pdf', '.png', '.C']:
	#for ext in ['.pdf']:
		cfit.SaveAs(os.path.join(outD,outF+ext))



"""
generates the RooFit workspace with the data and the fitting model
"""
def generateWorkspace(CandTypes,inputUrl,postfixForOutputs,options):
	import math

	outputDir=options.output
	#################################
	foundWS = False
	try:
		cachefile = open(".charmpeakworkspaces.pck", 'r')
		workspaces = pickle.load(cachefile)
		if not options.weight:
			ws=workspaces[(tuple(inputUrl),tuple(CandTypes))]
		else:
			ws=workspaces[(tuple(inputUrl),tuple(CandTypes), options.weight)]
		print workspaces.keys()
		print ">>> Read workspace from .charmpeakworkspaces.pck"
		cachefile.close()
		foundWS = True
	except KeyError:
		ws = ROOT.RooWorkspace("w")
		print (tuple(inputUrl),tuple(CandTypes))
		print workspaces.keys()
		print ">>> Cache found, but not workspace, recreating it"

	except EOFError:
		workspaces = {}
		ws = ROOT.RooWorkspace("w")
		print ">>> EOF: Workspace not found in cache, recreating it"

	except IOError:
		workspaces = {}
		ws = ROOT.RooWorkspace("w")
		print ">>> Cache not found, creating it"

	# workspaces = {}
	# ws = ROOT.RooWorkspace("w")

	if not foundWS:
		#create the data set
		variables=ROOT.RooArgSet()
		if '421' in str(CandTypes): ## D0 #note: str([1,2,3]) = '[1,2,3]'
			variables.add( ws.factory("mass[1.85,1.70,2.0]") )
		elif '411' in str(CandTypes): ## D+
			variables.add( ws.factory("mass[1.87,1.75,1.98]") )
		elif '443' in str(CandTypes): ## J/Psi
			variables.add( ws.factory("mass[3.1,2.50,3.40]") )
		elif '-413' in str(CandTypes): ## D*-
			variables.add( ws.factory("mass[0.1455,0.1400,0.1700]") )

		variables.add(ws.factory("pt[0,0,100]") )
		variables.add(ws.factory("eta[0,0,2.5]") )
		variables.add(ws.factory("ptfrac[0,0,1.1]") )
		variables.add(ws.factory("pzfrac[0,0,1.1]") )
		variables.add(ws.factory("ptrel[0,0,4.0]") )
		variables.add(ws.factory("pfrac[0,0,1.1]") )
		variables.add(ws.factory("ptchfrac[0,0,1.1]") )
		variables.add(ws.factory("pzchfrac[0,0,1.1]") )
		variables.add(ws.factory("dr[0,0,0.3]") )
		variables.add(ws.factory("wgt[0,0,9999999.]") )
		data=ROOT.RooDataSet("data","data",variables,"wgt")

		if options.weight:
			wmatch = re.match(r'([\w]*)(?:\[([\d]{1,2})\])?',options.weight)
			wvarname = wmatch.group(1)
			wind = wmatch.group(2)
			print "Will weight events using", wvarname,
			if wind: print "index",wind
			else: print ''

		#fill the dataset
		chain=ROOT.TChain("CharmInfo")
		for f in inputUrl: chain.AddFile(f)
		nEntries = chain.GetEntries()
		print "Will loop over", nEntries, "entries."
		for i in xrange(0,nEntries):
			if i%500 == 0:
				sys.stdout.write("[%3d/100]\r" % (100*i/float(nEntries)))
				sys.stdout.flush()

			chain.GetEntry(i)
			#filter on candidate type and mass range
			if not (chain.CandType in CandTypes) : continue
			if (chain.CandMass > ws.var("mass").getMax() or
				chain.CandMass < ws.var("mass").getMin()): continue

			#compute the variables and add to the dataset
			ws.var("mass")     .setVal(chain.CandMass)
			ws.var("pt")       .setVal(chain.CandPt)
			ws.var("eta")      .setVal(abs(chain.CandEta))
			ws.var("ptfrac")   .setVal(chain.CandPt/chain.JetPt)
			ws.var("pzfrac")   .setVal(chain.CandPz/chain.JetPz)
			ws.var("ptrel")    .setVal(chain.CandPtRel)
			ws.var("pfrac")    .setVal(chain.CandPt*math.cosh(chain.CandEta)/
												(chain.JetPt*math.cosh(chain.JetEta)))
			ws.var("ptchfrac") .setVal(chain.CandPt/chain.SumPtCharged)
			ws.var("pzchfrac") .setVal(chain.CandPz/chain.SumPzCharged)
			ws.var("dr")       .setVal(chain.CandDeltaR)
			baseWeight = chain.Weight[0]*chain.XSWeight
			if chain.XSWeight != 1 : baseWeight *= LUMI
			ws.var("wgt")      .setVal(baseWeight)
			if options.weight:
				wvar = getattr(chain, wvarname)
				try:
					weight = float(wvar[int(wind)])
				except TypeError:
					weight = float(wvar)
				ws.var("wgt").setVal(weight*baseWeight)
			argset = ROOT.RooArgSet()
			for var in VARIABLES:
				argset.add(ws.var(var))
			argset.add(ws.var("wgt"))

			data.add(argset, ws.var("wgt").getVal())

		print "[  done ]"

		#import dataset to workspace
		getattr(ws,'import')(data)

		#now create a fitting model for the mass spectrum
		getattr(ws,'import')( ROOT.RooRealVar("nsig","Signal candidates",     0.,
									 0., data.sumEntries()*2) )
		getattr(ws,'import')( ROOT.RooRealVar("nbkg","Background candidates", 0.,
									 0., data.sumEntries()*2) )


		if not options.weight:
			workspaces[(tuple(inputUrl),tuple(CandTypes))] = ws
		else:
			workspaces[(tuple(inputUrl),tuple(CandTypes), options.weight)] = ws
		cachefile = open(".charmpeakworkspaces.pck", 'w')
		pickle.dump(workspaces, cachefile, pickle.HIGHEST_PROTOCOL)
		cachefile.close()
		print ">>> Wrote workspace to cache"


	##################################################
	# Specialization by candidate type
	## D+-  ##############
	if '411' in str(CandTypes):
		ws.factory("RooGaussian::sig_model(mass,sig_mu[1.87,1.86,1.88],sig_sigma[0.01,0.001,0.05])")
		#ws.factory("RooCBShape::sig_model(mass,sig_mu[1.87,1.86,1.88],sig_sigma[0.001,0,0.025],sig_alpha[1,0.5,2],sig_n[5,0,10])")
		ws.factory("RooExponential::bkg_model(mass,bkg_lambda[-0.5,-4,0])")

	## D0   ##############
	elif '421' in str(CandTypes):
		ws.factory("RooCBShape::sig_model(mass,sig_mu[1.87,1.86,1.88],sig_sigma[0.001,0,0.025],sig_alpha[1,0.5,2],sig_n[5,0,10])")
		ws.factory("RooExponential::bkg_model(mass,bkg_lambda[-0.5,-4,0])")

	## J/Psi  ############
	elif '443' in str(CandTypes):
		# ws.factory("RooCBShape::sig_CB(mass,sig_mu[3.1,3.05,3.15],sig_CB_sigma[0.07,0.01,0.5],sig_CB_alpha[1,0.5,2],sig_CB_n[5,0,10])")
		# ws.factory("RooGaussian::sig_Gauss(mass,sig_mu,sig_Gauss_sigma[0.1,0,0.2])")
		# getattr(ws,'import')( ROOT.RooRealVar("frac_CB","CB Fraction", 1., 0.9, 1.) )
		# sig_model=ROOT.RooAddPdf("sig_model","signal model",
		#                           ws.pdf("sig_CB"), ws.pdf("sig_Gauss"),
		#                           ws.var("frac_CB") )
		ws.factory("RooGaussian::sig_Gauss1(mass,sig_mu[3.1,3.05,3.15],sig_Gauss1_sigma[0.03,0.01,0.05])")
		ws.factory("RooGaussian::sig_Gauss2(mass,sig_mu,               sig_Gauss2_sigma[0.1,0.04,0.2])")
		getattr(ws,'import')( ROOT.RooRealVar("frac_Gauss1","Gauss1 Fraction", 1., 0.8, 1.) )
		sig_model=ROOT.RooAddPdf("sig_model","signal model",
										  ws.pdf("sig_Gauss1"), ws.pdf("sig_Gauss2"),
										  ws.var("frac_Gauss1") )
		getattr(ws,'import')( sig_model )

		ws.factory("RooExponential::bkg_model(mass,bkg_lambda[-1,-2,0])")

	## D*- ##############
	elif '-413' in str(CandTypes):
		getattr(ws,'import')( ROOT.RooRealVar("sig_mu","Signal gaussian mean", 0.1456, 0.1450, 0.1460) )
		getattr(ws,'import')( ROOT.RooRealVar("sig_Gauss1_sigma","Signal gaussian1 sigma", 0.001, 0.0005, 0.0015) )
		getattr(ws,'import')( ROOT.RooRealVar("sig_Gauss2_sigma","Signal gaussian2 sigma", 0.0015, 0.001,  0.002 ) )
		ws.factory("RooGaussian::sig_Gauss1(mass,sig_mu,sig_Gauss1_sigma)")
		ws.factory("RooGaussian::sig_Gauss2(mass,sig_mu,sig_Gauss2_sigma)")
		getattr(ws,'import')( ROOT.RooRealVar("frac_Gauss1","Gauss1 Fraction", 0.9, 0.3, 1.) )
		sig_model=ROOT.RooAddPdf("sig_model","signal model",
										  ws.pdf("sig_Gauss1"), ws.pdf("sig_Gauss2"),
										  ws.var("frac_Gauss1") )
		getattr(ws,'import')( sig_model )
		ws.factory("RooDstD0BG::bkg_model(mass,0.139, bgparC[0.03,0.002,0.05],"
			                                         "bgparA[-10.,-0.5,-50.],"
			                                         "bgparB[2,1,5])")

	#an expected pdf of signal+background
	model=ROOT.RooAddPdf("model","signal+background model",
								ROOT.RooArgList( ws.pdf("sig_model"), ws.pdf("bkg_model") ),
								ROOT.RooArgList( ws.var("nsig"),      ws.var("nbkg") )
								)
	getattr(ws,'import')(model)

	#do the fit
	doTheMassFit(ws=ws,data=ws.data('data'),
					CandTypes=CandTypes,
					showResult=True,
					outD=outputDir,
					postfixForOutputs=postfixForOutputs)

	#fix all parameters except the yields in the model
	allVars=ws.allVars()
	varIter = allVars.createIterator()
	var=varIter.Next()
	while var :
		varName=var.GetName()
		if varName.find('sig_')==0 or varName.find('bkg_')==0 :
			ws.var(varName).setConstant()
			print varName,
		var=varIter.Next()
	print ' were set constant after fitting'

	#save workspace
	wsUrl=os.path.join(outputDir,"CharmInfo_workspace%s.root"%postfixForOutputs)
	ws.writeToFile(wsUrl)

	#all done here
	return wsUrl


"""
"""
def runDifferentialMeasurement(ws,vname,ranges,outF):
	outdir = os.path.dirname(outF.GetName())
	# unfix all parameters except the yields in the model
	allVars = ws.allVars()
	varIter = allVars.createIterator()
	var = varIter.Next()
	while var:
		varName=var.GetName()
		if varName.find('sig_')==0 or varName.find('bkg_')==0 :
			ws.var(varName).setConstant(False)
			print varName,
		var = varIter.Next()
	print 'were unfrozen for fitting the differential cross sections'

	dsigma = {"S"      : ROOT.TGraphAsymmErrors(),
	          "SoverB" : ROOT.TGraphAsymmErrors(),
	          "mass"   : ROOT.TGraphAsymmErrors(),
	          "width"  : ROOT.TGraphAsymmErrors() }
	for x in dsigma: dsigma[x].SetName('%s_d%s'%(vname,x))


	for ir in xrange(0,len(ranges)-1):
		vmin=ranges[ir]
		vmax=ranges[ir+1]
		cut='(%s>=%4.2f&&%s<%4.2f)'%(vname,vmin,vname,vmax)
		print cut
		redData = ws.data("data").reduce(cut)
		if redData.numEntries < 10 : continue

		avgVar   = redData.mean( ws.var( vname ) )
		sigmaVar = redData.sigma(ws.var( vname ) )

		#ws.var('sig_sigma').setRange(0.001,0.02)

		doTheMassFit(ws=ws,data=redData,
						 showResult=True,
						 outD=outdir,
						 postfixForOutputs='%s_%3.1f_%3.1f'%(vname,vmin,vmax))
		nsig     = ws.var("nsig").getVal()
		nsigErr  = ws.var("nsig").getError()
		nbkg     = ws.var("nbkg").getVal()
		nbkgErr  = ws.var("nbkg").getError()
		mass     = ws.var("sig_mu").getVal()
		massErr  = ws.var("sig_mu").getError()
		try:
			width    = ws.var("sig_sigma").getVal()
			widthErr = ws.var("sig_sigma").getError()
		except:
			width    = ws.var("sig_Gauss1_sigma").getVal()
			widthErr = ws.var("sig_Gauss1_sigma").getError()

		np=dsigma["S"].GetN()
		binWidth=vmax-vmin
		binErrLo=avgVar-vmin
		binErrHi=vmax-avgVar
		dsigma["S"].SetPoint(np,avgVar,nsig/binWidth)
		dsigma["S"].SetPointError(np,binErrLo,binErrHi,nsigErr/binWidth,nsigErr/binWidth)

		if nbkg>0:
			soverb=(nsig/nbkg)
			soverb_err=(ROOT.TMath.Sqrt(ROOT.TMath.Power(nsigErr*nbkg,2)+ROOT.TMath.Power(nsig*nbkgErr,2))/ROOT.TMath.Power(nbkg,2))
			dsigma["SoverB"].SetPoint(np,avgVar,soverb)
			dsigma["SoverB"].SetPointError(np,binErrLo,binErrHi,soverb_err,soverb_err)

		dsigma["mass"].SetPoint(np,avgVar,mass)
		dsigma["mass"].SetPointError(np,binErrLo,binErrHi,massErr,massErr)
		dsigma["width"].SetPoint(np,avgVar,width)
		dsigma["width"].SetPointError(np,binErrLo,binErrHi,widthErr,widthErr)

	#differential measurements canvas
	cdiff=ROOT.TCanvas("cdiff","cdiff",500,500)
	for ds in dsigma:
		cdiff.cd()
		cdiff.Clear()
		ytitle="1/#sigma d#sigma/d%s"%vname
		if ds=="SoverB" : ytitle="S/B"
		if ds=="mass" : ytitle="M"
		if ds=="sigma" : ytitle="#sigma"
		xtitle = "Transverse momentum [GeV]"
		if vname=="eta": xtitle="Pseudo-rapidity"
		dsigma[ds].Draw("ap")
		dsigma[ds].SetMarkerStyle(20)
		dsigma[ds].GetXaxis().SetTitle( xtitle )
		dsigma[ds].GetYaxis().SetTitle( ytitle )
	        for ext in ['.pdf', '.png', '.C']:
		#for ext in ['.pdf']:
			cdiff.SaveAs(os.path.join(outdir,'diff_%s_%s%s'%(vname,ds,ext)))

		# write to file
		outF.cd()
		dsigma[ds].Write()
		if ds=='S' : normalizeDistribution(dsigma[ds]).Write()


"""
steer the script
"""
def main():

	#global ROOT configuration
	ROOT.gStyle.SetOptStat(0)
	ROOT.gStyle.SetOptTitle(0)
	ROOT.gStyle.SetOptFit(0)

	ROOT.gSystem.Load("libUserCodeTopMassSecVtx")
	ROOT.AutoLibraryLoader.enable()
	ROOT.shushRooFit()
	# see TError.h - gamma function prints lots of errors when scanning
	ROOT.gROOT.ProcessLine("gErrorIgnoreLevel=kFatal")
	ROOT.RooMsgService.instance().setSilentMode(True)

	ROOT.gStyle.SetPadTopMargin(0.05)
	ROOT.gStyle.SetPadBottomMargin(0.1)
	ROOT.gStyle.SetPadLeftMargin(0.15)
	ROOT.gStyle.SetPadRightMargin(0.05)

	ROOT.gROOT.SetBatch(True)

	#configuration
	usage = 'usage: %prog [options]'
	parser = optparse.OptionParser(usage)
	parser.add_option('-c', '--cands', dest='CandTypes',
							 help='csv list of candidates',
							 default='421',
							 type='string')
	parser.add_option('-i', '--input', dest='inputUrl' ,
							 help='csv list of files',
							 default=None,
							 type='string')
	parser.add_option('-w', '--ws', dest='wsUrl',
							 help='ws url',
							 default=None,
							 type='string')
	parser.add_option('-o', '--output', dest='output',
							 help='Where to put the output',
							 default=None,
							 type='string')
	parser.add_option('--weight', dest='weight',
							 help='Apply a weight',
							 default=None,
							 type='string')
	(opt, args) = parser.parse_args()

	###########################################
	# Differential xsec measurement: pT, eta
	if opt.wsUrl:
		if not opt.output:
			opt.output = os.path.join(
			                os.path.dirname(opt.wsUrl).strip('.root'),'diff')
		if not os.path.exists(opt.output):
			os.system('mkdir -p %s' % opt.output)

		print "Will store output in", opt.output
		wsF = openTFile(opt.wsUrl)
		if wsF == None:
			print "ERROR: workspace file not found %s"%opt.wsUrl
			return -1
		ws = wsF.Get("w")
		print "Read Workspace from  %s"%opt.wsUrl
		wsF.Close()

		outUrl=os.path.join(opt.output,
		            os.path.basename(opt.wsUrl).replace('workspace','diff'))
		outF = ROOT.TFile(outUrl,'RECREATE')
		varRanges = { "pt"  : [10,25,50,75],
					  "eta" : [0,0.9,1.5,2.5] }
		for vname,ranges in varRanges.iteritems():
			runDifferentialMeasurement(ws,vname,ranges,outF)
		outF.Close()

	###########################################
	# Create workspace and run sPlot
	else:
		if not opt.output:
			opt.output = os.path.join('unfolded',os.path.basename(
			                          opt.inputUrl).strip('.root'))
		else:
			opt.output = os.path.join(opt.output,os.path.basename(
			                          opt.inputUrl).strip('.root'))
		if opt.weight:
			wname = {
				'BFragWeight[0]': 'bfrag',
				'BFragWeight[1]': 'bfragup',
				'BFragWeight[2]': 'bfragdn',
				'BFragWeight[3]': 'bfragp11',
				'BFragWeight[4]': 'bfragpete',
				'BFragWeight[5]': 'bfraglund',
			}.get(opt.weight, opt.weight.replace('[','').replace(']',''))
			opt.output = '%s_%s'%(opt.output,wname)

		if not opt.output.endswith('/'): opt.output += '/'
		if not os.path.exists(opt.output):
			os.system('mkdir -p %s' % opt.output)

		print "Will store all output in", opt.output

		#turn csvs to arrays
		CandTypes = None
		if len(opt.CandTypes)>0:
			CandTypes=[int(val) for val in opt.CandTypes.split(',')]
		postfixForOutputs=''
		for c in CandTypes: postfixForOutputs +='_%d'%c

		inputUrl = None
		if not (opt.inputUrl is None):
			if len(opt.inputUrl)>0:
				inputUrl=opt.inputUrl.split(',')

		# Create the workspace
		wsUrl=generateWorkspace(CandTypes=CandTypes,
		                        inputUrl=inputUrl,
		                        postfixForOutputs=postfixForOutputs,
		                        options=opt)
		print "Retrieving workspace from ",wsUrl
		wsF = ROOT.TFile.Open(wsUrl)
		ws = wsF.Get("w")
		wsF.Close()

		#use the SPlot class to add SWeights to our data set
		sData = ROOT.RooStats.SPlot("sData","An SPlot from mass",
		                             ws.data('data'),ws.pdf('model'),
		                             ROOT.RooArgList(ws.var('nsig'),ws.var('nbkg'))
		)
		getattr(ws,'import')(ws.data('data'), ROOT.RooFit.Rename("dataWithSWeights"))
		data = ws.data("dataWithSWeights")

		#the weighted data for signal and background species
		sigData = ROOT.RooDataSet(data.GetName(),data.GetTitle(),data,data.get(),'','nsig_sw')
		bkgData = ROOT.RooDataSet(data.GetName(),data.GetTitle(),data,data.get(),'','nbkg_sw')

		#show the unfolded distributions and save them to a file
		outFurl = os.path.join(opt.output,'UnfoldedDistributions%s.root'%postfixForOutputs)
		outF = ROOT.TFile.Open(outFurl,'RECREATE')
		varsToUnfold = [
			['ptrel',    'p_{T,rel} [GeV]',           8],
			['pfrac',    'p / p^{Jet} [GeV]',         8],
			['ptfrac',   'p_{T} / p_{T}^{jet}',       8],
			['pzfrac',   'p_{z} / p_{z}^{jet}',       8],
			['ptchfrac', 'p_{T} / #Sigma_{ch} p_{T}', 8],
			['pzchfrac', 'p_{z} / #Sigma_{ch} p_{z}', 8],
			['dr',       '#DeltaR to jet',            8]
		]
		for var,varTitle,nBins in varsToUnfold:
			ws.var(var).SetTitle(varTitle)
			ws.var(var).setBins(nBins)
			showUnfolded(sigData=sigData,
			             bkgData=bkgData,
			             var=ws.var(var),
			             outD=opt.output,
			             outF=outF,
			             postfixForOutputs=postfixForOutputs)
		outF.Close()
		print 'Unfolded distributions can be found @ ',outFurl

"""
for execution from another script
"""
if __name__ == "__main__":
	 sys.exit(main())



