# -*- coding: utf-8 -*-
"""
analyze_simulation_results


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

# IMPORTS
import os
import time
import csv
import re   # regular expressions
import glob
from write_to_log import write_to_log

# script version
VERSION = "v. 1.09 Github"

# MAX NUMBER OF STRUCTURES IN THE GAMMA ANALYSIS FILE
MAX_NUM_STRUCTURES = 30


def analyze_simulation_results(simulation_folder, linac_ID, TPS, TPS_version,
                               energy, plan_technique):

    # log start program
    write_to_log(f"Starting extraction of simulation results {VERSION}")
        
    # ANALYSIS OF .LOG FILE
    data_log = analyze_log_file(simulation_folder)
  
    
    # Analyzes and extracts data from RTF simulation file and
    # stores the data in a data_row
    data_row = analyze_rtf_file(simulation_folder,
                                data_log['project_id'], VERSION,
                                data_log['PRIMO_version'],
                                data_log['processors'],
                                data_log['proc_speed_GHz'],
                                data_log['engine'], data_log['start_datetime'],
                                data_log['histories'], linac_ID,
                                TPS, TPS_version, energy, plan_technique,
                                data_log['PSF'], data_log['MLC_model'],
                                data_log['splitting_factor'],
                                data_log['voxel_size_x_mm'],
                                data_log['voxel_size_y_mm'],
                                data_log['voxel_size_z_mm'],
                                data_log['cpu_time_s'],
                                data_log['speed_hist_s'],
                                data_log['avg_uncert_percent'],
                                data_log['int_efficiency'],
                                data_log['abs_efficiency'])

        
        
    # List of the text files with the gamma analysis results
    text_file_list = glob.glob1(simulation_folder, "*_dose_report_*.txt")
    
    # Extracts data from the text files with gamma analysis results
    updated_data_row = extract_gamma_analysis_data(text_file_list,
                                                   simulation_folder,
                                                   MAX_NUM_STRUCTURES,
                                                   data_row)

    
    # Saves simulation results and gamma analysis to a CSV file
    save_simulation_results_to_csv(text_file_list, MAX_NUM_STRUCTURES,
                                   updated_data_row)
    








def analyze_log_file(simulation_folder):
    file_list = os.listdir(simulation_folder)
    
    log_file_path = None
    for filename in file_list:
        if filename.endswith('.log'):
            log_file_path = os.path.join(simulation_folder, filename)
            break

    if not log_file_path:
        return

    write_to_log(f"Starting analysis of {log_file_path} file")

    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    data = {}
    for index, line in enumerate(lines):
        if line.startswith(' PRIMO version'):
            data['PRIMO_version'] = line.strip('\n').rsplit(' ', 1)[1]
        elif line.startswith(' Project Id'):
            data['project_id'] = line.strip('\n').rsplit(' ', 1)[1]
        elif line.startswith('  - Number of Processors:'):
            data['processors'] = line.strip('\n').rsplit(' ', 1)[1]
        elif line.startswith('  - Speed (GHz):'):
            data['proc_speed_GHz'] = line.strip('\n').rsplit(' ', 1)[1]
        elif line.startswith(' Simulation engine: Dose Planning Method (DPM)'):
            data['engine'] = "DPM"
        elif line.startswith(' Simulation engine: PENELOPE'):
            data['engine'] = "PENELOPE"
        elif line.startswith('MLC (code,leaves):'):
            MLC_code = lines[index+1].strip('\n').rsplit(' ', 1)[0]
            data['MLC_model'] = {
                '400': 'HD',
                '300': 'Millennium 120'
            }.get(MLC_code, 'MLC unknown')
        elif line.startswith(' Simulation started '):
            start_datetime_parts = line.strip('\n').rsplit(' at ', 1)
            data['start_datetime'] = f"{start_datetime_parts[0].rsplit(' ', 1)[1]} {start_datetime_parts[1]}"
        elif line.startswith('No of histories:'):
            data['histories'] = lines[index+1].strip('\n').strip()
        elif line.startswith('PSF filename (set to - for none):'):
            data['PSF'] = lines[index+1].strip('\n')
        elif line.startswith('Splitting factor in the voxelized geometry:'):
            data['splitting_factor'] = lines[index+1].strip('\n')
        elif line.startswith(' [SECTION VOXELS HEADER'):
            voxel_sizes = lines[index+3].strip('\n').strip().split()
            data['voxel_size_x_mm'] = float(voxel_sizes[0]) * 10
            data['voxel_size_y_mm'] = float(voxel_sizes[1]) * 10
            data['voxel_size_z_mm'] = float(voxel_sizes[2]) * 10
        elif line.startswith('#   CPU time [t] (s):'):
            data['cpu_time_s'] = float(lines[index+1].strip('\n').rsplit(' ', 1)[1])
        elif line.startswith('#   Speed (histories/s):'):
            data['speed_hist_s'] = float(lines[index+1].strip('\n').rsplit(' ', 1)[1])
        elif line.startswith('#   Average uncertainty (above 1/2 max score)'):
            data['avg_uncert_percent'] = float(lines[index+1].strip('\n').rsplit(' ', 1)[1])
        elif line.startswith('#   Intrinsic efficiency [N*uncert^2]^-1:'):
            data['int_efficiency'] = lines[index+1].strip('\n').rsplit(' ', 1)[1]
        elif line.startswith('#   Absolute efficiency [t*uncert^2]^-1:'):
            data['abs_efficiency'] = lines[index+1].strip('\n').rsplit(' ', 1)[1]

    write_to_log(f"Data extraction from {log_file_path} completed")

    return data








def analyze_rtf_file(simulation_folder, project_id, VERSION,
                     PRIMO_version, processors, proc_speed_GHz, engine,
                     start_datetime, histories, linac_ID, TPS, TPS_version,
                     energy, plan_technique, PSF, MLC_model, splitting_factor,
                     voxel_size_x_mm, voxel_size_y_mm, voxel_size_z_mm,
                     cpu_time_s, speed_hist_s, avg_uncert_percent,
                     int_efficiency, abs_efficiency):
    """Analyze the .RTF file and extract relevant data."""
    
    file_list = os.listdir(simulation_folder)     # list of files in folder
    # Find the .rtf file in the file list
    rtf_file = next((os.path.join(simulation_folder,filename) for filename \
                     in file_list if filename.endswith('.rtf')), None)
    
    if not rtf_file:
        write_to_log("No .rtf file found in the provided file list.")
        return []

    write_to_log(f"Starting analysis of {rtf_file} file")
    
    with open(rtf_file, 'r') as file:
        lines = file.readlines()

    coarse_simulation = ""
    control_points = ""
    
    for index, line in enumerate(lines):
        if 'Coarse simulation' in line:
            coarse_simulation = line.strip('\n').rsplit(' ',
                                          1)[1].rsplit('\par')[0]
        if 'Control points' in line:
            control_points = line.strip('\n').rsplit(' ', 1)[1].rsplit('/')[0]

    data_row = [project_id, VERSION, PRIMO_version, processors,
                proc_speed_GHz, engine, start_datetime, histories, linac_ID,
                TPS, TPS_version, energy, plan_technique, PSF, MLC_model,
                splitting_factor, voxel_size_x_mm, voxel_size_y_mm,
                voxel_size_z_mm, cpu_time_s, speed_hist_s, avg_uncert_percent,
                int_efficiency, abs_efficiency, coarse_simulation,
                control_points]
    
    write_to_log(f"Data extraction from {rtf_file} completed")
    
    return data_row









def extract_gamma_analysis_data(text_file_list, simulation_folder,
                                MAX_NUM_STRUCTURES, data_row):
    """Extract gamma analysis data from text files and update the data row."""
    
    all_analysis_row = []
    
    for text_file in text_file_list:
        data_structs = []  # list to store structure name and GPR of each file
        text_file_path = os.path.join(simulation_folder, text_file)
        
        with open(text_file_path) as txt_file:
            lines = txt_file.readlines()   # read lines of file
        
        for index, line in enumerate(lines):
            if line.startswith("Results of gamma analysis:"):
                dose_dif = float(re.search("\d+\.\d+", lines[index+1])[0])
                dose_dif = str(dose_dif).replace('.0', '')
                global_local = re.findall('\(.*?\)', lines[index+1])[1]
                global_local = global_local.replace('(', '').replace(')', '')
                DTA = re.search("\d+\.\d+", lines[index+2])[0]
                DTA = str(float(DTA)*10).replace('.0', '')
                th = str(float(re.search("\d+\.\d+",
                                         lines[index+3])[0])).replace('.0', '')
                region = lines[index+5].strip().split('Region: ', 1)[1]
                total_GPR = float(re.search("\d+\.\d+", lines[index+8])[0])
            
            if line.startswith("REGION"):
                struct_count = 0
                while True:
                    try:
                        struct = lines[index+2+struct_count].strip().split('   ')
                    except:
                        break
                    struct_name = struct[0]
                    if struct_name == '':
                        break
                    try:
                        struct_GPR = float(struct[-1])
                        data_structs.extend([struct_name, struct_GPR])
                    except:
                        pass
                    struct_count += 1
        
        write_to_log(f'Data extraction from {text_file_path} completed')
        
        num_structs = len(data_structs) // 2
        data_structs.extend(['', ''] * (MAX_NUM_STRUCTURES - num_structs))
        
        all_analysis_row.extend([dose_dif, DTA, global_local, th, region,
                                 total_GPR] + data_structs)
    
    data_row.extend(all_analysis_row)
    return data_row




def save_simulation_results_to_csv(text_file_list, MAX_NUM_STRUCTURES,
                                   data_row):
    """Save the extracted data to a CSV file."""
    
    # Check if the CSV file already exists in the .exe folder
    if not os.path.isfile('PRIMO_simulation_results.csv'):
        header = [
            'project_id', 'watchdog_version', 'PRIMO_version',
            'processors', 'proc_speed_GHz', 'engine', 'start_datetime',
            'histories', 'linac_ID', 'TPS', 'TPS_version', 'energy',
            'plan_technique', 'PSF', 'MLC', 'splitting_factor',
            'voxel_size_x_mm', 'voxel_size_y_mm', 'voxel_size_z_mm',
            'cpu_time_s', 'speed_hist_s', 'avg_uncert_percent',
            'int_efficiency', 'abs_efficiency', 'coarse_simulation',
            'control_points'
        ]

        for i in range(len(text_file_list)):
            header.extend([
                f"gamma_analysis_{i+1}_dose_percent",
                f"gamma_analysis_{i+1}_DTA_mm",
                f"gamma_analysis_{i+1}_type",
                f"gamma_analysis_{i+1}_th",
                f"gamma_analysis_{i+1}_region",
                f"gamma_analysis_{i+1}_total_GPR"
            ])
            
            for j in range(MAX_NUM_STRUCTURES):
                header.extend([
                    f"gamma_analysis_{i+1}_structure_{j+1}_name",
                    f"gamma_analysis_{i+1}_structure_{j+1}_GPR"
                ])

        try:
            with open('PRIMO_simulation_results.csv', 'w', encoding='UTF8', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(header)
        except PermissionError:
            time.sleep(3)
            with open('PRIMO_simulation_results.csv', 'w', encoding='UTF8', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(header)
        except:
            write_to_log('ERROR: Header could not be written to csv file')

    try:
        with open('PRIMO_simulation_results.csv', 'a', encoding='UTF8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(data_row)
            write_to_log('Results saved to PRIMO_simulation_results.csv')
    except PermissionError:
        time.sleep(3)
        with open('PRIMO_simulation_results.csv', 'a', encoding='UTF8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(data_row)
            write_to_log('Results saved to PRIMO_simulation_results.csv')
    except:
        write_to_log(f"ERROR: Results could not be saved to PRIMO_simulation_results.csv!")








