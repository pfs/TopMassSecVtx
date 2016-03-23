#! /usr/bin/env python
import ROOT
import utils
from array import array
import optparse
import numpy as np
import os,sys
from UserCode.TopMassSecVtx.storeTools_cff import fillFromStore
from UserCode.TopMassSecVtx.KinematicsMoments import KinematicsMoments
from makeSVLMassHistos import getMassTrees
import re

"""
Loop over a tree and fill histograms you declared before
If q is True, you get the quantiles from your histograms returned in an array, q_gen or q_rec depending on your histogram
It could also work to return the quantiles from just one of the histograms - see commented lines
"""
def runRecoAnalysis(fileName,outFileName,mode):
    
    isData = True if 'Data' in outFileName else False
    print '...analysing ',fileName,' file names isData=',isData,' output in',outFileName

    observables_rec={'ptpos':0,'enpos':0,'ptll':0,'mll':0,'EposEm':0,'ptposptm':0}
    observables_gen={'ptpos':0,'enpos':0,'ptll':0,'mll':0,'EposEm':0,'ptposptm':0}
    obsMoments_rec,obsMoments_gen={},{}

    #create list of systematic variations
    systVars=['nominal']

    #include other uncertainties for signal only
    pdfIdx={}
    if 'MC8TeV_TTJets_MSDecays_172v5' in fileName:
        
        systVars += ['puup','pudn',
                     'lepselup','lepseldn', 'lesup','lesdn',
                     'toppt',
                     'jesup', 'jesdn',  'jerup',    'jerdn',
                     'btagup','btagdn', 'mistagup', 'mistagdn']

        for idx in xrange(0,52) : 
            key='pdf%d'%idx
            systVars.append(key)
            pdfIdx[key]=idx

    for var in systVars:
        if isData and var != 'nominal': continue
        obsMoments_rec[var]=KinematicsMoments(observables=observables_rec,name=var,       maxMoment=3)
        obsMoments_gen[var]=KinematicsMoments(observables=observables_gen,name=var+'_gen',maxMoment=3)

    jetMultH=ROOT.TH1F("njets",   ";Jet multiplicity; Events",4,0,4)
    jetMultH.SetDirectory(0)
    jetMultH.Sumw2()
    observablesH={'ptpos':    ROOT.TH1F('ptpos',';Lepton transverse momentum [GeV];Events',100,0,200),
                  'enpos':    ROOT.TH1F('enpos',';Lepton energy [GeV];Events',100,0,200),
                  'ptll':     ROOT.TH1F('ptll',';Dilepton transverse momentum [GeV];Events',100,0,200),
                  'mll':      ROOT.TH1F('mll',';Invariant mass [GeV];Events',100,0,400),
                  'EposEm':   ROOT.TH1F('EposEm',';Energy sum [GeV];Events',100,40,500),
                  'ptposptm': ROOT.TH1F('ptposptm',';Transverse momentum sum [GeV];Events',100,40,300)}
    for var in observablesH:
        observablesH[var].SetDirectory(0)
        observablesH[var].Sumw2()


    #open file
    tree=ROOT.TChain('DileptonInfo')
    tree.AddFile(fileName)
    
    #loop over events in the tree and fill histos
    totalEntries=tree.GetEntries()
    for i in xrange(0,totalEntries):

        tree.GetEntry(i)

        if i%100==0 : sys.stdout.write('\r [ %d/100 ] done' %(int(float(100.*i)/float(totalEntries))) )

        #select only emu events
        if tree.EvCat != -11*13 : continue
        if not isData: 
           if tree.GenLpPt == 0 or tree.GenLmPt == 0: continue        
        
        #central leptons
        if mode==4:
            if ROOT.TMath.Abs(tree.LpEta)<2.1 : continue
        if mode==5:
            if ROOT.TMath.Abs(tree.LpEta)<2.1 : continue
            if ROOT.TMath.Abs(tree.LmEta)<2.1 : continue

        #up to 2 jets all b-tagged
        if mode==2:
            if tree.NJets>2 : continue
            if tree.NJets!=tree.NbJets : continue

        #=2jets,=2-btags
        if mode==3:
            if tree.NJets!=2 : continue
            if tree.NbJets!=2: continue

        for var in systVars:
            if isData and var!='nominal' : continue

            #base weight: BR fix for ttbar x pileup x lepton selection x xsec weight
            weight = 1.0
            if not isData:
                if var=='nominal'   : 
                    weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[0]
                elif var=='puup'    : weight = tree.Weight[0]*tree.Weight[2]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[0]
                elif var=='pudn'    : weight = tree.Weight[0]*tree.Weight[3]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[0]
                elif var=='lepselup': weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[5]*tree.BtagWeight[0]*tree.JESWeight[0]
                elif var=='lepseldn': weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[6]*tree.BtagWeight[0]*tree.JESWeight[0]
                elif var=='jesup'   : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[1]
                elif var=='jesdn'   : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[2]
                elif var=='jerup'   : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[3]
                elif var=='jerdn'   : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[4]
                elif var=='btagup'  : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[1]*tree.JESWeight[0]
                elif var=='btagdn'  : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[2]*tree.JESWeight[0]
                elif var=='mistagup': weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[3]*tree.JESWeight[0]
                elif var=='mistagdn': weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[4]*tree.JESWeight[0]
                elif var=='toppt'   : weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[0]*tree.Weight[10]
                elif 'pdf' in var :   
                    weight = tree.Weight[0]*tree.Weight[1]*tree.Weight[4]*tree.BtagWeight[0]*tree.JESWeight[0]*tree.PDFWeights[ pdfIdx[var] ]
                
            #positive lepton
            lp=ROOT.TLorentzVector()
            lp.SetPtEtaPhiM(tree.LpPt,tree.LpEta,tree.LpPhi,0.)
            if var=='lesup' : lp*=(1+tree.LpScale)
            if var=='lesdn' : lp*=(1-tree.LpScale)
            glp=ROOT.TLorentzVector()
            glp.SetPtEtaPhiM(tree.GenLpPt,tree.GenLpEta,tree.GenLpPhi,0.)

            #negative lepton
            lm=ROOT.TLorentzVector()
            lm.SetPtEtaPhiM(tree.LmPt,tree.LmEta,tree.LmPhi,0.)       
            if var=='lesup' : lm*=(1+tree.LmScale)
            if var=='lesdn' : lm*=(1-tree.LmScale)
            glm=ROOT.TLorentzVector()
            glm.SetPtEtaPhiM(tree.GenLmPt,tree.GenLmEta,tree.GenLmPhi,0.)
            
            #charged lepton pair - pt
            ll=ROOT.TLorentzVector()
            ll = lp + lm
            gll=ROOT.TLorentzVector()
            gll = glp + glm

            observables_rec['ptpos']=lp.Pt() 
            observables_rec['enpos']=lp.E()
            observables_rec['ptll']=ll.Pt()
            observables_rec['mll']=ll.M()
            observables_rec['EposEm']=lp.E()+lm.E()
            observables_rec['ptposptm']=lp.Pt()+lm.Pt()

            #apply fiducial cuts
            if mode>0:
                if ( observables_rec['ptpos']>115    or observables_rec['ptpos']<25 )   : observables_rec['ptpos']=None
                if ( observables_rec['enpos']>185    or observables_rec['enpos']<25 )   : observables_rec['enpos']=None
                if ( observables_rec['ptll']>125     or observables_rec['ptll']<10)     : observables_rec['ptll']=None
                if ( observables_rec['mll']>205      or observables_rec['mll']<25)      : observables_rec['mll']=None
                if ( observables_rec['EposEm']>270   or observables_rec['EposEm']<70)   : observables_rec['EposEm']=None
                if ( observables_rec['ptposptm']>195 or observables_rec['ptposptm']<50) : observables_rec['ptposptm']=None

            obsMoments_rec[var].measure(observables_rec,weight)
            if var=='nominal':
                jetMultH.Fill(tree.NJets,weight)
                for obsName in observables_rec:
                    if observables_rec[obsName] is None : continue
                    observablesH[obsName].Fill(observables_rec[obsName],weight)

            observables_gen['ptpos']    = glp.Pt()          if observables_rec['ptpos'] else None
            observables_gen['enpos']    = glp.E()           if observables_rec['enpos'] else None
            observables_gen['ptll']     = gll.Pt()          if observables_rec['ptll'] else None
            observables_gen['mll']      = gll.M()           if observables_rec['mll'] else None
            observables_gen['EposEm']   = glp.E()+glm.E()   if observables_rec['EposEm'] else None
            observables_gen['ptposptm'] = glp.Pt()+glm.Pt() if observables_rec['ptposptm'] else None
            obsMoments_gen[var].measure(observables_gen,weight)

    #save results
    fOut=ROOT.TFile.Open(outFileName,'RECREATE')
    jetMultH.Write()
    for var in observablesH: observablesH[var].Write()
    for var in obsMoments_rec:
        obsMoments_rec[var].save(fOut)
        obsMoments_gen[var].save(fOut)
    fOut.Close()

 
