#!/usr/bin/env python
'''
File: DrawHistogram.py
Author: Alejandro Gomez Espinosa
Email: gomez@physics.rutgers.edu
Description: My Draw histograms. Check for options at the end.
'''

#from ROOT import TFile, TH1F, THStack, TCanvas, TMath, gROOT, gPad
from ROOT import *
import time, os, math, sys
from array import array
import argparse
from collections import OrderedDict
from DrawHistogram import Rebin2D
try:
	from RUNA.RUNAnalysis.histoLabels import labels, labelAxis, finalLabels, setSelection
	from RUNA.RUNAnalysis.scaleFactors import * #scaleFactor as SF
	from RUNA.RUNAnalysis.commonFunctions import * 
	from RUNA.RUNAnalysis.cuts import selection 
	import RUNA.RUNAnalysis.CMS_lumi as CMS_lumi 
	import RUNA.RUNAnalysis.tdrstyle as tdrstyle
except ImportError:
	sys.path.append('../python')
	from histoLabels import labels, labelAxis, finalLabels
	from scaleFactors import * #scaleFactor as SF
	from commonFunctions import * 
	from cuts import selection 
	import CMS_lumi as CMS_lumi 
	import tdrstyle as tdrstyle

gROOT.Reset()
gROOT.SetBatch()
gROOT.ForceStyle()
tdrstyle.setTDRStyle()
gStyle.SetOptStat(0)

xline = array('d', [0,2000])
yline = array('d', [1, 1])
line = TGraph(2, xline, yline)
line.SetLineColor(kRed)

yline11 = array('d', [1.1, 1.1])
line11 = TGraph(2, xline, yline11)
line11.SetLineColor(kGreen)

yline09 = array('d', [0.9, 0.9])
line09 = TGraph(2, xline, yline09)
line09.SetLineColor(kGreen)

yline0 = array('d', [0,0])
line0 = TGraph(2, xline, yline0)
line0.SetLineColor(kRed)


def listOfCont( histo ):
 	"""docstring for listOfCont"""
	tmpListContent = []
	tmpListError = []
	for ibin in range( histo.GetNbinsX() ): 
		tmpListContent.append( histo.GetBinContent( ibin ) )
		tmpListError.append( histo.GetBinError( ibin ) )
	return tmpListContent, tmpListError

def BCDHisto( tmpHisto, BList, CList, DList ):
	"""docstring for BCDHisto"""

	#tmpHisto.Reset()
	for jbin in range( len( BList ) ):
		Nominal_Side = BList[ jbin ]
		Side_Side = CList[ jbin ]
		Side_Nominal = DList[ jbin ]
		if Side_Side != 0: 
			Bkg = Nominal_Side*Side_Nominal/Side_Side
			#BkgError = TMath.Sqrt( Bkg ) 
			try: BkgError = Bkg * TMath.Sqrt( TMath.Power(( TMath.Sqrt( Nominal_Side ) / Nominal_Side ), 2) + TMath.Power(( TMath.Sqrt( Side_Nominal ) / Side_Nominal ), 2) + TMath.Power(( TMath.Sqrt( Side_Side ) / Side_Side ), 2) )
			except ZeroDivisionError: BkgError = 0
		else: 
			Bkg = 0
			BkgError = 0
		tmpHisto.SetBinContent( jbin, Bkg )
		tmpHisto.SetBinError( jbin, BkgError )
	return tmpHisto

def addSysBand( histo, uncSys, colour ):
	"""docstring for addSysBand"""
	
	hclone = histo.Clone()
	hclone.Reset()
	for i in range( 0, histo.GetNbinsX()+1 ):
		cont = histo.GetBinContent( i )
		hclone.SetBinContent( i, cont )
		hclone.SetBinError( i, ((cont*uncSys) -cont) )
	hclone.SetFillStyle(3004)
	hclone.SetFillColor( colour )
	return hclone


def makePulls( histo1, histo2 ):
	"""docstring for makePulls"""

	histoPulls = histo1.Clone()
	histoPulls.Reset()
	pullsOnly = TH1F( 'pullsOnly', 'pullsOnly', 14, -3, 3 )
	for ibin in range(0, histo1.GetNbinsX() ):
		try: pull = ( histo1.GetBinContent( ibin ) - histo2.GetBinContent( ibin ) ) / histo1.GetBinError( ibin ) 
		except ZeroDivisionError: pull = 0
		histoPulls.SetBinContent( ibin, pull )
		histoPulls.SetBinError( ibin, 1 )
		pullsOnly.Fill( pull )

	return histoPulls, pullsOnly

def rebin( histo, binning ):
	"""docstring for rebin"""

	oldhisto = histo.Clone()
	if 'reso' in str(binning):  
		boostedMassAveBins = array( 'd', [ 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235, 240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 300, 310, 320, 330, 340, 350, 500, 510 ] )
		newhisto = oldhisto.Rebin( len( boostedMassAveBins )-1, oldhisto.GetName(), boostedMassAveBins )
	elif 'ratio' in str(binning): 
		boostedMassAveBins = array( 'd', [ 0, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400, 450, 500 ] )
		newhisto = oldhisto.Rebin( len( boostedMassAveBins )-1, oldhisto.GetName(), boostedMassAveBins )
	else:
		newhisto = oldhisto.Rebin( binning )

	return newhisto
	

def ratioPlots( histo1, histo2 ):
	"""docstring for ratioPlots"""

	chi2 = 0
	ndf = 0
	h1errFull = histo1.Clone()
	h1errFull.Reset()
	h1errh2 = histo1.Clone()
	h1errh2.Reset()
	ratioList = []
	binCenterList = []
	ratioLogNErrXPlusList = []
	ratioLogNErrXMinusList = []

	for ibin in range( 0, histo1.GetNbinsX() ):
		binCenterList.append( histo1.GetXaxis().GetBinCenter( ibin ) )
		x = histo1.GetBinContent( ibin )
		xErr = histo1.GetBinError( ibin )
		y = histo2.GetBinContent( ibin )
		yErr = histo2.GetBinError( ibin )
		try: 
			ratio = x/y
			ratioErrX = ratio * TMath.Sqrt( TMath.Power( xErr/x, 2) + TMath.Power( yErr/y, 2)  )
			ratioErrY = ratio* yErr / y
			ratioLogNErrXPlus = TMath.Sqrt( TMath.Power( ( (x/(y-yErr)) - ratio ), 2 )  + TMath.Power( ( ((x+xErr)/y) - ratio ) , 2) ) 
			ratioLogNErrXMinus = TMath.Sqrt( TMath.Power( ( (x/(y+yErr)) - ratio ), 2 )  + TMath.Power( ( ((x-xErr)/y) - ratio ) , 2) ) 
		except ZeroDivisionError: 
			ratio = 0
			ratioErrX = 0
			ratioErrY = 0
			ratioLogNErrXPlus = 0
			ratioLogNErrXMinus = 0
		#print x, xErr, y, yErr, ratio, ratioErrX, ratioLogNErrX, ratioErrY, ratioLogNErrY
		#print x, xErr, y, yErr, ratio, ratioLogNErrXPlus, ratioLogNErrXMinus
		h1errFull.SetBinContent( ibin, ratio )
		h1errFull.SetBinError( ibin, ratioErrX )
		h1errh2.SetBinContent( ibin, ratio )
		h1errh2.SetBinError( ibin, ratioErrY )
		ratioList.append( ratio )
		ratioLogNErrXPlusList.append( ratioLogNErrXPlus )
		ratioLogNErrXMinusList.append( ratioLogNErrXMinus )
		if ibin < 35 :
			if (y>0):
				try: chi2 += ((y-x)*(y-x))/( (yErr*yErr) + (xErr*xErr) )
				except ZeroDivisionError: chi2 += 0
				ndf += 1

	'''
	histoAsymErrors = histo1.Clone()
	histoAsymErrors.Reset()
	histoAsymErrors.Sumw2(False)
	for ibin in range( histoAsymErrors.GetNbinsX() ):
		histoAsymErrors.SetBinContent( ibin, ratioList[ibin] )
	histoAsymErrors.SetBinErrorOption(TH1.kPoisson)
	'''

	zeroArray = array( 'd', ( [ 0 ] * (len( ratioList )) ) )
	asymErrors = TGraphAsymmErrors( len(ratioList), array('d', binCenterList), array('d', ratioList), zeroArray, zeroArray, array('d',ratioLogNErrXMinusList), array('d', ratioLogNErrXPlusList) )

	return h1errFull, h1errh2, chi2, ndf-1, asymErrors

