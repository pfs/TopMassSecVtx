#!/usr/bin/env python
import ROOT, os, sys
from ROOT import TFile, TCanvas, THStack, TLegend, TH1D, TGraph, TGraphErrors, TF1, TGaxis, TPad, TH2D

## Run by calling in the shell:
## ./macroTemplate.py

# Open a file
path = "/afs/cern.ch/work/j/jklocans/private/CMSSW_5_3_15/src/UserCode/llvv_fwk/lxyplots/"

################

ts_deltar_correct = []
ts_deltar_wrong = []

# Make a new TCanvas
c = TCanvas("canvas", "c", 1000, 1000)

# save all names of desired files in a list

listoffiles = [[] for x in xrange(0,6)]

for file in os.listdir( path ):
	if(file.endswith(".root") and file.startswith("MC8TeV_TTJets_MSDecays_166v5")):
		listoffiles[0].insert(0,file)
	elif (file.endswith(".root") and file.startswith("MC8TeV_TTJets_MSDecays_169v5")):
		listoffiles[1].insert(0,file)
	elif(file.endswith(".root") and file.startswith("MC8TeV_TTJets_MSDecays_172v5")):
		listoffiles[2].insert(0,file)
	elif(file.endswith(".root") and file.startswith("MC8TeV_TTJets_MSDecays_173v5")):       
		listoffiles[3].insert(0,file)
	elif(file.endswith(".root") and file.startswith("MC8TeV_TTJets_MSDecays_175v5")):
		listoffiles[4].insert(0,file)
	elif(file.endswith(".root") and file.startswith("MC8TeV_TTJets_178v5")):
		listoffiles[5].insert(0,file)

listofnames = []
listofnames.append("166v5")
listofnames.append("169v5")
listofnames.append("172v5")
listofnames.append("173v5")
listofnames.append("175v5")
listofnames.append("178v5")

for x in listofnames:

	ts_deltar_correct.append(TH1D("secl_emu_deltar_correct_" + x,"deltar between lepton and secv" + x, 50, 0., 150.))
	ts_deltar_wrong.append(TH1D("secl_emu_deltar_wrong_" + x,"deltar between lepton and secv" + x, 50, 0., 150.))

# Open the files -> adds all samples together
for i in range(0,6):
	ts_deltar_correct[i].Sumw2()
	ts_deltar_wrong[i].Sumw2()
	rootfile1 = []

	for x in listoffiles[i]:
	#inv.m. l + sv
		rootfile1.append(TFile.Open("./../lxyplots/" + x, "READ"))

	histo_deltar_correct = []
	histo_deltar_wrong = []

	for x in range(0,len(listoffiles[i])):

		histo_deltar_correct.append(rootfile1[x].Get("mlsv_emu_deltar_cut_correct"))
		histo_deltar_wrong.append(rootfile1[x].Get("mlsv_emu_deltar_cut_wrong"))


		histo_deltar_correct[x].Sumw2()
		histo_deltar_wrong[x].Sumw2()


		#adding histos

		ts_deltar_correct[i].Add(histo_deltar_correct[x])
		ts_deltar_wrong[i].Add(histo_deltar_wrong[x])


	#normalization
#		ts_pratio_2ntr[i].Scale(1/ts_pratio_2ntr[i].Integral())

	# Set colors and stuff

	ts_deltar_wrong[i].SetLineColor(2)
	
	del histo_deltar_correct
	del histo_deltar_wrong

	del rootfile1

for i in range(0,6):

	c.cd()
	ts_deltar_correct[i].Draw("HIST")
	ts_deltar_wrong[i].Draw("HIST:same")


	c.SaveAs("./../plots/secl_emu_deltar_cut" + listofnames[i] + ".pdf")

ts_deltar_correct_allmases = TH1D("secl_emu_deltar_correct_allmases","deltar between lepton and secv all masses incl.", 50, 0., 150.)
ts_deltar_correct_allmases.Sumw2()
ts_deltar_wrong_allmases = TH1D("secl_emu_deltar_wrong_allmases","deltar between lepton and secv all masses incl.", 50, 0., 150.)
ts_deltar_wrong_allmases.Sumw2()

for i in range(0,6):
	ts_deltar_correct_allmases.Add(ts_deltar_correct[i])
	ts_deltar_wrong_allmases.Add(ts_deltar_wrong[i])

c.cd()
ts_deltar_wrong_allmases.SetLineColor(2)

ts_deltar_correct_allmases.Draw("HIST")
ts_deltar_wrong_allmases.Draw("HIST:same")

print "correct charge events/total events = " 
print ts_deltar_correct_allmases.Integral()/(ts_deltar_wrong_allmases.Integral()+ts_deltar_correct_allmases.Integral())

c.SaveAs("./../plots/secl_emu_deltar_cut.pdf")