"""
Wrapper for when the analysis is run in parallel
Also creates histograms, get quantiles from just one file and re run histograms
"""
def runRecoAnalysisPacked(args):
    try:
        fileNames,outFileName,mode=args
        runRecoAnalysis(fileNames,outFileName,mode)
    except : # ReferenceError:
        print 50*'<'
        print "  Problem with", name, "continuing without"
        print 50*'<'
        return False
    
"""
Create summary distributions to unfold
"""
def createRecoAnalysisTasks(opt):

    onlyList=opt.only.split('v')

    #########################
    ## Multiple files
    ## First collect all the files
    file_list = []

    ## Local directory
    if os.path.isdir(opt.input):
        for file_path in os.listdir(opt.input):
            if file_path.endswith('.root'):
                file_list.append(os.path.join(opt.input,file_path))

    ## Directory on eos
    elif opt.input.startswith('/store/'):
        file_list = getEOSlslist(opt.input)

    #list of files to analyse
    tasklist=[]
    for filename in file_list:
        baseFileName=os.path.basename(filename)      
        tag,ext=os.path.splitext(baseFileName)
        splitNb=re.search(r'\d+$',tag)
        if splitNb:
            postfix='_'+splitNb.group()
            tag=tag[:-len(postfix)]
        if len(onlyList)>0:
            processThis=False
            for filtTag in onlyList:
                if filtTag in tag:
                    processThis=True
            if not processThis : continue
        tasklist.append((filename,'%s/%s'%(opt.output,baseFileName),opt.mode))

    #loop over tasks
    if opt.jobs>1:
        print ' Submitting jobs in %d threads' % opt.jobs
        import multiprocessing as MP
        pool = MP.Pool(opt.jobs)
        pool.map(runRecoAnalysisPacked,tasklist)
    else:
        for fileNames,outFileName,mode in tasklist:
            runRecoAnalysis(fileNames,outFileName,mode)

