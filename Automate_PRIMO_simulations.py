# -*- coding: utf-8 -*-
"""
AutomatePRIMOsimulations


v1.09_para_GitHub: no new functionalities. Simplifications to publish in
                   Github. Quiron edition removed. MH. 8/10/23.

v1.09: added gamma criteria 3%/1mm global with threshold 10%, only for QUIRON.
       Opens all gamma analyses PDF reports. 1/11/22. MH.

v1.08: added more conditions to detect if the CT was acquired or if it is a 
       virtual phantom created in the TPD. Uses the "KVP" DICOM tag. 23/2/22.MH

v1.07: corrected bug in Analyze_simulation_results. Change the pattern "\RP."
       and "\CT." to "\RP" and "\CT". 15/2/22. MH.

v1.06: Bug: "Dose planning" in ManufacturerModelName does not guarantee that
       the plan is from Elements MBM. 14/2/22. MH.

v1.05: Deletes the original PDF and txt reports to avoid repeated files. Opens
       the PDF report after simulation. Adds plan technique (3DCRT,
       VMAT, etc). Takes into account in the macro if the CT is from a
       virtual phantom. 13/2/22. MH.

v1.04: Bug with setup fields corrected. If a HyperArc plan is detected,
       and QUIRON = YES, the full PSF is used, ignoring the factor stated in
       the CONFIG.DOG file. Gamma criteria were added to the CONFIG but they
       are not operative yet.24/1/22. MH.
       
v1.03: Add "# SEND TELEGRAM" parameter in the CONFIG.DOG file. Removes "#"
       character from plan name, as PRIMO does not accept it. 
       Added "# QUIRON", so only one edition of the program is needed.
       New parameters are added to the CSV file: linac_ID, TPS and TPS version.
       MH. 22-1-22.

v1.02: Implements recursive watchdog: the program works both with a 
       set of DICOM files, or with a folder containing the DICOM files.
       29-12-21.

v1.01: Implements independent threading to allow multiple simultaneous
       simulations. Uses the PID of the PRIMO process to close the 
       corresponding process. 28-12-2021.

v1.00: v0.11, renamed to v1.00. Version adapted to PRIMO 0.3.64.1816 (PRIMO
       version customized by Miguel Rodríguez). Previous script versions were
       adapted to PRIMO 0.3.64.1814. PDF reports use names with date. Results
       of the simulation and of the gamma analyses are stored in a csv file
       for further analysis. 27-12-2021. MH.

v0.10: Minor robustness improvements. It works both in Dell-MH and in the
       laptop (two different CONFIG.DOG files). If DICOM files already exist,
       they are overwritten. If project folder already exists, it is deleted
       and created again with the macro. If change of segmentation file fails,
       it continues with the default segmentation file. Analysis of results 
       work-in-progress. Dec 18, 2021. MH

v0.09: modifies the segmentation file on-the-fly. Include the option in the
       CONFIG.DOG file to use the REDUCED or ORIGINAL CT resolution. It is
       possible now to introduce a fraction of the PSF histories to be
       simulated. Added a new gamma criteria: 2%/2 mm. Dec 8, 2021. MH.

v0.08: Log capability added. Nominal energy and fluence mode (FF or FFF) is
       correctly read in this version. Nov 21, 2021. MH.

v0.07: Try-except al enviar mensajes de Telegram (no funciona el envío desde el
       hospital). Cambio a formato x.xx. Nov 9, 2021. MH.

v0.6: Minor improvements. 

v0.5: Same functionality as v 0.4. Just added splash screen. Nov 07 2021. MH.

v0.4: Read MORE configuration parameters from config file. Nov 06 2021. MH.

v0.3: Read configuration parameters from config file. Nov 02 2021. MH.

v0.2: Created on Nov 01 2021




@author: Marcelino Hermida
"""