def alternativeABCD( nameInRoot, histoB, histoC, histoD, typePlot, plot=True ):
	"""docstring for alternativeABCD"""
	
	histoC = rebin( histoC, 50 ) 
	histoD = rebin( histoD, 50 ) 
	histoCD = histoC.Clone()
	histoCD.Reset()
	histoCD.Divide( histoC, histoD, 1., 1., '' )

	histoCD.GetYaxis().SetTitle( 'Ratio B/D' )
	histoCD.GetYaxis().SetTitleOffset(0.75)
	histoCD.GetXaxis().SetTitle( 'Average pruned mass [GeV]' )
	histoCD.SetStats( True)
	fitCD = TF1( 'fitCD', 'pol3', 50, 350 )
	'''
	fitLow = TF1( 'fitLow', 'pol2', 25, 100 )
	fitHigh = TF1( 'fitHigh', 'pol1', 100, 500 )
	fitCD = TF1( 'fitCD', 'pol2(0)+pol1(3)', 0, 300 )
	#fitCD = TF1( 'fitCD', '[0]+([1]*x)+([2]*(x-400)*(x-400))+([3]*x*x*x)', 20, 400 )
	histoCD.Fit( fitLow, 'R' ) 
	histoCD.Fit( fitHigh, 'R+' ) 
	fitCD.SetParameter( 0, fitLow.GetParameter( 0 ) )
	fitCD.SetParameter( 1, fitLow.GetParameter( 1 ) )
	fitCD.SetParameter( 2, fitLow.GetParameter( 2 ) )
	fitCD.SetParameter( 3, fitHigh.GetParameter( 0 ) )
	fitCD.SetParameter( 4, fitHigh.GetParameter( 1 ) )
	'''
	for i in range(3):  fitCDResult =  TFitResultPtr(histoCD.Fit( fitCD, 'MIRS' ) )
	
	listFitValues = []
	listFitErrors = []
	listBinCenter = []

	histoBCD = histoB.Clone()
	histoBCD.Reset()
	for ibin in range( 1, histoBCD.GetNbinsX() ):
		contB = histoB.GetBinContent( ibin )
		errorB = histoB.GetBinError( ibin )
		binCenter = histoB.GetBinCenter( ibin )
		factorCD = fitCD.Eval( binCenter )
		contBCD = contB * factorCD

		err = array( 'd', [0] )
		fitCDResult.GetConfidenceIntervals( 1, 1, 1, array('d',[binCenter]), err, 0.683, False ) 
		#print ibin, contB, errorB, binCenter, factorCD, contBCD, err[0]
		listFitValues.append( factorCD )
		listFitErrors.append( err[0] )
		listBinCenter.append( binCenter )

		try: errBCD = contBCD* TMath.Sqrt( TMath.Power( err[0]/factorCD, 2 ) + TMath.Power( errorB/contB, 2 ) )
		except ZeroDivisionError: errBCD = 1.8
		if contBCD == 0 : errBCD = 1.8

		histoBCD.SetBinContent( ibin, contBCD )
		histoBCD.SetBinError( ibin, errBCD )

	#tmpFile = TFile( 'test.root', 'recreate' )
	#histoCD.Write()
	#histoB.Write()
	#histoC.Write()
	#histoD.Write()
	#tmpFile.Close()

	if plot:
		canCD = TCanvas('canCD', 'canCD',  10, 10, 750, 500 )
		#if 'simple' in args.binning: tmpcanCD= canCD.DrawFrame(0,0,500,2)
		#else: tmpcanCD= canCD.DrawFrame(0,0,boostedMassAveBins[-1],2)
		gStyle.SetOptFit(1)
		histoCD.Draw("PES")
		fitCD.SetLineWidth(2)
		fitCD.SetLineColor(kBlue)
		fitCD.Draw("same")
		#fitLow.Draw("same")
		#fitHigh.Draw("same")

		fitCDUp = TGraph( len(listFitValues), array( 'd', listBinCenter ), np.add( listFitValues, listFitErrors ) ) 
		fitCDUp.SetLineColor(kRed)
		fitCDUp.Draw('same pc')
		fitCDDown = TGraph( len(listFitValues), array( 'd', listBinCenter ), np.subtract( listFitValues, listFitErrors ) ) 
		fitCDDown.Draw('same pc')
		fitCDDown.SetLineColor(kRed)
		canCD.Update()
		canCD.Modified()
		outputFileNameCD = nameInRoot+'_'+typePlot+'_CD_'+args.grooming+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
		canCD.SaveAs('Plots/'+outputFileNameCD)

	return histoBCD

def alternativeABCDCombined( nameInRoot, binning, hDataB, hDataC, hDataD, hBkgB, hBkgC, hBkgD, typePlot, plot=True, rootFile=False ):
	"""docstring for alternativeABCDcombined"""
	
	hDataC = rebin( hDataC, binning ) 
	hDataD = rebin( hDataD, binning ) 
	hDataCD = hDataC.Clone()
	hDataCD.Reset()
	hDataCD.Divide( hDataC, hDataD, 1., 1., '' )

	hBkgC = rebin( hBkgC, binning ) 
	hBkgD = rebin( hBkgD, binning ) 
	hBkgCD = hBkgC.Clone()
	hBkgCD.Reset()
	hBkgCD.Divide( hBkgC, hBkgD, 1., 1., '' )

	fitFunction = 'pol3'
	fitMin = 50
	fitMax = 350

	hBkgCD.GetYaxis().SetTitle( 'Ratio B/D' )
	hBkgCD.GetYaxis().SetTitleOffset(0.75)
	hBkgCD.GetXaxis().SetTitle( 'Average pruned mass [GeV]' )
	hBkgCD.SetStats( True)
	fitBkgCD = TF1( 'fitBkgCD', fitFunction, fitMin, fitMax )
	for i in range(3):  fitBkgCDResult =  TFitResultPtr(hBkgCD.Fit( fitBkgCD, 'MIRS' ) )

	hDataCD.GetYaxis().SetTitle( 'Ratio B/D' )
	hDataCD.GetYaxis().SetTitleOffset(0.75)
	hDataCD.GetXaxis().SetTitle( 'Average pruned mass [GeV]' )
	hDataCD.SetStats( True)
	fitCD = TF1( 'fitCD', fitFunction, fitMin, fitMax )
	for p in range(fitBkgCD.GetNpar() ): fitCD.SetParameter( p, fitBkgCD.GetParameter( p ) )
	fitCDResult =  TFitResultPtr(hDataCD.Fit( fitCD, 'MIRS' ) )
	
	listFitValues = []
	listFitErrors = []
	listBinCenter = []
	hDataBCD = hDataB.Clone()
	hDataBCD.Reset()
	hDataRatioCD = hDataB.Clone()
	hDataRatioCD.Reset()
	hBkgBCD = hBkgB.Clone()
	hBkgBCD.Reset()
	for ibin in range( 1, hDataBCD.GetNbinsX() ):
		contB = hDataB.GetBinContent( ibin )
		errorB = hDataB.GetBinError( ibin )
		binCenter = hDataB.GetBinCenter( ibin )
		factorCD = fitCD.Eval( binCenter )
		contBCD = contB * factorCD

		### error in fit
		err = array( 'd', [0] )
		fitCDResult.GetConfidenceIntervals( 1, 1, 1, array('d',[binCenter]), err, 0.683, False ) 
		#print ibin, contB, errorB, binCenter, factorCD, contBCD, err[0]
		listFitValues.append( factorCD )
		listFitErrors.append( err[0] )
		listBinCenter.append( binCenter )

		try: errBCD = contBCD* TMath.Sqrt( TMath.Power( err[0]/factorCD, 2 ) + TMath.Power( errorB/contB, 2 ) )
		except ZeroDivisionError: errBCD = 1.8
		if contBCD == 0 : errBCD = 1.8

		hDataBCD.SetBinContent( ibin, contBCD )
		hDataBCD.SetBinError( ibin, errBCD )
		hDataRatioCD.SetBinContent( ibin, factorCD )
		hDataRatioCD.SetBinError( ibin, err[0] )

		## same for bkg
		contBkgB = hBkgB.GetBinContent( ibin )
		errorBkgB = hBkgB.GetBinError( ibin )
		contBkgBCD = contBkgB * factorCD
		try: errBkgBCD = contBkgBCD* TMath.Sqrt( TMath.Power( err[0]/factorCD, 2 ) + TMath.Power( errorBkgB/contBkgB, 2 ) )
		except ZeroDivisionError: errBkgBCD = 1.8
		if contBkgBCD == 0 : errBkgBCD = 1.8
		hBkgBCD.SetBinContent( ibin, contBkgBCD )
		hBkgBCD.SetBinError( ibin, errBkgBCD )
	
	fitCDUp = TGraph( len(listFitValues), array( 'd', listBinCenter ), np.add( listFitValues, listFitErrors ) ) 
	fitCDDown = TGraph( len(listFitValues), array( 'd', listBinCenter ), np.subtract( listFitValues, listFitErrors ) ) 

	if rootFile:
		tmpFile = TFile('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_DATA_ABCDBkg_'+args.RANGE+'_'+args.version+'.root', 'recreate' )
		hDataBCD.SetName( 'massAve_prunedMassAsymVsdeltaEtaDijet_DATA_ABCDProj' )
		hDataBCD.Write()
		hDataRatioCD.SetName( 'massAve_prunedMassAsymVsdeltaEtaDijet_DATA_RatioBD' )
		hDataRatioCD.Write()
		hDataB.Write()
		tmpFile.Close()

	if plot:
		canCD = TCanvas('canCD', 'canCD',  10, 10, 750, 500 )
		#if 'simple' in args.binning: tmpcanCD= canCD.DrawFrame(0,0,500,2)
		#else: tmpcanCD= canCD.DrawFrame(0,0,boostedMassAveBins[-1],2)
		gStyle.SetOptFit(1)
		hBkgCD.SetLineColor(kBlue)
		hBkgCD.Draw()
		hDataCD.SetMarkerStyle(8)
		hDataCD.Draw("sames")
		fitBkgCD.SetLineWidth(1)
		fitBkgCD.SetLineColor(kBlue-2)
		fitBkgCD.Draw("same")

		fitCD.SetLineWidth(2)
		fitCD.SetLineColor(kRed)
		fitCD.Draw("same")
		fitCDUp.SetLineColor(kRed)
		fitCDUp.Draw('same pc')
		fitCDDown.Draw('same pc')
		fitCDDown.SetLineColor(kRed)
		CMS_lumi.extraText = "Preliminary"
		CMS_lumi.relPosX = 0.13
		CMS_lumi.CMS_lumi(canCD, 4, 0)

		legend=TLegend(0.65,0.15,0.90,0.35)
		legend.SetFillStyle(0)
		legend.SetTextSize(0.03)
		legend.AddEntry( hDataCD, 'Data', 'pl' )
		legend.AddEntry( hBkgCD, 'All MC Bkgs', 'pl' )
		legend.AddEntry( fitCD, 'Fit to data', 'l' )
		legend.AddEntry( fitCDUp, 'Fit unc. to data', 'l' )
		legend.AddEntry( fitBkgCD, 'Fit to MC', 'l' )
		legend.Draw("same")

		canCD.Update()
		st2 = hBkgCD.GetListOfFunctions().FindObject("stats")
		st2.SetX1NDC(.15)
		st2.SetX2NDC(.35)
		st2.SetY1NDC(.76)
		st2.SetY2NDC(.91)
		st2.SetTextColor(kBlue)
		st1 = hDataCD.GetListOfFunctions().FindObject("stats")
		st1.SetX1NDC(.35)
		st1.SetX2NDC(.55)
		st1.SetY1NDC(.76)
		st1.SetY2NDC(.91)
		st1.SetTextColor(kRed)
		canCD.Modified()
		outputFileNameCD = nameInRoot+'_'+typePlot+'_CD_'+args.grooming+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
		canCD.SaveAs('Plots/'+outputFileNameCD)

	return hDataBCD, hBkgBCD


