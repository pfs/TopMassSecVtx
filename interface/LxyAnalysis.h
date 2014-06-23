#ifndef _lxyanalysis_
#define _lxyanalysis_

#include "UserCode/llvv_fwk/interface/SmartSelectionMonitor.h"
#include "UserCode/llvv_fwk/interface/DataEventSummaryHandler.h"

struct BeautyEvent_t
{
	Int_t run, lumi, event, evcat, nvtx;
	Float_t rho;
	// Weights
	Int_t nw;
	Float_t w[50];
	// Leptons / GenLeptons
	Int_t nl,lid[50],glid[50];
	Float_t lpt[50],leta[50],lphi[50];
	Float_t glpt[50],gleta[50],glphi[50];
	// Jets
	Int_t nj,jflav[50];
	Float_t jpt[50],jeta[50],jphi[50],jcsv[50],jarea[50],jtoraw[50];
	// Sec.Vertices
	Float_t svpt[2],sveta[2],svphi[2],svmass[2],svntk[2],svlxy[2],svlxyerr[2];
	// Gen Bhadrons
	Int_t bid[2],bhadid[2];
	Float_t bpt[2],beta[2],bphi[2];
	Float_t bhadpt[2],bhadeta[2],bhadphi[2],bhadmass[2],bhadlxy[2];
	// Gen Top
	Int_t tid[2];
	Float_t tpt[2],teta[2],tphi[2],tmass[2];
	// PF Candidates
	Int_t npf,npfb1,pfid[200];
	Float_t pfpt[200],pfeta[200],pfphi[200];
	// MET
	Float_t metpt,metphi;
};

class LxyAnalysis
{

public:
	LxyAnalysis();

	void attachToDir(TDirectory *outDir);
	inline void setTruthMode(int mode){mcTruthMode = mode;}

	bool analyze(Int_t run, Int_t event, Int_t lumi,
				 Int_t nvtx, Float_t rho,
				 std::vector<Float_t> weights,
				 Int_t evCat,
				 std::vector<data::PhysicsObject_t *> &leptons,
				 std::vector<data::PhysicsObject_t *> &jets,
				 LorentzVector &met,
				 data::PhysicsObjectCollection_t &pf,
				 data::PhysicsObjectCollection_t &mctruth);

private:

	void resetBeautyEvent();

	TTree *outT_;
	BeautyEvent_t bev_;
	TDirectory *outDir_;

	int mcTruthMode;

};

#endif
