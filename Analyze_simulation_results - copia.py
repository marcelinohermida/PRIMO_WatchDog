# -*- coding: utf-8 -*-
"""
Analyze_simulation_results


v1.09_para_GitHub: no new features, except adding a fourth gamma criteria:
                   3%/3mm, th=10%. Simplifications to publish in Github.
                   Quiron edition removed. MH. 8/10/23.

v1.09: no changes respect to 1.08. 1/11/22. MH.

v1.08: no changes respect to 1.07. 23/2/22. MH.

v1.07: a bug was introduced in v1.05: when the original txt files were deleted,
       the format of the only txt files remaining was "_dose_report" instead
       of the original "-dose_report-". As a consequence, the text files were
       not analyzed. Corrected in this version. 15/2/22. MH.

v1.06: no changes respect to 1.05. MH

v1.05: Include plan_technique as input parameter. MH. 29/1/22. MH.

v1.04: add new input parameter: energy. Taken from the RP file. 22/1/22. MH.

v1.03: add new input parameters: linac_ID, TPS, and TPS_version. Taken from
       the RP file. 22/1/22. MH.

v1.02: Implements recursive watchdog. 29-12-21.

v 1.01: try to implement simulations queue.

v 1.00

Created on Wed Dec  8 17:29:11 2021


@author: Marce
"""