def plotBkgEstimation( dataFile, bkgFiles, signalFiles, Groom, nameInRoot, xmin, xmax, rebinX, labX, labY, log, Norm=False ):
	"""docstring for plotBkgEstimation"""

	SRHistos = {}
	BCDHistos = {}
	tmpBCDHistos = {}
	CRHistos = {}
	for bkgSamples in bkgFiles:
		SRHistos[ bkgSamples ] = bkgFiles[ bkgSamples ][0].Get( nameInRoot+'_'+bkgSamples+'_A' )
		BCDHistos[ bkgSamples+'_B' ] = bkgFiles[ bkgSamples ][0].Get( nameInRoot+'_'+bkgSamples+'_B' )
		tmpBCDHistos[ bkgSamples+'_B' ] = BCDHistos[ bkgSamples+'_B' ].Clone()
		BCDHistos[ bkgSamples+'_C' ] = bkgFiles[ bkgSamples ][0].Get( nameInRoot+'_'+bkgSamples+'_C' )
		tmpBCDHistos[ bkgSamples+'_C' ] = BCDHistos[ bkgSamples+'_C' ].Clone()
		BCDHistos[ bkgSamples+'_D' ] = bkgFiles[ bkgSamples ][0].Get( nameInRoot+'_'+bkgSamples+'_D' )
		tmpBCDHistos[ bkgSamples+'_D' ] = BCDHistos[ bkgSamples+'_D' ].Clone()
		CRHistos[ bkgSamples ] = bkgFiles[ bkgSamples ][0].Get( nameInRoot+'_'+bkgSamples+'_ABCDProj' )
		if 'simple' in args.binning:
			if rebinX > 1: 
				SRHistos[ bkgSamples ] = rebin( SRHistos[ bkgSamples ], rebinX )
				BCDHistos[ bkgSamples+'_B' ] = rebin( BCDHistos[ bkgSamples+'_B' ], rebinX )
				BCDHistos[ bkgSamples+'_C' ] = rebin( BCDHistos[ bkgSamples+'_C' ], rebinX )
				BCDHistos[ bkgSamples+'_D' ] = rebin( BCDHistos[ bkgSamples+'_D' ], rebinX )
				CRHistos[ bkgSamples ] = rebin( CRHistos[ bkgSamples ], rebinX )
		else:
			SRHistos[ bkgSamples ] = rebin( SRHistos[ bkgSamples ], args.binning ) 
			BCDHistos[ bkgSamples+'_B' ] = rebin( BCDHistos[ bkgSamples+'_B' ], args.binning )
			BCDHistos[ bkgSamples+'_C' ] = rebin( BCDHistos[ bkgSamples+'_C' ], args.binning )
			BCDHistos[ bkgSamples+'_D' ] = rebin( BCDHistos[ bkgSamples+'_D' ], args.binning )
			CRHistos[ bkgSamples ] = rebin( CRHistos[ bkgSamples ], args.binning )
		if bkgFiles[ bkgSamples ][1] != 1: 
			scale = bkgFiles[ bkgSamples ][1] 
			SRHistos[ bkgSamples ].Scale( scale ) 
			CRHistos[ bkgSamples ].Scale( scale )
			BCDHistos[ bkgSamples+'_B' ].Scale( scale )
			BCDHistos[ bkgSamples+'_C' ].Scale( scale )
			BCDHistos[ bkgSamples+'_D' ].Scale( scale )
			tmpBCDHistos[ bkgSamples+'_B' ].Scale( scale )
			tmpBCDHistos[ bkgSamples+'_C' ].Scale( scale )
			tmpBCDHistos[ bkgSamples+'_D' ].Scale( scale )

	
	hData =  dataFile.Get( nameInRoot+'_DATA_A' )
	hData = rebin( hData, ( rebinX if 'simple' in args.binning else args.binning ) )
	htmpDataCR =  dataFile.Get( nameInRoot+'_DATA_ABCDProj' )
	htmpDataCR = rebin( htmpDataCR, ( rebinX if 'simple' in args.binning else args.binning ) )
	hDataCR = htmpDataCR.Clone()
	hDataCR.Reset()
	for ibin in range( htmpDataCR.GetNbinsX() ):
		binCont = htmpDataCR.GetBinContent( ibin )
		binErr = htmpDataCR.GetBinError( ibin )
		if binCont == 0:
			hDataCR.SetBinContent( ibin, 0 )
			hDataCR.SetBinError( ibin, 1.8 )
		else:
			hDataCR.SetBinContent( ibin, binCont )
			hDataCR.SetBinError( ibin, binErr )
	hDataB =  dataFile.Get( nameInRoot+'_DATA_B' )
	htmpDataB = hDataB.Clone()
	hDataB = rebin( hDataB, ( rebinX if 'simple' in args.binning else args.binning ) )
	hDataC =  dataFile.Get( nameInRoot+'_DATA_C' )
	htmpDataC = hDataC.Clone()
	hDataC = rebin( hDataC, ( rebinX if 'simple' in args.binning else args.binning ) )
	hDataD =  dataFile.Get( nameInRoot+'_DATA_D' )
	htmpDataD = hDataD.Clone()
	hDataD = rebin( hDataD, ( rebinX if 'simple' in args.binning else args.binning ) )
	
	for signalSamples in signalFiles:
		hSignalSR = signalFiles[ signalSamples ][0].Get( nameInRoot+'_RPVStopStopToJets_'+args.decay+'_M-'+str(args.mass)+'_A' )
		hSignalCR = signalFiles[ signalSamples ][0].Get( nameInRoot+'_RPVStopStopToJets_'+args.decay+'_M-'+str(args.mass)+'_ABCDProj' )
		if signalFiles[ signalSamples ][1] != 1: 
			scale = signalFiles[ signalSamples ][1] 
			hSignalSR.Scale( scale ) 
			hSignalCR.Scale( scale )

	hSR = hDataCR.Clone()
	hSR.Reset()
	hCR = hDataCR.Clone()
	hCR.Reset()
	for samples in SRHistos:
		hSR.Add( SRHistos[ samples ].Clone() )
		hCR.Add( CRHistos[ samples ].Clone() )
	hBkgB = hDataB.Clone()	
	hBkgB.Reset()
	hBkgC = hDataB.Clone()	
	hBkgC.Reset()
	hBkgD = hDataB.Clone()	
	hBkgD.Reset()
	htmpBkgB = htmpDataB.Clone()	
	htmpBkgB.Reset()
	htmpBkgC = htmpDataB.Clone()	
	htmpBkgC.Reset()
	htmpBkgD = htmpDataB.Clone()	
	htmpBkgD.Reset()
	for isamples in BCDHistos:
		if '_B' in isamples: 
			hBkgB.Add( BCDHistos[ isamples ].Clone() )
			htmpBkgB.Add( tmpBCDHistos[ isamples ].Clone() )
		elif '_C' in isamples: 
			hBkgC.Add( BCDHistos[ isamples ].Clone() )
			htmpBkgC.Add( tmpBCDHistos[ isamples ].Clone() )
		elif '_D' in isamples: 
			hBkgD.Add( BCDHistos[ isamples ].Clone() )
			htmpBkgD.Add( tmpBCDHistos[ isamples ].Clone() )

	if 'simple' in args.binning: binWidth = round(hSR.GetBinWidth(1))
	else: binWidth = '#sigma_{mass}' 

	#hRatiohSRhCRerrhCR, hRatiohSRhCRerrFull, hSRchi2, hSRndf, hRatiohSRhCRAsymErr = ratioPlots( hSR, hCR ) 
	#makePlots( nameInRoot, hSR, 'All MC Bkgs SR', hCR, 'All MC Bkgs ABCD Pred', binWidth, xmin, xmax, hRatiohSRhCRAsymErr, "MC (SR/Bkg Pred)", '', 'Bkg')
	#makePlots( nameInRoot, hSR, 'All MC Bkgs SR', hCR, 'All MC Bkgs ABCD Pred', binWidth, xmin, xmax, hRatiohSRhCRAsymErr, "MC (SR/Bkg Pred)", '', 'Bkg_Log', True, True)
	#hRatiohCRhSRerrhSR, hRatiohCRhSRerrFull, hCRchi2, hCRndf, hRatiohCRhSRAsymErr = ratioPlots( hCR, hSR ) 
	#makePlots( nameInRoot, hSR, 'All MC Bkgs SR', hCR, 'All MC Bkgs ABCD Pred', binWidth, xmin, xmax, hRatiohCRhSRerrFull, "MC (Bkg Pred/SR)", hRatiohCRhSRerrhSR, 'Bkg_Diff')

	#hRatiohSRhDataCRerrFull, hRatiohSRhDataCRerrhData, hDataCRchi2, hDataCRndf, hRatiohSRhDataCRAsymErr = ratioPlots( hSR, hDataCR ) 
	#makePlots( nameInRoot, hSR, 'All MC Bkgs SR', hDataCR, 'DATA ABCD Pred', binWidth, xmin, xmax, hRatiohSRhDataCRAsymErr, "MC SR/ABCD Pred", '', 'DATA_Bkg')
	#hRatiohDataCRhSRerrhSR, hRatiohDataCRhSRerrFull, hDataCRchi2, hDataCRndf, hRatiohDataCRhSRAsymErr = ratioPlots( hDataCR, hSR ) 
	#makePlots( nameInRoot, hSR, 'All MC Bkgs SR', hDataCR, 'DATA ABCD Pred', binWidth, xmin, xmax, hRatiohDataCRhSRerrFull, "ABCD Pred/MC SR)", hRatiohDataCRhSRerrhSR, 'DATA_Bkg_Diff')

	#hRatiohBkgBhDataBerrDataB, hRatiohBkgBhDataBerrFull, hBkgBchi2, hBkgBndf, hRatiohBkgBAsymErr = ratioPlots( hDataB, hBkgB ) 
	#makePlots( nameInRoot, hBkgB, 'All MC Bkgs Region B', hDataB, 'DATA Region B', binWidth, xmin, xmax, hRatiohBkgBAsymErr, "DATA/MC", '', 'B', True)
	#hRatiohBkgChDataCerrDataB, hRatiohBkgChDataCerrFull, hBkgCchi2, hBkgCndf, hRatiohBkgCAsymErr = ratioPlots( hDataC, hBkgC ) 
	#makePlots( nameInRoot, hBkgC, 'All MC Bkgs Region C', hDataC, 'DATA Region C', binWidth, xmin, xmax, hRatiohBkgCAsymErr, "DATA/MC", '', 'C', True)
	#hRatiohBkgDhDataDerrDataB, hRatiohBkgDhDataDerrFull, hBkgDchi2, hBkgDndf, hRatiohBkgDAsymErr = ratioPlots( hDataD, hBkgD ) 
	#makePlots( nameInRoot, hBkgD, 'All MC Bkgs Region D', hDataD, 'DATA Region D', binWidth, xmin, xmax, hRatiohBkgDAsymErr, "DATA/MC", '', 'D', True)

	#hRatiohDataerrDataB, hRatiohBDataerrFull, hDatachi2, hDatandf, hRatiohDataAsymErr = ratioPlots( hData, hDataCR ) 
	#makePlots( nameInRoot, hData, 'DATA', hDataCR, 'DATA ABCD Pred.', binWidth, xmin, xmax, hRatiohDataAsymErr, "DATA/ABCD Pred", '', '')
	#makePlots( nameInRoot, hData, 'DATA', hDataCR, 'DATA ABCD Pred.', binWidth, xmin, xmax, hRatiohDataAsymErr, "DATA/ABCD Pred", '', 'Log', True)
	#hRatiohDataerrDataB, hRatiohBDataerrFull, hDatachi2, hDatandf, hRatiohDatahCRAsymErr = ratioPlots( hData, hCR ) 
	#makePlots( nameInRoot, hData, 'DATA', hCR, 'MC ABCD Pred.', binWidth, xmin, xmax, hRatiohDatahCRAsymErr, "DATA/MC ABCD Pred", '', 'DATAvsBkg', True)

	#althDataCR = alternativeABCD( nameInRoot, hDataC, htmpDataB, htmpDataD, 'DATA' )
	#althDataCR = alternativeABCD( nameInRoot, hDataC, hDataB, hDataD, 'DATA' )
	althDataCR, althBkgCR = alternativeABCDCombined( nameInRoot, 25, hDataC, htmpDataB, htmpDataD, hBkgC, htmpBkgB, htmpBkgD, 'combined', rootFile=True )
	althRatiohDataerrDataB, althRatiohBDataerrFull, althDatachi2, althDatandf, althRatiohDataAsymErr = ratioPlots( hData, althDataCR ) 
	makePlots( nameInRoot, hData, 'DATA', althDataCR, 'DATA ABCD Pred.', binWidth, xmin, xmax, althRatiohDataAsymErr, "DATA/ABCD Pred", '', 'Log_altBCD', True)
	hRatiohSRhDataCRerrhCR, hRatiohSRhCRerrFull, hSRchi2, hSRndf, hRatiohSRhDataCRAsymErr = ratioPlots( hSR, althDataCR ) 
	makePlots( nameInRoot, hSR, 'All MC Bkgs SR', althDataCR, 'DATA ABCD Pred', binWidth, xmin, xmax, hRatiohSRhDataCRAsymErr, "(MC SR)/(DATA Pred)", '', 'BkgSR_DATAAltBCD_Log', True)

	althRatiohBkgerrBkgB, althRatiohBBkgerrFull, althBkgchi2, althBkgndf, althRatiohDatahBkgAsymErr = ratioPlots( althDataCR, althBkgCR ) 
	makePlots( nameInRoot, althBkgCR, 'Hybrid MC ABCD Pred.', althDataCR, 'DATA ABCD Pred', binWidth, xmin, xmax, althRatiohDatahBkgAsymErr, "ABCD Pred (DATA/MC)", '', 'DATA_Bkg_Log_altBCD', True)

	althRatiohBkgerrBkgB, althRatiohBBkgerrFull, althBkgchi2, althBkgndf, althRatiohBkgAsymErr = ratioPlots( hSR, althBkgCR ) 
	makePlots( nameInRoot, hSR, 'MC SR', althBkgCR, 'Hybrid MC ABCD Pred.', binWidth, xmin, xmax, althRatiohBkgAsymErr, "MC SR/ABCD Pred", '', 'HybridBkg_Log_altBCD', True)
	althBkgCR = alternativeABCD( nameInRoot, hBkgC, htmpBkgB, htmpBkgD, 'Bkg' )
	althRatiohBkgerrBkgB, althRatiohBBkgerrFull, althBkgchi2, althBkgndf, althRatiohBkgAsymErr = ratioPlots( hSR, althBkgCR ) 
	makePlots( nameInRoot, hSR, 'MC SR', althBkgCR, 'MC ABCD Pred.', binWidth, xmin, xmax, althRatiohBkgAsymErr, "MC SR/ABCD Pred", '', 'Bkg_Log_altBCD', True)
	sys.exit(0)


	#linearCR = TF1("linearCR", "pol0", 0, 500 ) 
	#linearCR = TF1("linearCR", "pol0", firstBinData, lastBinData ) 
	#hRatiohSRhDataCRerrhData.Fit(linearCR, 'MIR' )
	#fCR = hRatiohSRhDataCRerrhData.GetFunction("linearCR") 

	hSignalCRAlone = hSignalCR.Clone()
	hSignalCR.Add( hCR )
	#hSignalSR.Add( hSR )
	tmphSignalCR = hSignalCR.Clone()
	tmphSignalCR.Reset()
	tmphSignalCR.Divide( hSignalCR, hCR, 1., 1., '' )

