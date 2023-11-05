# PRIMO WatchDog

The PRIMO Monte Carlo software [Strahlenther Onkol. 2013;189:881-886] allows the simulation of clinical IMRT and VMAT plans for Varian linacs. PRIMO relies on the general-purpose Monte Carlo code PENELOPE and the fast Monte Carlo code DPM.
The setup of a plan simulation in PRIMO takes 5-10 min, as several manual steps are needed: project creation, selection of phase-space file (PSF), import of DICOM files, etc. After the simulation, a manual import of the DICOM dose file from the treatment planning system (TPS) is also needed to compare PRIMO and TPS dose distributions. PRIMO provides an advanced macro mode to speed up the process, but the macro file creation is also manual. Hence, the simulation of plans on a routine basis can be very time-consuming. We aimed to automate the simulation setup of clinical plans, including IMRT, dynamic conformal arc (DCA), and VMAT techniques.

A set of scripts (PRIMO WatchDog) was developed in Python 3.7 to automate the simulation setup:
-	The scripts run in background monitoring a specified folder. Plan DICOM files can be pasted in this folder or manually exported from the TPS to the folder. The following steps proceed automatically.
-	When the DICOM files are detected, the patient and plan ID, linac ID, beam energy, and MLC model, among other parameters, are read from the DICOM files.
-	The scripts create a PRIMO macro file to setup the simulation and the gamma index analyses. At this point, the scripts are ready to manage a new plan in a parallel process.
-	The scripts start PRIMO with the macro file, and the simulation begins.
-	Once the simulation and the gamma index analysis is done, the PDF report with the results is open for review, and the associated PRIMO instance is closed.

The scripts were tested with the following hardware and software:
-	PRIMO v. 0.3.64.1814 under Windows 7 and Windows 10.
-	Varian PSF for 6 MV and 6 MV FFF photon beams from a TrueBeam linac.
-	IMRT and VMAT plans from Varian Eclipse 15.6/16.1, for TrueBeam linacs with Millennium 120 and HD MLC models.
-	VMAT plans from Brainlab Elements Cranial SRS 3.0, and DCA plans from Brainlab Elements Multiple Metastases 3.0, for a TrueBeam linac with HD MLC.

In conclusion, Python scripts were developed to automate the simulation setup for Monte Carlo simulations of clinical IMRT, VMAT and DCA plans with the PRIMO software, with a minimal workload for the medical physicist. This facilitates introducing PRIMO as a routine system for independent verifications.