"""
steer
"""
def main():
	usage = 'usage: %prog [options]'
	parser = optparse.OptionParser(usage)
	parser.add_option('-i', '--input',
                          dest='input',   
                          default='/afs/cern.ch/user/p/psilva/public/Dileptons2012',
                          help='input directory with the files [default: %default]')
	parser.add_option('--jobs',
                          dest='jobs', 
                          default=1,
                          type=int,
                          help='# of jobs to process in parallel the trees [default: %default]')
	parser.add_option('--only',
                          dest='only', 
                          default='',
                          type='string',
                          help='csv list of tags to process')
	parser.add_option('-o', '--output',
                          dest='output', 
                          default='dileptonMoments',
                          help='Output directory [default: %default]')
	parser.add_option('-m', '--mode',
                          dest='mode', 
                          default=0,
                          type=int,
                          help='Mode: 0-no cuts 1-fid.cuts 2-up to two jets all b-tagged 3-2jets2b-tags [default: %default]')
	(opt, args) = parser.parse_args()

        ROOT.gSystem.Load("libUserCodeTopMassSecVtx")
	ROOT.AutoLibraryLoader.enable()
	os.system('mkdir -p %s' % opt.output)

        createRecoAnalysisTasks(opt)
        

if __name__ == "__main__":
	sys.exit(main())