#	linearSignalCR = TF1("pol0", "pol0", 50, 300 ) 
#	tmphSignalCR.Fit(linearSignalCR, 'MEIRLLF' )
#	fSignalCR = TF1( tmphSignalCR.GetFunction("pol0") )
#	linearSignalCRChi2 = fSignalCR.GetChisquare()
#	linearSignalCRNDF = fCR.GetNDF()

	hDataSignal =  hDataCR.Clone()
	hDataSignal.Add( hSignalCRAlone, -1 )
	tmphDataCR = hDataCR.Clone()
	tmphDataCR.Reset()
	tmphDataCR.Divide( hCR, hDataSignal, 1., 1., '' )

	hDataPlusSignal =  hDataCR.Clone()
	hDataPlusSignal.Add( hSignalSR )
	tmphDataCRPlusSignal = hDataCR.Clone()
	tmphDataCRPlusSignal.Reset()
	tmphDataCRPlusSignal.Divide( hDataCR, hDataPlusSignal, 1., 1., '' )
	'''
	#for i in range( 0, len(res)) : 
	#	print locFirstBin+i+1, res[i], 
	#	hRatiohSRhCRerrFull.SetBinContent( locFirstBin+i+1, res[i] )
	#hRatiohSRhCRerrFull, hRatiohSRhCRerrFullPulls = makePulls( hCR, hSR )
	#hRatiohSRhCRerrFullCR, hRatiohSRhCRerrFullCRPulls = makePulls( hSR, hCR )
	'''

	#### Data minus signal
	legend4=TLegend(0.55,0.75,0.90,0.87)
	legend4.SetFillStyle(0)
	legend4.SetTextSize(0.03)
	legend4.AddEntry( hCR, 'All MC Bkgs ABCD Pred', 'pl' )
	legend4.AddEntry( hDataSignal, '(DATA - RPV #tilde{t} '+str(args.mass)+' GeV) ABCD Pred' , 'pl' )

	hDataSignal.SetMarkerStyle(8)
	hDataSignal.SetMarkerColor(kRed-4)
	#hDataSignal.SetLineWidth(2)
	hDataSignal.GetYaxis().SetTitle('Events / '+str(binWidth))
	hDataSignal.GetXaxis().SetRangeUser( xmin, xmax )
	hDataSignal.SetMaximum( 1.2* max( hDataSignal.GetMaximum(), hCR.GetMaximum() ) )

	tdrStyle.SetPadRightMargin(0.05)
	tdrStyle.SetPadLeftMargin(0.15)
	can = TCanvas('c1', 'c1',  10, 10, 750, 750 )
	pad1 = TPad("pad1", "Fit",0,0.207,1.00,1.00,-1)
	pad2 = TPad("pad2", "Pull",0,0.00,1.00,0.30,-1);
	pad1.Draw()
	pad2.Draw()

	pad1.cd()
	pad1.SetGrid()
	#if log: pad1.SetLogy() 	
	hDataSignal.Draw("EP")
	hCR.Draw('histe same')

	CMS_lumi.extraText = "Simulation Preliminary"
	CMS_lumi.relPosX = 0.13
	CMS_lumi.CMS_lumi(pad1, 4, 0)
	legend4.Draw()
	#if not (labX and labY): labels( name, '', '' )
	#labels( name1, '', '' ) #, labX, labY )

	pad2.cd()
	pad2.SetGrid()
	pad2.SetTopMargin(0)
	pad2.SetBottomMargin(0.3)
	
	labelAxis( nameInRoot, hRatiohSRhCRerrFull, Groom )
	tmphDataCR.GetXaxis().SetRangeUser( xmin, xmax )
	tmphDataCR.SetMarkerStyle(8)
	tmphDataCR.GetXaxis().SetTitleOffset(1.1)
	tmphDataCR.GetXaxis().SetLabelSize(0.12)
	tmphDataCR.GetXaxis().SetTitleSize(0.12)
	tmphDataCR.GetYaxis().SetTitle("MC/(DATA-Signal)")
	tmphDataCR.GetYaxis().SetLabelSize(0.12)
	tmphDataCR.GetYaxis().SetTitleSize(0.12)
	tmphDataCR.GetYaxis().SetTitleOffset(0.55)
	tmphDataCR.SetMaximum( 2. )
	tmphDataCR.SetMinimum( 0. )
	tmphDataCR.GetYaxis().SetNdivisions(505)
	tmphDataCR.Draw()
	line.Draw("same")

	outputFileName = nameInRoot+'_DATAMinusRPVSt'+str(args.mass)+'_'+Groom+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	print 'Processing.......', outputFileName
	can.SaveAs( 'Plots/'+ outputFileName )
	del can

	#### Signal stack on DATA
	hSignalSR.SetFillStyle( 1001 )
	hSignalSR.SetFillColor( kRed )
	stackHisto = THStack('stackHisto', 'stack')
	stackHisto.Add( hDataCR )
	stackHisto.Add( hSignalSR )

	legend5=TLegend(0.70,0.75,0.90,0.87)
	legend5.SetFillStyle(0)
	legend5.SetTextSize(0.03)
	legend5.AddEntry( hDataCR, 'DATA ABCD Pred', 'l' )
	legend5.AddEntry( hSignalSR, 'RPV #tilde{t} '+str(args.mass)+' GeV' , 'f' )

	tdrStyle.SetPadRightMargin(0.05)
	tdrStyle.SetPadLeftMargin(0.15)
	can = TCanvas('c1', 'c1',  10, 10, 750, 750 )
	pad1 = TPad("pad1", "Fit",0,0.207,1.00,1.00,-1)
	pad2 = TPad("pad2", "Pull",0,0.00,1.00,0.30,-1);
	pad1.Draw()
	pad2.Draw()

	pad1.cd()
	pad1.SetGrid()
	#if log: pad1.SetLogy() 	
	stackHisto.Draw('hist')
	hDataCR.Draw("EP same")
	#hCR.Draw('histe same')
	canRatio.Modified()

	stackHisto.GetYaxis().SetTitle('Events / '+str(binWidth))
	stackHisto.GetXaxis().SetRangeUser( xmin, xmax )
	#stackHisto.SetMaximum( 1.2* max( hDataSignal.GetMaximum(), hCR.GetMaximum() ) )

	CMS_lumi.extraText = "Simulation Preliminary"
	CMS_lumi.relPosX = 0.13
	CMS_lumi.CMS_lumi(pad1, 4, 0)
	legend5.Draw()
	#if not (labX and labY): labels( name, '', '' )
	#labels( name1, '', '' ) #, labX, labY )

	pad2.cd()
	pad2.SetGrid()
	pad2.SetTopMargin(0)
	pad2.SetBottomMargin(0.3)
	
	labelAxis( nameInRoot, hRatiohSRhCRerrFull, Groom )
	tmphDataCRPlusSignal.GetXaxis().SetRangeUser( xmin, xmax )
	tmphDataCRPlusSignal.SetMarkerStyle(8)
	tmphDataCRPlusSignal.GetXaxis().SetTitleOffset(1.1)
	tmphDataCRPlusSignal.GetXaxis().SetLabelSize(0.12)
	tmphDataCRPlusSignal.GetXaxis().SetTitleSize(0.12)
	tmphDataCRPlusSignal.GetYaxis().SetTitle("DATA/Bkg Pred")
	tmphDataCRPlusSignal.GetYaxis().SetLabelSize(0.12)
	tmphDataCRPlusSignal.GetYaxis().SetTitleSize(0.12)
	tmphDataCRPlusSignal.GetYaxis().SetTitleOffset(0.55)
	tmphDataCRPlusSignal.SetMaximum( 2. )
	tmphDataCRPlusSignal.SetMinimum( 0. )
	tmphDataCRPlusSignal.GetYaxis().SetNdivisions(505)
	tmphDataCRPlusSignal.Draw()
	line.Draw("same")

	outputFileName = nameInRoot+'_DATAStackRPVSt'+str(args.mass)+'_'+Groom+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	print 'Processing.......', outputFileName
	can.SaveAs( 'Plots/'+ outputFileName )
	del can