def automate_PRIMO_simulation():
    
    # script version
    VERSION = "v. 1.09 GitHub"
    
    # IMPORTS
    import os
    import sys
    import subprocess
    import time
    import pydicom
    import shutil
    from send_telegram_message import telegram_bot_sendtext
    from send_telegram_message import telegram_bot_senddocument
    from WriteToLog import WriteToLog
    from pathlib import Path
    import glob
    import re
    import winsound

        
    # current folder
    execution_folder = os.getcwd()
    
        
    
    # READ CONFIG file
    # Source: (https://stackabuse.com/read-a-file-line-by-line-in-python/)
    with open('.\\CONFIG.DOG', encoding="UTF-8") as config_file:
                  config_lines = config_file.readlines()   # read lines of file    

    for index, line in enumerate(config_lines):
        if line == "# DICOM RT IMPORT FOLDER\n":
                DICOM_import_folder = config_lines[index + 1].strip('\n')
        if line == "# DICOM RT CASES\n":
                DICOM_RT_cases = config_lines[index + 1].strip('\n')
        #PSF PATH
        if line == "# PSF PATH 6 MV\n":
                PSF_path_6MV = config_lines[index + 1].strip('\n')
        if line == "# PSF PATH 6 MV FFF\n":
                PSF_path_6MV_FFF = config_lines[index + 1].strip('\n')
        
        if line == "# SIMULATIONS FOLDERS\n":
                Simulations_folders = config_lines[index + 1].strip('\n')
        if line == "# PRIMO FOLDER\n":
                PRIMO_folder = config_lines[index + 1].strip('\n')        
        
        if line == "# ORIGINAL OR REDUCED CT RESOLUTION\n":
                CT_RESOLUTION = config_lines[index + 1].strip('\n') 
        
        if line == "# SPLITTING FACTOR\n":
                SPLITTING_FACTOR = config_lines[index + 1].strip('\n')       

        if line == "# SEND TELEGRAM\n":
                SEND_TELEGRAM = config_lines[index + 1].strip('\n')
        if line == "# BOT TOKEN\n":
                BOT_TOKEN = config_lines[index + 1].strip('\n')
        if line == "# BOT CHATID\n":
                BOT_CHATID = config_lines[index + 1].strip('\n')
    
        if line == "# SOUND\n":
                SOUND = config_lines[index + 1].strip('\n')
  
    
    
    # log start program
    WriteToLog("-----------Starting Automate PRIMO simulations " + VERSION )
    
    WriteToLog("CONFIG.DOG read")
    WriteToLog("CT resolution used: " + CT_RESOLUTION)
    
    
    # read RP file to extract patient and plan IDs
    file_list = glob.glob(DICOM_import_folder + "/**/*.*", recursive = True)
    
    for filename in file_list:    
        if '\RP' in filename:
            plan_file = pydicom.dcmread(filename)
            break
    
    for filename in file_list:    
        if '\CT' in filename:    # reads the first CT file found
            image_file = pydicom.dcmread(filename)
            break
    # Checks if the images are from a virtual Eclipse phantom
    if hasattr(image_file, 'SeriesDescription') and image_file.SeriesDescription ==  "Generated empty phantom image set":
        IsPhantom = "YES"
        WriteToLog("Virtual phantom detected, by SeriesDescription")
    elif hasattr(image_file, 'KVP') and image_file.KVP == "":
        IsPhantom = "YES"
        WriteToLog("Virtual phantom detected, by KVP empty")
    elif hasattr(image_file, 'KVP') and image_file.KVP != "":
            IsPhantom = "NO"
            WriteToLog("Acquired CT detected, with kVp = " + \
                       str(image_file.KVP) + " kV")
    else:
        IsPhantom = "NO"      # default: no phantom
        WriteToLog("Assumed acquired CT (SeriesDescription or KVP not found")
    
    # Extracts patient and plan IDs (plan label, actually) from RP plan file
    patient_ID = plan_file.PatientID
    plan_ID = plan_file.RTPlanLabel
    print("Found plan", plan_ID, "from patient", patient_ID)
    WriteToLog("Found plan " + plan_ID + " from patient " + patient_ID)
    
    # remove "#" character, as PRIMO does not accept it
    if "#" in plan_ID:
        original_plan_ID = plan_ID    
        plan_ID = original_plan_ID.replace("#", "_")   
        print("Plan ID", original_plan_ID, "changed to ", plan_ID, "!")
        WriteToLog("WARNING! Plan ID " + original_plan_ID + " changed to " + plan_ID)
    
    if "#" in patient_ID:
        original_patient_ID = patient_ID    
        patient_ID = original_patient_ID.replace("#", "_")
        print("Patient ID", original_patient_ID, "changed to ", patient_ID, "!")
        WriteToLog("WARNING! Patient ID " + original_patient_ID + " changed to " + patient_ID)
    
    
    # remove " " in patient and plan IDs
    if " " in plan_ID:
        original_plan_ID = plan_ID    
        plan_ID = original_plan_ID.replace(" ", "_")   
        print("Plan ID", original_plan_ID, "changed to ", plan_ID, "!")
        WriteToLog("WARNING! Plan ID " + original_plan_ID + " changed to " + plan_ID)
                              
    if " " in patient_ID:
        original_patient_ID = patient_ID    
        patient_ID = original_patient_ID.replace(" ", "_")   
        print("Patient ID", original_patient_ID, "changed to ", patient_ID, "!")
        WriteToLog("WARNING! Patient ID " + original_patient_ID + " changed to " + patient_ID)


        
    
    # Extracts plan energy and MLC model from RP plan file
    # find the first treatment field in the beam sequence
    beam_seq = plan_file.BeamSequence     # sequence of beams in the plan file
    beam_index = -1
    for beam in beam_seq:
        beam_index = beam_index + 1
        if beam.TreatmentDeliveryType == "TREATMENT":   # found treatment field
            break
    
    
    # search for MLC positions in the treatment field located in the previous
    # lines of the code
    treatment_beam = plan_file.BeamSequence[beam_index]
    WriteToLog("MLC model and fluence mode taken from field " + \
               treatment_beam.BeamName)
    
    device_seq =  treatment_beam.BeamLimitingDeviceSequence[2]    # MLC
        
    leaf_boundaries = device_seq.LeafPositionBoundaries
    
    # Nominal beam energy, taken from the first control point
    control_point_seq = treatment_beam.ControlPointSequence[0] 
    energy = control_point_seq.NominalBeamEnergy
    
    # linac ID
    try:
        linac_ID = treatment_beam.TreatmentMachineName
    except:
        linac_ID = "UNKNOWN"
    WriteToLog("Linac ID found on the plan: " + linac_ID)
    
    # TPS
    # manufacturer = plan_file.Manufacturer   # Varian or Brainlab. Redundant
    try:
        TPS = plan_file.ManufacturerModelName     # TPS
    except:
        TPS = "UNKNOWN"
            
    try:
        TPS_version = plan_file.SoftwareVersions  # TPS version
    except:
        TPS_version = "UNKNOWN"
    
    if TPS == "ARIA RadOnc":
        TPS = "Eclipse"
    elif TPS == "VMATPlanning":
        TPS = "Elements Cranial SRS"
    elif TPS == "DosePlanning":
        TPS = "Elements (Cranial or MBM)"
    else:
        TPS = "UNKNOWN"
    
    if TPS == "UNKOWN":
        WriteToLog("WARNING: TPS unknown!")
    else:
        WriteToLog("Plan calculated with " + TPS)
    
    if TPS_version == "UNKNOWN":
        WriteToLog("WARNING: TPS version unknown!")
    else:
        WriteToLog("TPS version: " + TPS_version)
        
    
    # determines the plan technique (3DCRT, IMRT, VMAT, HyperArc, DCA)
    plan_technique = "UNKNOWN"
    
    if plan_file.ManufacturerModelName == "VMATPlanning":
        plan_technique = "VMAT"   # VMAT from Elements Cranial SRS
    elif plan_file.ManufacturerModelName == "DosePlanning":
        plan_technique = "VMAT or DCA"   # DCA from Elements MBM
    elif hasattr(plan_file, 'PatientSetupSequence[1].FixationDeviceSequence[0].Manufacturer'):
        if plan_file.PatientSetupSequence[1].FixationDeviceSequence[0].Manufacturer == 'QFix':
            plan_technique = "HA"   # HyperArc from Eclipse
    elif treatment_beam.BeamType == "STATIC":
        plan_technique = "3DCRT"   # 3DCRT
    elif treatment_beam.BeamType == "DYNAMIC" and treatment_beam.ControlPointSequence[0].GantryRotationDirection == 'NONE':
        plan_technique = "IMRT"   # IMRT from Eclipse
    elif TPS == "Eclipse" and treatment_beam.ControlPointSequence[0].GantryRotationDirection.isnumeric():
        plan_technique = "VMAT"   # VMAT from Eclipse
    elif TPS == "Eclipse" and treatment_beam.ControlPointSequence[0].GantryRotationDirection == "CW":
        plan_technique = "VMAT"   # VMAT from Eclipse
    elif TPS == "Eclipse" and treatment_beam.ControlPointSequence[0].GantryRotationDirection == "CCW":
        plan_technique = "VMAT"   # VMAT from Eclipse
    
    
    WriteToLog('Plan technique: ' + plan_technique)
  
    # Energy check. Only 6 MV (FF or FFF) is allowed in this version
    if str(energy) != "6":
        print("Energy found: " + str(energy) + ". Only 6 MV (FF or FFF) allowed!")
        print("Closing program")
        WriteToLog("ERROR: Energy found: " + energy + \
                   ". Only 6 MV (FF or FFF) allowed!")
        WriteToLog("Closing program")
        exit()
    else:
        WriteToLog("6 MV nominal energy (FF or FFF) found")
        
    fluence = treatment_beam.PrimaryFluenceModeSequence[0]
    fluence_mode = fluence.FluenceMode          # STANDARD OR NON-STANDARD
    try:
        fluence_ID = fluence.FluenceModeID          # FF or FFF
        WriteToLog("Fluence ID found in the plan: " + fluence_ID)
    except:
        WriteToLog("Fluence ID not found in the plan")
    
    if fluence_mode == "STANDARD":          # standard means FF beam
        PSF_path = PSF_path_6MV             # 6 MV
        energy = "6MV"
        WriteToLog("Found STANDARD fluence mode. 6 MV beam")
        WriteToLog("PSF: " + PSF_path)
    
    elif fluence_ID == "FFF":
        PSF_path = PSF_path_6MV_FFF         # 6 MV FFF
        energy = "6MV FFF"
        WriteToLog("PSF: " + PSF_path) 
    
    else:
        print ("\n Energy fluence mode unknown! Closing program")
        WriteToLog("ERROR: Energy fluence mode unknown! Closing program")
        time.sleep(10)
        exit()              # closes program
    
    
    # determines the leaf width of the central leaf to determine the MLC
    # used in the plan, assuming 60 leaves (valid both for Millennium 120 MLC
    # and for HD 120 MLC)
    central_leaf_width = leaf_boundaries[31]-leaf_boundaries[30]
    if central_leaf_width == 2.5:
        MLC_CODE = "400"     # PRIMO code for HD MLC (2.5 mm leaf width)
        WriteToLog("Found HD MLC in the plan")
    if central_leaf_width == 5:
        MLC_CODE = "300"     # PRIMO code for Millennium 120 MLC (5 mm width)
        WriteToLog("Found Millennium MLC 120 in the plan")
    
    
    for index, line in enumerate(config_lines):
        if line == "# HISTORIES (NUMBER OR FRACTION OF THE HISTORIES IN PSF)\n":
                HISTORIES = config_lines[index + 1].strip('\n')        

    if float(HISTORIES) <= 1:             # PSF factor
        FACTOR = float(HISTORIES)
        
        with open(PSF_path) as psf_header:
                  lines = psf_header.readlines()   # read lines of file
        for index, line in enumerate(lines):
            if line == "$ORIG_HISTORIES:\n":
                    PSF_HISTORIES = lines[index + 1].strip('\n').strip() 
                    HISTORIES = round(FACTOR * float(PSF_HISTORIES), 0)
                    HISTORIES = str(HISTORIES)

    WriteToLog('{:.0f}'.format(float(HISTORIES)) + \
               " histories will be simulated")


    # read PSF calibration factors
    if energy == "6MV":
        calibration_line = "# CALIBRATION FOR PSF 6 MV\n"
    if energy == "6MV FFF":
        calibration_line = "# CALIBRATION FOR PSF 6 MV FFF\n"
        
    for index, line in enumerate(config_lines):
        if line == calibration_line:
                MEAS_DOSE = config_lines[index + 2].strip('\n')        
                MU = config_lines[index + 3].strip('\n')
                CALC_DOSE = config_lines[index + 4].strip('\n')

    WriteToLog("PSF calibration. Measured dose = " + MEAS_DOSE + \
                " Gy, MU = " + MU + ", Simulated dose = " + CALC_DOSE + \
                " eV/(g hist)")

    
    # create folder to store the DICOM RT files for the current plan
    try:
        path = DICOM_RT_cases + '\\' + patient_ID + '_' + plan_ID
        os.mkdir(path)
    except OSError:
        print ("Folder %s already exists. Files will be overwritten!" % path)
        WriteToLog("WARNING: Folder %s already exists. Files will be overwritten!" % path)
    else:
        print ("Successfully created the folder %s \n" % path)
        WriteToLog("Successfully created the folder %s" % path)
   
    # move files from DICOM import folder to specific case folder
    for filename in file_list:
        if ".dcm" in filename:
            shutil.move(filename, 
                    os.path.join(DICOM_RT_cases + '\\' + patient_ID + '_' + \
                                 plan_ID, os.path.basename(filename)))
    
    
    # delete residual folders in DICOM import folder
    residual_files = glob.glob(DICOM_import_folder + "/*", recursive = True)
    if len(residual_files) > 0:
        for f in residual_files:
            try:
                os.remove(f)
            except:
                os.rmdir(f)
    
    
    # Create PRIMO macro
    macro_file = open(PRIMO_folder + '\Macros\\' + patient_ID + '_' + plan_ID + '.pma',
                      'w') # write mode
    macro_file.write("#--------------------------------------------------------------------\n")
    macro_file.write("#  PRIMO Macro v1.0\n")
    macro_file.write("#\n")
    macro_file.write("#  Macro: PRIMOMacro_DoseDPM_GammaPRIMO\n")
    macro_file.write("#  Purpose: To simulate segments s2 and s3 with DPM to tally a\n")
    macro_file.write("#  dose distribution and to perform gamma analysis with an external\n")
    macro_file.write("#  PRIMO formatted dose distribution \n")
    macro_file.write("#  Requirements: \n")
    macro_file.write("#    - An existing project with a linac set in an operational mode \n")
    macro_file.write("#    - A source PSF \n")
    macro_file.write("#    - A full set of DICOM files  (CT, Structures and Plan) in a \n")
    macro_file.write("#      DICOM repository \n")
    macro_file.write("#  Adjust to your requirements: \n")
    macro_file.write("#   - path of the DICOM repository \n")
    macro_file.write("#   - path and name of the source phase space file \n")
    macro_file.write("#   - simulation parameters  \n")
    macro_file.write("# \n")
    macro_file.write("#  last update: March, 2018 \n")
    macro_file.write("#  Macro created by Automate_PRIMO_simulations_"+ VERSION + " \n")
    macro_file.write("#  by Marcelino Hermida. January 2022 \n")
    macro_file.write("#--------------------------------------------------------------------\n")
    macro_file.write("\n")
    macro_file.write("# 0 - New project     " + patient_ID + '_' + plan_ID + "\n")
    macro_file.write("set.primo.repository \path=" + Simulations_folders + " \n")
    macro_file.write("new.project \id=" + patient_ID + "_" + plan_ID +
                     " \linac=6 \mode=2 \n")
    macro_file.write("# 1 - Link the psf:  modify the path to your own psf \n")
    macro_file.write("link.psf \path=" + PSF_path + " \n")
    macro_file.write("# 2- Set paths to repositories: \n")
    macro_file.write("set.dicom.repository \path=" + DICOM_RT_cases + "\\" +
                     patient_ID + '_' + plan_ID + "\n")
    macro_file.write("# 3 - Import the CT scan \n")
    if CT_RESOLUTION == "REDUCED":
        macro_file.write("import.ct " + "\\" + "reduce \n")
    if CT_RESOLUTION == "ORIGINAL":
        macro_file.write("import.ct \n")
    
    macro_file.write("# 4 - Import the structures (not mandatory) \n")
    macro_file.write("#      if the CT is a phantom made from structures use " + "\\" + "fillbody \n")
    
    # modifies macro according to the IsPhantom variable
    if IsPhantom == "YES":
        macro_file.write("import.structures " +"\\" + "airoutbody \segment \\fillbody \n")
    elif IsPhantom == "NO":
        macro_file.write("import.structures " +"\\" + "airoutbody \segment \n")    
    
    macro_file.write("# 5 - Import the plan: for a Varian 120 HD MLC use \mlc=400 \n")
    macro_file.write("import.plan \mlc=" + MLC_CODE + " \n")
    macro_file.write("# 6 - Config the simulation parameters for segments s2 and s3 \n")
    macro_file.write("config.simu  \seg=s2s3 \engine=dpm \seeds \histories=" + HISTORIES + " \n")
    macro_file.write("# 7 - Config variance reduction to splitting = 170 in the patient \n")
    macro_file.write("config.vr \split=" + SPLITTING_FACTOR + " \n")
    macro_file.write("# 8 - Do simulate with DPM\n")
    macro_file.write("simulate \n")
    macro_file.write("# 9 - Calibrate: Establish calibration factor to convert the dose to Gy \n")
    macro_file.write("#      Enter your own calibration parameters in the next command: \n")
    macro_file.write("calibrate \measured=" + MEAS_DOSE + " \mu=" + MU + " \calculated=" + CALC_DOSE + " \n")
    macro_file.write("# 10 - Gamma analysis inside body, default criteria, smoothing \n")
    macro_file.write("#        the reference 'project' dose \n")

    # gamma criteria 3%/1 mm, th=20%
    macro_file.write("gamma \deltadose=3.0 \dta=0.1 " +"\\" + "threshold=20 " + "\\" +
                     "unc=10 " +"\\" +"region=body " +"\\" + "extended " + "\\" +
                     "report \n")
    
    # gamma criteria 5%/1 mm, th=20%
    macro_file.write("gamma \deltadose=5.0 \dta=0.1 " +"\\" + "threshold=20 " + "\\" +
                     "unc=10 " +"\\" +"region=body " +"\\" + "extended " + "\\" +
                     "report \n")
    
    # gamma criteria 2%/2 mm., th=50%
    macro_file.write("gamma \deltadose=2.0 \dta=0.2 " +"\\" + "threshold=50 " + "\\" +
                     "unc=10 " +"\\" +"region=body " +"\\" + "extended " + "\\" +
                     "report \n")
    
    # gamma criteria 3%/3 mm., th=10% for standard plans
    macro_file.write("gamma \deltadose=3.0 \dta=0.3 " +"\\" + "threshold=10 " + "\\" +
                     "unc=10 " +"\\" +"region=body " +"\\" + "extended " + "\\" +
                     "report \n")
    
    macro_file.write("\n")
    macro_file.write("\n")
    macro_file.write("\n")
    macro_file.write("\n")
    macro_file.write("\n")
    macro_file.write("\n")
    macro_file.write("# end-of-macro -----------------------------------------------------\n")
    
    macro_file.close()
    
    print("\nPRIMO macro created \n")
    WriteToLog("PRIMO macro created: " + macro_file.name)
    
    MULTIPLE_GAMMA_ANALYSES = 4   # analysis with 3 criteria, to be used later.
                                  # This will improved in further versions
        
    # Checks if the simulation folder already exists. If it exists, it is
    # deleted
    patient_plan = patient_ID + '_' + plan_ID
    project_path = Path(os.path.join(Simulations_folders, patient_plan))
    if os.path.isdir(project_path):
        shutil.rmtree(project_path)
        print('Project folder already exists! It will be deleted and created again\n')
        WriteToLog('WARNING: Project folder already exists! It will be deleted and created again')
        if os.path.isdir(project_path) == True:
            time.sleep(3)      # pause of 3 s to allow the files to be deleted

    
    # Execute PRIMO with macro, as a background process
    # and takes care of the project name and the PID of the process
    PRIMO_proc = subprocess.Popen([PRIMO_folder + "\PRIMO.exe",
                      PRIMO_folder + "\kk\kk.ppj",
                      macro_file.name])
    
    print('Starting PRIMO... \n') 
    WriteToLog('Starting PRIMO with PID ' + str(PRIMO_proc.pid))
    WriteToLog("Using PRIMO default segmentation file")
              
     
    # Check PDF formation to be sure macro is finished
    simulation_folder = Simulations_folders + '\\' + patient_ID + '_' + plan_ID
    
    
    numPDFfiles = 0       # PDF files counter
    while numPDFfiles != MULTIPLE_GAMMA_ANALYSES:
        numPDFfiles = len(glob.glob1(simulation_folder,"*.pdf"))
        time.sleep(3)
    
    # list of PDF files
    PDF_file_list = glob.glob1(simulation_folder, "*.pdf")
    for file in PDF_file_list:
        filename = file.split('.pdf')[0]
        filename = filename + '.txt'     # the corresponding txt file
        filename_text = filename
        filename = os.path.join(simulation_folder, filename.split('.pdf')[0])
 
        with open(filename, encoding="UTF-8") as file_txt:
            lines = file_txt.readlines()   # read lines of file
            
            for index, line in enumerate(lines):
                if "DTA criterion" in line:
                    DTA = re.search("\d+\.\d+", line)[0]  #regexp for float
                    DTA = float(DTA)*10     # DTA in mm
                    DTA = str(DTA).replace('.0', '')
               
                if "Dose difference criterion" in line:
                    dose_dif = float(re.search("\d+\.\d+", line)[0])  #regexp for float
                    dose_dif = str(dose_dif).replace('.0', '')
                    
                    global_local = re.findall('\(.*?\)', line)[1]
                    global_local = global_local.replace('(', '').replace(')', '')
                
                if "Dose threshold" in line:
                    th = float(re.search("\d+\.\d+", line)[0])  #regexp for float
                    th = str(th).replace('.0', '')
           
        try:
            PDF_report = patient_ID + "_" + plan_ID + "_dose_report_" + \
                dose_dif + "_" + DTA + "_" + th + "_" + global_local + ".pdf"
            
            txt_report = patient_ID + "_" + plan_ID + "_dose_report_" + \
                dose_dif + "_" + DTA + "_" + th + "_" + global_local + ".txt"
                        
            # copy PDF with different name and delete original PDF (move)
            shutil.move(simulation_folder + "\\" + file,
                           simulation_folder + "\\" + PDF_report)
            
            
            # copy text file with different name and delete original text file
            # (move)
            shutil.move(simulation_folder + "\\" + filename_text,
                           simulation_folder + "\\" + txt_report)
            
            WriteToLog("Gamma analysis report ready: " + PDF_report)

        except:
            WriteToLog("ERROR: Problem found while renaming PDF report: " + file)

    # opens all gamma analyses PDF reports
    PDF_file_list = glob.glob1(simulation_folder, "*.pdf")
    for file in PDF_file_list:
        report = os.path.join(simulation_folder, file)
        # open PDF report as subprocess
        subprocess.Popen(report, shell=True)
        
    
    
    
    
    # POST-(SIMULATION AND GAMMA ANALYSES) TASKS
    
    file_list = os.listdir(simulation_folder)     # list of files in folder
    
    # search for simulation log file in the simulation folder
    string_program_ended = "Program ended on"
    for filename in file_list:    
        if filename.endswith("s3.log"):
                with open(simulation_folder + '\\' + filename) as s3_log:
                    lines = s3_log.readlines()   # read lines of log file
                  
                    # setting flag and index to 0
                    flag = 0
                    # Loop through the file line by line
                    for line in lines:  
                    # checking string is present in line or not
                        if string_program_ended in line:
                            flag = 1
                            break 
              
    # checking condition for string found or not
    if flag == 0: 
       print('Simulation did not end properly \n') 
       WriteToLog("ERROR: Simulation did not end properly")
    else: 
       print('Simulation ended succesfully! \n')
       WriteToLog("Simulation ended succesfully")
       
       
    
    # EXTRACT DATA FROM LOG AND TXT FILES.
    # ONCE EXTRACTED, SAVE THE DATA ON CSV FILE
    #
    ## DATA EXTRACTION
    from Analyze_simulation_results import Analyze_simulation_results
    Analyze_simulation_results(simulation_folder, linac_ID, TPS, TPS_version,
                               energy, plan_technique)


    
    # SEND RESULTS TO TELEGRAM BOT
    if SEND_TELEGRAM == "YES":

        try:
            project_name = patient_ID + "\_" + plan_ID
            message = ("Simulation of project " + project_name +
                                  " finished succesfully \n" +
                                  "\nPRIMO WatchDog " + VERSION +
                                  " wishes you a nice day! 👋 \n")
            telegram_bot_sendtext(message, BOT_TOKEN, BOT_CHATID)
            
            # send PDF reports
            file_list = os.listdir(simulation_folder)     # list of files in folder
            for filename in file_list:
                if filename.endswith("al.pdf"):     # global.pdf or local.pdf
                    caption = ''
                    telegram_bot_senddocument(simulation_folder, filename, caption,
                                              BOT_TOKEN, BOT_CHATID)
        
            print("Gamma analysis reports were sent via Telegram\n")
            # change again to the execution folder, as at this point we are
            # at the simulation folder
            os.chdir(execution_folder)
            WriteToLog("Gamma analysis reports were sent via Telegram")
     
        except ConnectionError:
            print("Connection with Telegram servers was not possible!\n")
            print("Gamma analysis reports are available at the project folder.\n")
            # change again to the execution folder, as at this point we are
            # at the simulation folder
            os.chdir(execution_folder)
            WriteToLog("ERROR: Connection with Telegram servers was not possible")
        
        except:
            print("Sending results via Telegram was not possible!\n")    
            print("Gamma analysis reports are available at the project folder.\n")
            # change again to the execution folder, as at this point we are
            # at the simulation folder
            os.chdir(execution_folder)
            WriteToLog("ERROR: Sending results via Telegram was not possible")
     
    else:
        print("Gamma analysis reports are available at the project folder.\n")
        
        
    # closing PRIMO
    try:
        os.system("taskkill /pid " + str(PRIMO_proc.pid))   # closing PRIMO by PID
        print("Closed PRIMO with PID " + str(PRIMO_proc.pid))
        WriteToLog("Closed PRIMO with PID " + str(PRIMO_proc.pid))
    except:
        print("PRIMO with PID " + str(PRIMO_proc.pid) + " could not be closed!")
        WriteToLog("WARNING: PRIMO with PID " + str(PRIMO_proc.pid) + " could not be closed!")
     
    
    # Warning sound of end of simulation + analysis
    def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    if SOUND == 'YES':
        try:
            winsound.PlaySound(resource_path("dog-bark.wav"),
                               winsound.SND_FILENAME)
        except:
            WriteToLog('Sound failed!')
    
        
       
    # The End
    print('\n Have a nice day! \n') 