def Analyze_simulation_results(simulation_folder, linac_ID, TPS, TPS_version,
                               energy, plan_technique):

    # script version
    VERSION = "v. 1.09 Github"
    
    # IMPORTS
    import os
    import time
    from write_to_log import write_to_log
    import csv
    import re                    # regular expressions
    import glob
    
    # MAX NUMBER OF STRUCTURES IN THE GAMMA ANALYSIS FILE
    MAX_NUM_STRUCTURES = 30
    
    # log start program
    write_to_log("Starting extraction of simulation results " + VERSION)
    
    
    # ANALYSIS OF .LOG FILE
    file_list = os.listdir(simulation_folder)     # list of files in folder
    for filename in file_list:    
        if filename.endswith('.log'):
            log_file = simulation_folder + "\\" + filename  # path added
            
            break
    write_to_log("Starting analysis of " + log_file + " file")
    
    with open(log_file) as log_file:
              lines = log_file.readlines()   # read lines of file
              
    for index, line in enumerate(lines):
        if line.startswith(' PRIMO version'):
                PRIMO_version = lines[index].strip('\n')
                PRIMO_version = PRIMO_version.rsplit(' ', 1)[1]
        
        if line.startswith(' Project Id'):
                project_id = lines[index].strip('\n')
                project_id = project_id.rsplit(' ', 1)[1]
               
        if line.startswith('  - Number of Processors:'):
                processors = lines[index].strip('\n')
                processors = processors.rsplit(' ', 1)[1]

        if line.startswith('  - Speed (GHz):'):
                proc_speed_GHz = lines[index].strip('\n')
                proc_speed_GHz = proc_speed_GHz.rsplit(' ', 1)[1]
                
        if line.startswith(' Simulation engine: Dose Planning Method (DPM)'):
                engine = "DPM"

        if line.startswith(' Simulation engine: PENELOPE'):
                engine = "PENELOPE"
        
        if line.startswith('MLC (code,leaves):'):
                MLC_code = lines[index+1].strip('\n')
                MLC_code = MLC_code.rsplit(' ', 1)[0]
                if MLC_code == '400':
                    MLC_model = 'HD' 
                elif MLC_code == '300':
                    MLC_model = 'Millennium 120'
                else:
                    MLC_model = 'MLC unknown'
         
        if line.startswith(' Simulation started '):
                start_datetime = lines[index].strip('\n')
                start_time = start_datetime.rsplit(' at ', 1)[1]       
                start_date = start_datetime.rsplit(' at ', 1)[0]       
                start_date = start_date.rsplit(' ', 1)[1]       
                start_datetime = start_date + ' ' + start_time
        
        if line.startswith('No of histories:'):
                histories = lines[index+1].strip('\n').strip()
                
        if line.startswith('PSF filename (set to - for none):'):
                PSF = lines[index+1].strip('\n')

        if line.startswith('Splitting factor in the voxelized geometry:'):
                splitting_factor = lines[index+1].strip('\n')
         
        if line.startswith(' [SECTION VOXELS HEADER'):
                voxel_sizes = lines[index+3].strip('\n').strip().split()
                voxel_size_x_mm = float(voxel_sizes[0])*10      # size in mm
                voxel_size_y_mm = float(voxel_sizes[1])*10      # size in mm
                voxel_size_z_mm = float(voxel_sizes[2])*10      # size in mm
        
        if line.startswith('#   CPU time [t] (s):'):
                cpu_time_s = float(lines[index+1].strip('\n').rsplit(' ',
                                   1)[1])
      
        if line.startswith('#   Speed (histories/s):'):
                speed_hist_s = float(lines[index+1].strip('\n').rsplit(' ',
                                     1)[1])
                
        if line.startswith('#   Average uncertainty (above 1/2 max score)'):
              avg_uncert_percent = float(lines[index+1].strip('\n').rsplit(' ',
                                         1)[1])
               
        if line.startswith('#   Intrinsic efficiency [N*uncert^2]^-1:'):
              int_efficiency = lines[index+1].strip('\n').rsplit(' ', 1)[1]
        
        if line.startswith('#   Absolute efficiency [t*uncert^2]^-1:'):
              abs_efficiency = lines[index+1].strip('\n').rsplit(' ', 1)[1]
        
    write_to_log("Data extraction from " + log_file.name + " completed")
    
    
    
    
    
    # ANALYSIS OF .RTF FILE (LOG OF THE PRIMO MACRO, GAMMA INDEX ANALYSES, ETC)
    for filename in file_list:    
        if filename.endswith('.rtf'):
            rtf_file = simulation_folder + "\\" + filename  # path added
            
            break
    write_to_log("Starting analysis of " + rtf_file + " file")
    
    with open(rtf_file) as rtf_file:
              lines = rtf_file.readlines()   # read lines of file
              
    for index, line in enumerate(lines):
        if 'Coarse simulation' in line:
                coarse_simulation = lines[index].strip('\n')
                coarse_simulation = coarse_simulation.rsplit(' ', 1)[1]
                coarse_simulation = coarse_simulation.rsplit('\par')
                coarse_simulation = coarse_simulation[0]
    
        if 'Control points' in line:
                control_points = lines[index].strip('\n')
                control_points = control_points.rsplit(' ', 1)[1]
                control_points = control_points.rsplit('/')
                control_points = control_points[0]
    
    data_row = [project_id, VERSION, PRIMO_version, processors, proc_speed_GHz, engine,
             start_datetime, histories, linac_ID, TPS, TPS_version, energy,
             plan_technique, PSF, MLC_model, splitting_factor,
             voxel_size_x_mm, voxel_size_y_mm, voxel_size_z_mm, cpu_time_s,
             speed_hist_s, avg_uncert_percent, int_efficiency, abs_efficiency,
             coarse_simulation, control_points]
    
    write_to_log('Data extraction from ' + filename + ' completed')
    
    
    # ANALYSIS OF TEXT FILES WITH GAMMA ANALYSIS RESULTS
    # Data extraction from text files with gamma analysis result
    text_file_list = glob.glob1(simulation_folder, "*_dose_report_*.txt")
    
    all_analysis_row = []       # list to store structure name and GPR of all files
    
    for text_file in text_file_list:
        data_structs = []  # list to store structure name and GPR of each file
        text_file = os.path.join(simulation_folder, text_file)
        with open(text_file) as txt_file:
                  lines = txt_file.readlines()   # read lines of file
        
        for index, line in enumerate(lines):
            if line.startswith("Results of gamma analysis:"):
            
                dose_dif = float(re.search("\d+\.\d+", lines[index+1])[0])  #regexp for float
                dose_dif = str(dose_dif).replace('.0', '')
                
                global_local = re.findall('\(.*?\)', lines[index+1])[1]
                global_local = global_local.replace('(', '').replace(')', '')
            
                DTA = re.search("\d+\.\d+", lines[index+2])[0]  #regexp for float
                DTA = float(DTA)*10     # DTA in mm
                DTA = str(DTA).replace('.0', '')
                
                th = float(re.search("\d+\.\d+", lines[index+3])[0])  #regexp for float
                th = str(th).replace('.0', '')
                
                region = lines[index+5].strip()
                region = region.split('Region: ', 1)[1]
            
                total_GPR = float(re.search("\d+\.\d+", lines[index+8])[0])
            
            # read name and GPR of structures. Only taken into account the
            # structures with GPR calculated (i.e. with dose > threshold)
            if line.startswith("REGION"):
                struct_count = 0
                while 1:        ## executes until a break is found
                    try:
                        struct = lines[index+2+struct_count].strip().split('   ')
                    except:
                        break
                    struct_name = struct[0]
                    if struct_name == '':
                        break
                    try:   # only considers structures with GPR
                        struct_GPR = float(struct[-1])
                        data_structs =  data_structs + [struct_name, struct_GPR]
                    except:
                        struct_GPR = ''
                    
                    struct_count = struct_count + 1
        
        write_to_log('Data extraction from ' + text_file + ' completed')
            
        
        num_structs = int(len(data_structs)/2)  # num structures found in the file
        for i in range (num_structs+1, MAX_NUM_STRUCTURES + 1):
            data_structs = data_structs + ['', '']   # add empty values
                
        all_analysis_row = all_analysis_row + \
            [dose_dif, DTA, global_local, th, region, total_GPR] + \
            data_structs
       

    data_row = data_row + all_analysis_row    # added structure name and GPR
    
    
    
    
    
    # SAVE TO CSV FILE
    # Check if the CSV file already exists in the .exe folder
    if not(os.path.isfile('PRIMO_simulation_results.csv')):
    
        header = ['project_id', 'watchdog_version', 'PRIMO_version',
                  'processors', 'proc_speed_GHz', 'engine', 'start_datetime',
                  'histories', 'linac_ID', 'TPS', 'TPS_version', 'energy',
                  'plan_technique', 'PSF', 'MLC', 'splitting_factor',
                  'voxel_size_x_mm', 'voxel_size_y_mm', 'voxel_size_z_mm',
                  'cpu_time_s', 'speed_hist_s', 'avg_uncert_percent',
                  'int_efficiency', 'abs_efficiency', 'coarse_simulation',
                  'control_points']
    
    
        for i in range(0, len(text_file_list)):    # add gamma analysis header
           header = header + ["gamma_analysis_" + str(i+1) + "_dose_percent",
                              "gamma_analysis_" + str(i+1) + "_DTA_mm",
                              "gamma_analysis_" + str(i+1) + "_type",
                              "gamma_analysis_" + str(i+1) + "_th",
                              "gamma_analysis_" + str(i+1) + "_region",
                              "gamma_analysis_" + str(i+1) + "_total_GPR"]
           
           # add variable names for structure names and GPRs
           for j in range(0, MAX_NUM_STRUCTURES):
               header = header + ["gamma_analysis_" + str(i+1) + \
                                      "_structure_" + str(j+1) + "_name",
                                  "gamma_analysis_" + str(i+1) + \
                                      "_structure_" + str(j+1) + "_GPR"]

        try:        
            with open('PRIMO_simulation_results.csv', 'w', encoding='UTF8',
                newline='') as csv_file:
                writer = csv.writer(csv_file)
        
                # write the header
                writer.writerow(header)

        except PermissionError:  # can happen if file is used by another process  
            time.sleep(3)         # wait 3 s for the file
            with open('PRIMO_simulation_results.csv', 'w', encoding='UTF8',
                newline='') as csv_file:
                writer = csv.writer(csv_file)
        
                # write the header
                writer.writerow(header)
        
        except:
             write_to_log('ERROR: Header could not be written to csv file')
    
    # open csv to save data
    try:
        with open('PRIMO_simulation_results.csv', 'a', encoding='UTF8',
              newline='') as csv_file:
            writer = csv.writer(csv_file)
    
            # write the data
            writer.writerow(data_row)
            write_to_log('Results saved to PRIMO_simulation_results.csv')

    except PermissionError:  # can happen if file is used by another process
        time.sleep(3)         # wait 3 s for the file
        
        with open('PRIMO_simulation_results.csv', 'a', encoding='UTF8',
              newline='') as csv_file:
            writer = csv.writer(csv_file)
    
            # write the data
            writer.writerow(data_row)
            write_to_log('Results saved to PRIMO_simulation_results.csv')
        
    except:
         write_to_log('ERROR: Results could not be saved to PRIMO_simulation_results.csv!')

    
    
    