def makePlots( nameInRoot, tmphisto1, labelh1, tmphisto2, labelh2, binWidth, xmin, xmax, ratio, labelRatio, ratio2, typePlot, log=False, reScale=False):
	"""docstring for makePlots"""

	histo1 = tmphisto1.Clone()
	histo2 = tmphisto2.Clone()
	legend=TLegend(0.55,0.75,0.90,0.87)
	legend.SetFillStyle(0)
	legend.SetTextSize(0.04)
	if 'DATA' in labelh1: legend.AddEntry( histo1, labelh1, 'ep' )
	else: legend.AddEntry( histo1, labelh1, 'l' )
	legend.AddEntry( histo2, labelh2, 'pl' )

	histo1.GetYaxis().SetTitle('Events / '+(str(int(binWidth)) if 'simple' in args.binning else binWidth )+' GeV')
	histo1.GetXaxis().SetRangeUser( 50, 350 )
	histo2.GetXaxis().SetRangeUser( 50, 350 )
	histo1.SetMaximum( 1.1* max( histo1.GetMaximum(), histo2.GetMaximum() ) )
	if 'MC' in labelh1: 
		histo1.SetLineColor(kRed-4)
		histo1.SetLineWidth(2)
	histo2.SetLineColor(kBlue-4)
	histo2.SetLineWidth(2)
	if 'MC' in labelh2: histo2.SetLineStyle(2)
	else: histo2.SetLineStyle(1)

	tdrStyle.SetPadRightMargin(0.05)
	tdrStyle.SetPadLeftMargin(0.15)
	can = TCanvas('c1', 'c1',  10, 10, 750, 750 )
	pad1 = TPad("pad1", "Fit",0,0.207,1.00,1.00,-1)
	pad2 = TPad("pad2", "Pull",0,0.00,1.00,0.30,-1);
	pad1.Draw()
	pad2.Draw()

	pad1.cd()
	if log: 
		pad1.SetLogy() 	
		if not 'Region' in labelh1: histo1.SetMaximum( (5000 if 'low' in args.RANGE else 500) )
		histo1.SetMinimum( 0.5 )
	else: 
		pad1.SetGrid()
		if not 'Region' in labelh1: histo1.SetMaximum( (3000 if 'low' in args.RANGE else 400) )
	if 'DATA' in labelh1: 
		histo1.SetMarkerStyle(8)
		histo1.Draw("PE")
	else: histo1.Draw("histe")
	#histo1UncBand = addSysBand( histo1, 1.10, kRed )
	#legend.AddEntry( histo1UncBand, 'Syst. unc.', 'f' )
	#histo1UncBand.Draw("same E2")
	histo2.Draw('hist E0 same')
	#histo2UncBand = addSysBand( histo2, 1.10, kBlue )
	#histo2UncBand.Draw("same E2")

	#locFirstBin = boostedMassAveBins.index( firstBinData )
	tmpHisto1 = histo1.Clone()
	tmpHisto2 = histo2.Clone()
	'''
	if 'DATA' in labelh2: 
		if 'simple' in args.binning: 
			firstBinData = histo2.FindFirstBinAbove( 0, 1 )*binWidth  #histo2.GetXaxis().GetLowEdge(  )  #40
			lastBinData = histo2.FindLastBinAbove( 10, 1 )*binWidth  #hDataCR.GetXaxis().GetLowEdge(  )   #300
		else: 
			firstBinData = boostedMassAveBins[ histo2.FindFirstBinAbove( 0, 1 ) ]
			lastBinData = boostedMassAveBins[ histo2.FindLastBinAbove( 10, 1 ) ]
		#tmpHisto1.GetXaxis().SetRangeUser( firstBinData, lastBinData )
		#tmpHisto2.GetXaxis().SetRangeUser( firstBinData, lastBinData )
	'''
	res = array( 'd', ( [ 0 ] * tmpHisto1.GetNbinsX() ) )
	chi2Ndf =  round( tmpHisto1.Chi2Test(tmpHisto2, 'WWCHI2/NDFP', res), 2 )
	chi2 =  round( tmpHisto1.Chi2Test(tmpHisto2, 'WWCHI2'), 2 )
	chi2Test = TLatex( 0.6, 0.7, '#chi^{2}/ndF Test = '+ str( chi2 )+'/'+str( round(chi2/chi2Ndf) ) )
	chi2Test.SetNDC()
#	#chi2Test = TLatex( 209, 2000, '#chi^{2}/ndF Test = '+ str( round(hSRchi2,2) )+'/'+str( hSRndf ) )
	chi2Test.SetTextFont(42) ### 62 is bold, 42 is normal
	chi2Test.SetTextSize(0.04)
	chi2Test.Draw()

	if 'DATA' in labelh1: tmpLabel = 'DATA'
	else: tmpLabel = 'SR'
	numEvents = TLatex( 0.6, 0.62, '#splitline{events '+tmpLabel+'/ABCD Pred = }{'+ str( round( histo1.Integral(),2 ) )+'/'+str( round( histo2.Integral(),2 ) )+'}' )
	numEvents.SetNDC()
	numEvents.SetTextFont(42) ### 62 is bold, 42 is normal
	numEvents.SetTextSize(0.04)
	numEvents.Draw()

	CMS_lumi.extraText = ("Preliminary" if 'DATA' in labelh2 else "Simulation Preliminary")
	CMS_lumi.relPosX = 0.13
	CMS_lumi.CMS_lumi(pad1, 4, 0)
	legend.Draw()

	pad2.cd()
	pad2.SetGrid()
	pad2.SetTopMargin(0)
	pad2.SetBottomMargin(0.3)
	tmpPad2= pad2.DrawFrame(50,0,350,2)
	#if 'simple' in args.binning: tmpPad2= pad2.DrawFrame(50,0,350,2)
	#else: tmpPad2= pad2.DrawFrame(0,0,boostedMassAveBins[-1],2)
	tmpPad2.SetXTitle( 'Average pruned mass [GeV]' )
	tmpPad2.SetYTitle( labelRatio )
	tmpPad2.SetTitleSize(0.12, "x")
	tmpPad2.SetTitleSize(0.12, 'y')
	tmpPad2.SetLabelSize(0.12, 'x')
	tmpPad2.SetLabelSize(0.12, 'y')
	tmpPad2.SetTitleOffset(0.5, 'y')
	#tmpPad2.CenterXTitle()
	#tmpPad2.SetTitleOffset(0.55)
	tmpPad2.SetNdivisions(505, 'x' )
	tmpPad2.SetNdivisions(505, 'y' )
	pad2.Modified()
	
	#labelAxis( nameInRoot, ratio, args.grooming )
	#ratio.GetXaxis().SetRangeUser( xmin, xmax )
	ratio.SetMarkerStyle(8)
	ratio.SetLineColor(kBlack)
	#ratio.SetMaximum( 2. )
	#ratio.SetMinimum( 0. )
	#if isinstance( ratio, TGraphAsymmErrors ): ratio.Draw('p')
	ratio.Draw('P')
	if isinstance( ratio2, TH1 ):
		ratio2.SetFillStyle(3004)
		ratio2.SetFillColor( kRed )
		ratio2.Draw('same E2')
	line.Draw("same")
	line11.Draw("same")
	line09.Draw("same")

	outputFileName = nameInRoot+'_'+typePlot+'_'+args.grooming+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	if not 'simple' in args.binning: outputFileName = outputFileName.replace( typePlot, typePlot+'_ResoBasedBin' )
	print 'Processing.......', outputFileName
	can.SaveAs( 'Plots/'+ outputFileName )
	del can

	if reScale:
		canRatio = TCanvas('canRatio', 'canRatio',  10, 10, 750, 500 )
		if 'simple' in args.binning: tmpCanRatio = canRatio.DrawFrame(0,0,500,3)
		else: tmpCanRatio = canRatio.DrawFrame(0,0, boostedMassAveBins[-1] ,3)
		gStyle.SetOptFit(1)
		tmpCanRatio.SetXTitle( 'Average pruned mass [GeV]' )
		tmpCanRatio.SetYTitle( labelRatio )
		canRatio.Modified()
		ratio.Draw('ps')
		line.Draw("same")
		ratioP0 = TF1( 'ratioP0', 'pol0', 0, 500 )
		for i in range(2): ratio.Fit( ratioP0, 'MIR' )
		ratioP0.SetLineWidth(2)
		ratioP0.SetLineColor(kBlue)
		ratioP0.Draw("same")
		ratioP1 = TF1( 'ratioP1', 'pol1', 0, 500 )
		ratio1 = ratio.Clone()
		for i in range(2): ratio1.Fit( ratioP1, 'MIR' )
		ratio1.Draw("ps")
		ratioP1.SetLineWidth(2)
		ratioP1.SetLineColor(kViolet)
		ratioP1.Draw("same")
		canRatio.Update()
		st1 = ratio.GetListOfFunctions().FindObject("stats")
		st1.SetX1NDC(.15)
		st1.SetX2NDC(.35)
		st1.SetY1NDC(.76)
		st1.SetY2NDC(.91)
		st1.SetTextColor(kBlue)
		st2 = ratio1.GetListOfFunctions().FindObject("stats")
		st2.SetX1NDC(.35)
		st2.SetX2NDC(.55)
		st2.SetY1NDC(.76)
		st2.SetY2NDC(.91)
		st2.SetTextColor(kViolet)
		canRatio.Modified()
		outputFileNameRatio = nameInRoot+'_'+typePlot+'_Ratio_'+args.grooming+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
		if not 'simple' in args.binning: outputFileNameRatio = outputFileNameRatio.replace( typePlot, typePlot+'_ResoBasedBin' )
		canRatio.SaveAs('Plots/'+outputFileNameRatio)
		del canRatio


		tdrStyle.SetPadRightMargin(0.05)
		tdrStyle.SetPadLeftMargin(0.15)
		canReScale = TCanvas('canReScale', 'canReScale',  10, 10, 750, 750 )
		pad1 = TPad("pad1", "Fit",0,0.207,1.00,1.00,-1)
		pad2 = TPad("pad2", "Pull",0,0.00,1.00,0.30,-1);
		pad1.Draw()
		pad2.Draw()

		pad1.cd()
		if log: 
			pad1.SetLogy() 	
			histo1.SetMaximum( (5000 if 'low' in args.RANGE else 500) )
		else: 
			pad1.SetGrid()
			histo1.SetMaximum( (3000 if 'low' in args.RANGE else 400) )
		if 'DATA' in labelh1: 
			histo1.SetMarkerStyle(8)
			histo1.Draw("PE")
		else: histo1.Draw("histe")
		#histo1UncBand = addSysBand( histo1, 1.10, kRed )
		#legend.AddEntry( histo1UncBand, 'Syst. unc.', 'f' )
		#histo1UncBand.Draw("same E2")
		reScaleFactor = ratioP0.GetParameter( 0 ) 
		histo2.Scale( reScaleFactor )
		histo2.Draw('hist E0 same')
		#histo2UncBand = addSysBand( histo2, 1.10, kBlue )
		#histo2UncBand.Draw("same E2")

		#locFirstBin = boostedMassAveBins.index( firstBinData )
		tmpHisto1 = histo1.Clone()
		tmpHisto2 = histo2.Clone()
		res = array( 'd', ( [ 0 ] * tmpHisto1.GetNbinsX() ) )
		chi2Ndf =  round( tmpHisto1.Chi2Test(tmpHisto2, 'WWCHI2/NDFP', res), 2 )
		chi2 =  round( tmpHisto1.Chi2Test(tmpHisto2, 'WWCHI2'), 2 )
		chi2Test = TLatex( 0.6, 0.7, '#chi^{2}/ndF Test = '+ str( chi2 )+'/'+str( round(chi2/chi2Ndf) ) )
		chi2Test.SetNDC()
	#	#chi2Test = TLatex( 209, 2000, '#chi^{2}/ndF Test = '+ str( round(hSRchi2,2) )+'/'+str( hSRndf ) )
		chi2Test.SetTextFont(42) ### 62 is bold, 42 is normal
		chi2Test.SetTextSize(0.04)
		chi2Test.Draw()

		if 'DATA' in labelh1: tmpLabel = 'DATA'
		else: tmpLabel = 'SR'
		numEvents = TLatex( 0.6, 0.62, '#splitline{events '+tmpLabel+'/ABCD Pred = }{'+ str( round( histo1.Integral(),2 ) )+'/'+str( round( histo2.Integral(),2 ) )+'}' )
		numEvents.SetNDC()
		numEvents.SetTextFont(42) ### 62 is bold, 42 is normal
		numEvents.SetTextSize(0.04)
		numEvents.Draw()

		CMS_lumi.extraText = ("Preliminary" if 'DATA' in labelh2 else "Simulation Preliminary")
		CMS_lumi.relPosX = 0.13
		CMS_lumi.CMS_lumi(pad1, 4, 0)
		legend.Draw()

		pad2.cd()
		pad2.SetGrid()
		pad2.SetTopMargin(0)
		pad2.SetBottomMargin(0.3)
		if 'simple' in args.binning: TMPPad2= pad2.DrawFrame(0,0,500,2)
		else: TMPPad2= pad2.DrawFrame(0,0,boostedMassAveBins[-1],2)
		TMPPad2.SetXTitle( 'Average pruned mass [GeV]' )
		TMPPad2.SetYTitle( labelRatio )
		TMPPad2.SetTitleSize(0.12, "x")
		TMPPad2.SetTitleSize(0.12, 'y')
		TMPPad2.SetLabelSize(0.12, 'x')
		TMPPad2.SetLabelSize(0.12, 'y')
		TMPPad2.SetTitleOffset(0.5, 'y')
		#TMPPad2.CenterXTitle()
		#TMPPad2.SetTitleOffset(0.55)
		TMPPad2.SetNdivisions(505, 'x' )
		TMPPad2.SetNdivisions(505, 'y' )
		pad2.Modified()
		
		none1, none2, none3, none3, newRatio = ratioPlots( histo1, histo2 ) 
		#labelAxis( nameInRoot, newRatio, args.grooming )
		#newRatio.GetXaxis().SetRangeUser( xmin, xmax )
		newRatio.SetMarkerStyle(8)
		newRatio.SetLineColor(kBlack)
		newRatio.GetYaxis().SetNdivisions(505)
		#if isinstance( newRatio, TGraphAsymmErrors ): newRatio.Draw('ap')
		newRatio.Draw('P')
		line.Draw("same")
		line11.Draw("same")
		line09.Draw("same")

		outputFileName = outputFileName.replace( typePlot, typePlot+'_reScale_' )
		if not 'simple' in args.binning: outputFileName = outputFileName.replace( typePlot, typePlot+'_ResoBasedBin' )
		print 'Processing.......', outputFileName
		canReScale.SaveAs( 'Plots/'+ outputFileName )
		del canReScale
	'''
	can = TCanvas('c1', 'c1',  10, 10, 750, 500 )
	gStyle.SetOptStat(1)
	pullGaus = TF1( 'pullGaus', 'gaus', -3, 3 )
	hRatiohSRhCRerrFullPulls.Fit( 'pullGaus', 'MIR' )
	hRatiohSRhCRerrFullPulls.GetXaxis().SetTitle('Pulls')
	hRatiohSRhCRerrFullPulls.GetYaxis().SetTitle('Bins')
	hRatiohSRhCRerrFullPulls.Draw('PE')
	#can.Update()
	#gStyle.SetStatY(0.91)
	#gStyle.SetStatX(0.95)
	#gStyle.SetStatW(0.15)
	#gStyle.SetStatH(0.30) 
	#print hRatiohSRhCRerrFullPulls.GetListOfFunctions().FindObject("stats")
#	st1.SetX1NDC(.12);
#	st1.SetX2NDC(.32);
#	st1.SetY1NDC(.76);
#	st1.SetY2NDC(.91);
#	#st1.SetTextColor(4);
	can.Modified()
	outputFileNamePulls= nameInRoot+'_Pulls_Bkg_'+Groom+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	can.SaveAs('Plots/'+outputFileNamePulls)
	'''
def tmpPlotBkgEstimation( dataFile, Groom, nameInRoot, xmin, xmax, rebinX, labX, labY, log, Norm=False ):
	"""docstring for tmpPlotBkgEstimation"""

	hData_A =  dataFile.Get( 'BoostedAnalysisPlots/'+nameInRoot+'_A' )
	hData_A.Rebin( rebinX )
	hData_B =  dataFile.Get( 'BoostedAnalysisPlots/'+nameInRoot+'_B' )
	hData_B.Rebin( rebinX )
	hData_C =  dataFile.Get( 'BoostedAnalysisPlots/'+nameInRoot+'_C' )
	hData_C.Rebin( rebinX )
	hData_D =  dataFile.Get( 'BoostedAnalysisPlots/'+nameInRoot+'_D' )
	hData_D.Rebin( rebinX )
	
	tmpBC = hData_B.Clone()
	tmpBC.Reset()
	tmpBC.Multiply( hData_B, hData_C, 1, 1, '')
	tmpBCD = hData_B.Clone()
	tmpBCD.Reset()
	tmpBCD.Divide( tmpBC, hData_D, 1, 1, '')

	tmphSignalCR = hData_A.Clone()
	tmphSignalCR.Reset()
	tmphSignalCR.Divide( hData_A, tmpBCD, 1., 1., '' )

	binWidth = hData_A.GetBinWidth(1)

	legend3=TLegend(0.55,0.75,0.90,0.87)
	legend3.SetFillStyle(0)
	legend3.SetTextSize(0.03)
	legend3.AddEntry( hData_A, 'DATA - SR' , 'l' )
	legend3.AddEntry( tmpBCD, 'DATA - ABCD Pred', 'pl' )

	hData_A.SetLineColor(kRed-4)
	hData_A.SetLineWidth(2)
	hData_A.GetYaxis().SetTitle('Events / '+str(binWidth))
	hData_A.GetXaxis().SetRangeUser( xmin, xmax )
	hData_A.SetMaximum( 1.2* max( hData_A.GetMaximum(), tmpBCD.GetMaximum() ) )
	tmpBCD.SetLineColor(kBlue-4)
	tmpBCD.SetLineWidth(2)
	tmpBCD.SetLineStyle(2)

	tdrStyle.SetPadRightMargin(0.05)
	tdrStyle.SetPadLeftMargin(0.15)
	can = TCanvas('c1', 'c1',  10, 10, 750, 750 )
	pad1 = TPad("pad1", "Fit",0,0.207,1.00,1.00,-1)
	pad2 = TPad("pad2", "Pull",0,0.00,1.00,0.30,-1);
	pad1.Draw()
	pad2.Draw()

	pad1.cd()
	pad1.SetGrid()
	#if log: pad1.SetLogy() 	
	hData_A.Draw("histe")
	tmpBCD.Draw('histe same')

	CMS_lumi.extraText = "Preliminary"
	CMS_lumi.relPosX = 0.13
	CMS_lumi.CMS_lumi(pad1, 4, 0)
	legend3.Draw()
	#if not (labX and labY): labels( name, '', '' )
	#labels( name1, '', '' ) #, labX, labY )

	pad2.cd()
	pad2.SetGrid()
	pad2.SetTopMargin(0)
	pad2.SetBottomMargin(0.3)
	
	labelAxis( nameInRoot, hData_A, Groom )
	tmphSignalCR.GetXaxis().SetRangeUser( xmin, xmax )
	tmphSignalCR.SetMarkerStyle(8)
	tmphSignalCR.GetXaxis().SetTitleOffset(1.1)
	tmphSignalCR.GetXaxis().SetLabelSize(0.12)
	tmphSignalCR.GetXaxis().SetTitleSize(0.12)
	tmphSignalCR.GetYaxis().SetTitle("SR/ABCD Pred")
	tmphSignalCR.GetYaxis().SetLabelSize(0.12)
	tmphSignalCR.GetYaxis().SetTitleSize(0.12)
	tmphSignalCR.GetYaxis().SetTitleOffset(0.55)
	tmphSignalCR.SetMaximum( 2. )
	tmphSignalCR.SetMinimum( 0. )
	tmphSignalCR.GetYaxis().SetNdivisions(505)
	tmphSignalCR.Draw()
	line.Draw("same")

	outputFileName = nameInRoot+'_BkgPlusRPVSt'+str(args.mass)+'_'+Groom+'_'+args.RANGE+'_QCD'+args.qcd+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	print 'Processing.......', outputFileName
	can.SaveAs( 'Plots/'+ outputFileName )
	del can

def plot2DBkgEstimation( rootFile, sample, Groom, nameInRoot, titleXAxis, titleXAxis2, Xmin, Xmax, rebinx, Ymin, Ymax, rebiny, legX, legY ):
	"""docstring for plot"""

	outputFileName = nameInRoot+'_'+sample+'_'+Groom+'_'+args.RANGE+'_bkgShapeEstimationBoostedPlots'+args.version+'.'+args.extension
	print 'Processing.......', outputFileName

	bkgHistos = OrderedDict()
	if isinstance(rootFile, dict):
		for bkg in rootFile:
			bkgHistos[ bkg+'_A' ] = Rebin2D( rootFile[ bkg ][0].Get( nameInRoot+'_'+bkg+'_A' ), rebinx, rebiny )
			bkgHistos[ bkg+'_B' ] = Rebin2D( rootFile[ bkg ][0].Get( nameInRoot+'_'+bkg+'_B' ), rebinx, rebiny )
			bkgHistos[ bkg+'_C' ] = Rebin2D( rootFile[ bkg ][0].Get( nameInRoot+'_'+bkg+'_C' ), rebinx, rebiny )
			bkgHistos[ bkg+'_D' ] = Rebin2D( rootFile[ bkg ][0].Get( nameInRoot+'_'+bkg+'_D' ), rebinx, rebiny )

		hBkg = bkgHistos[ bkg+'_B' ].Clone()
		hBkg.Reset()
		for samples in bkgHistos:
			print samples
			hBkg.Add( bkgHistos[ samples ].Clone() )
	else: 
		bkgHistos[ sample+'_A' ] = Rebin2D( rootFile.Get( nameInRoot+'_'+sample+'_A' ), rebinx, rebiny )
		bkgHistos[ sample+'_B' ] = Rebin2D( rootFile.Get( nameInRoot+'_'+sample+'_B' ), rebinx, rebiny )
		bkgHistos[ sample+'_C' ] = Rebin2D( rootFile.Get( nameInRoot+'_'+sample+'_C' ), rebinx, rebiny )
		bkgHistos[ sample+'_D' ] = Rebin2D( rootFile.Get( nameInRoot+'_'+sample+'_D' ), rebinx, rebiny )

		hBkg = bkgHistos[ sample+'_B' ].Clone()
		for samples in bkgHistos:
			if sample+'_B' not in samples: hBkg.Add( bkgHistos[ samples ].Clone() )

	if 'DATA' in sample: CMS_lumi.extraText = "Preliminary"
	else: CMS_lumi.extraText = "Simulation Preliminary"
	hBkg.GetXaxis().SetTitle( titleXAxis )
	hBkg.GetYaxis().SetTitleOffset( 0.9 )
	hBkg.GetYaxis().SetTitle( titleXAxis2 )
	corrFactor = hBkg.GetCorrelationFactor()
	textBox=TLatex()
	textBox.SetNDC()
	textBox.SetTextSize(0.05) 
	textBox.SetTextFont(62) ### 62 is bold, 42 is normal
	textBox.SetTextAlign(31)

	if (Xmax or Ymax):
		hBkg.GetXaxis().SetRangeUser( Xmin, Xmax )
		hBkg.GetYaxis().SetRangeUser( Ymin, Ymax )

	tdrStyle.SetPadRightMargin(0.12)
	hBkg.SetMaximum( 1500 )
	hBkg.SetMinimum( 0.01 )
	can = TCanvas('c1', 'c1',  750, 500 )
	can.SetLogz()
	hBkg.Draw('colz')
	textBox.DrawLatex(0.85, 0.85, sample  )
	textBox1 = textBox.Clone()
	textBox1.DrawLatex(0.85, 0.8, 'Corr. Factor = '+str(round(corrFactor,2)))

	CMS_lumi.relPosX = 0.13
	CMS_lumi.CMS_lumi(can, 4, 0)

	can.SaveAs( 'Plots/'+outputFileName )
	#can.SaveAs( 'Plots/'+outputFileName.replace(''+ext, 'gif') )
	del can


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--proc', action='store', default='1D', help='Process to draw, example: 1D, 2D, MC.' )
	parser.add_argument('-d', '--decay', action='store', default='UDD312', dest='decay', help='Decay, example: UDD312, UDD323.' )
	parser.add_argument('-b', '--binning', action='store', default='simple', help='Binning: resoBased or simple' )
	parser.add_argument('-v', '--version', action='store', default='v05', help='Version: v01, v02.' )
	parser.add_argument('-g', '--grom', action='store', default='pruned', dest='grooming', help='Grooming Algorithm, example: Pruned, Filtered.' )
	parser.add_argument('-m', '--mass', action='store', default='100', help='Mass of Stop, example: 100' )
	parser.add_argument('-q', '--qcd', action='store', default='Pt', dest='qcd', help='Type of QCD binning, example: HT.' )
	parser.add_argument('-l', '--lumi', action='store', default=2.6, help='Luminosity, example: 1.' )
	parser.add_argument('-r', '--range', action='store', default='low', dest='RANGE', help='Trigger used, example PFHT800.' )
	parser.add_argument('-e', '--extension', action='store', default='png', help='Extension of plots.' )

	try:
		args = parser.parse_args()
	except:
		parser.print_help()
		sys.exit(0)
	
	CMS_lumi.lumi_13TeV = str(args.lumi)+" fb^{-1}"
	
	if 'Pt' in args.qcd: 
		#bkgLabel='(w QCD pythia8)'
		QCDSF = 0.80
	else: 
		#bkgLabel='(w QCD madgraphMLM+pythia8)'
		QCDSF = 1.05

	bkgFiles = OrderedDict() 
	signalFiles = {}
	dataFile = TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_DATA_'+args.RANGE+'_'+args.version+'.root')
	signalFiles[ 'Signal' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_RPVStopStopToJets_'+args.decay+'_M-'+str(args.mass)+'_'+args.RANGE+'_'+args.version+'.root'), 1, args.decay+' RPV #tilde{t} '+str(args.mass)+' GeV', kRed-4]
	bkgFiles[ 'TTJets' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_TTJets_'+args.RANGE+'_'+args.version+'.root'),	1, 't #bar{t} + Jets', kGreen ]
    	bkgFiles[ 'ZJetsToQQ' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_ZJetsToQQ_'+args.RANGE+'_'+args.version+'.root'), 1., 'Z + Jets', kOrange]
    	bkgFiles[ 'WJetsToQQ' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_WJetsToQQ_'+args.RANGE+'_'+args.version+'.root'), 1., 'W + Jets', kMagenta ]
	bkgFiles[ 'WWTo4Q' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_WWTo4Q_'+args.RANGE+'_'+args.version+'.root'), 1 , 'WW (had)', kMagenta+2 ]
	bkgFiles[ 'ZZTo4Q' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_ZZTo4Q_'+args.RANGE+'_'+args.version+'.root'), 1, 'ZZ (had)', kOrange+2 ]
	bkgFiles[ 'WZ' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_WZ_'+args.RANGE+'_'+args.version+'.root'), 1, 'WZ', kCyan ]
	bkgFiles[ 'QCD'+args.qcd+'All' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_QCD'+args.qcd+'All_'+args.RANGE+'_'+args.version+'.root'), QCDSF, 'QCD', kBlue-4 ]
	#bkgFiles[ 'QCDPtAll' ] = [ TFile.Open('Rootfiles/RUNMiniBoostedAnalysis_'+args.grooming+'_QCDPtAll_'+args.RANGE+'_'+args.version+'.root'), QCDSF, 'QCD', kBlue-4 ]


	massMinX = 0
	massMaxX = 510
	jetMassHTlabY = 0.20
	jetMassHTlabX = 0.85

	if 'all' in args.grooming: Groommers = [ '', 'Trimmed', 'Pruned', 'Filtered', "SoftDrop" ]
	else: Groommers = [ args.grooming ]

	for optGroom in Groommers:
		if '2D' in args.proc: 
			#for bkg in bkgFiles: plot2DBkgEstimation( bkgFiles[ bkg ][0], bkg, optGroom, 'prunedMassAsymVsdeltaEtaDijet', 'Mass Asymmetry', '| #eta_{j1} - #eta_{j2} |', 0, 1, 1, 0, 5, 1, jetMassHTlabX, jetMassHTlabY)
			plot2DBkgEstimation( dataFile, 'DATA', optGroom, 'prunedMassAsymVsdeltaEtaDijet', 'Mass Asymmetry', '| #eta_{j1} - #eta_{j2} |', 0, 1, 1, 0, 5, 1, jetMassHTlabX, jetMassHTlabY)
			#for bkg in bkgFiles: plot2DBkgEstimation( bkgFiles, bkg, optGroom, 'prunedMassAsymVsdeltaEtaDijet', 'Mass Asymmetry', '| #eta_{j1} - #eta_{j2} |', 0, 1, 1, 0, 5, 1, jetMassHTlabX, jetMassHTlabY)
			#for bkg in signalFiles: plot2DBkgEstimation( signalFiles[ bkg ][0], 'RPVStopStopToJets_'+args.decay+'_M-'+str(args.mass), optGroom, 'prunedMassAsymVsdeltaEtaDijet', 'Mass Asymmetry', '| #eta_{j1} - #eta_{j2} |', 0, 1, 1, 0, 5, 1, jetMassHTlabX, jetMassHTlabY)
		else: 
			tmpListCuts = selection[ 'RPVStopStopToJets_'+args.decay+'_M-'+str(args.mass) ][-2:]
			nameVarABCD = 'massAve_'+tmpListCuts[0][0]+'Vs'+tmpListCuts[1][0]
			plotBkgEstimation( dataFile, bkgFiles, signalFiles, optGroom, nameVarABCD, 0, massMaxX, 5, '', '', False )