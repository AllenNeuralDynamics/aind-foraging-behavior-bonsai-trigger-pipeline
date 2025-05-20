'''
Automatic pipeline for behavioral ingestion
1. Copy bonsai sessions from all rigs
2. Convert bonsai .json to .nwb
3. Upload bonsai sessions to AWS
'''

import subprocess
import sys
import logging
import glob
import os
import json
import multiprocessing as mp
import shutil
import smartsheet
import pandas as pd

from foraging_gui.TransferToNWB import bonsai_to_nwb
from raw_data_inventory import get_raw_behavior_sessions_from_multiple_places
from util import reformat_PI_names

import warnings
warnings.simplefilter('ignore', FutureWarning)

# Load passcode
with open(os.path.dirname(os.path.abspath(__file__)) + '\passcode.json') as f:
    passcode = json.load(f)

#%%
def get_passcode(rigs):
    ''' Get passcode for remote PCs from json
    '''
    for rig in rigs:
        if 'user_name' in rig:
            rig['passcode'] = passcode[rig['remote'].split('\\\\')[1].split('\\')[0]]

#=============================   Change me!!! ===============================
# Address of remote training rig PCs
# Solve connection bugs: https://stackoverflow.com/questions/24933661/multiple-connections-to-a-server-or-shared-resource-by-the-same-user-using-more

# -- Load standardized rigs --
with open(os.path.dirname(os.path.abspath(__file__)) + R'\rig_mapper.json') as f:
    rig_mapper = json.load(f)

rigs = []
for pc, boxes in rig_mapper.items():
    for box in boxes:
        rigs.append(
            {
                'local': f'AIND-{box}',
                'remote': fR'\\{pc}\behavior_data\{box}',
                'user_name': 'svc_aind_behavior',
            }
        )

# -- Append non-standardized rigs --
rigs.extend(
    [
        # Ephys rigs
        {'local': fR'323_EPHYS_1', 
        'remote': fR'\\W10DT713669\behavior_data\323_EPHYS1', 
        'user_name': 'svc_aind_ephys',
        },
        
        {'local': fR'323_EPHYS_1', 
         'remote': fR'\\allen\aind\scratch\ephys_rig_behavior_transfer\323_EPHYS1', 
        },
        
        {'local': fR'323_EPHYS_3', 
        'remote': fR'\\allen\aind\scratch\ephys_rig_behavior_transfer\323_EPHYS3', 
        },
        
        {'local': fR'323_EPHYS_3',
         'remote': fR'\\W10DT713883\behavior_data',
         'user_name': 'svc_aind_ephys',
        },
        
        {'local': fR'322_EPHYS_4',
         'remote': fR'\\W10DT714670\dynamic-foraging\322_EPHYS4',
         'user_name': 'svc_aind_ephys',}
    ]
)

get_passcode(rigs)

#%%

# Root path to place bonsai sessions
behavioral_root = R'C:\han_temp_pipeline'
to_exclude_folders = (  # Exclude these folders from syncing
    f'"0000" "test" "EphysFolder" "HarpFolder" "PhotometryFolder" "VideoFolder" '
    f'"raw.harp" "behavior-videos" "ecephys" "fib" "metadata-dir"'   # Exclud folders in the new file structure
)

to_exclude_files = (  # Exclude these files from syncing
    f'"finished" '
)


# Pipeline log
pipeline_log = R'C:\han_temp_pipeline\nwb\bonsai_pipeline.log'  # Simplified log for this code
#==========================================================================

logging.basicConfig(# filename=pipeline_log, 
                    level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s [%(funcName)s]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    #filemode='a',
                    handlers=[logging.StreamHandler(), logging.FileHandler(pipeline_log)])

log = logging.getLogger(__name__)


def sync_behavioral_folders():
    
    subprocess.Popen('net use * /delete /yes', shell=True).wait()  # Disconnect all network drives
    
    for rig in rigs:
        summary_start = False
        
        if 'user_name' in rig:  # If remote needs user_name and passcode to log in
            cmd_net_use = fR'''net use {rig['remote']} /u:{rig['user_name']} {rig['passcode']} &&'''
        else:
            cmd_net_use = ''
        
        command = (
            cmd_net_use +
            fR'''robocopy  {rig['remote']} {behavioral_root}\{rig['local']} '''
            fR'''/e /xx /XD {to_exclude_folders} /XF {to_exclude_files} '''
            fR'''/xj /xjd /mt /np /Z /W:1 /R:5 /tee /MAXAGE:20241001'''
        )
                #   fR'''net use {rig['remote']} /d /y'''         
                   ##fR'''net use {rig['remote']} /u:{rig['user_name']} {rig['passcode']}&&'''\          
                
        log.info('')
        log.info(f'''===== Sync "{rig['local']}" from {rig['remote']} ===== ''')
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True,
                                universal_newlines=True  # Output to console
                                )
        
        # Show progress in the console
        for line in proc.stdout:
            sys.stdout.write(line)  # All output to console
            if 'Total' in line:     # Only summary part to log file
                summary_start = True
                log.info('')
            if summary_start:
                log.info(line.rstrip('\n'))
       
        exitcode = proc.wait() # Essential for robocopy
        log.info(f'Done with exitcode = {exitcode}\n')
        
def convert_one_json_to_nwb(filepath, nwb_dir):
    filename = os.path.basename(filepath)
    nwb_filename = filename.replace('.json', '.nwb')

    # Skip if name start with 0
    if filename.startswith('0'):
        #log.info(f'Skipped {filename}: file name start with 0')
        return 'mouse_id_start_with_0'
    
    # Skip if name include "behavior_session_model"
    if 'behavior_session_model' in filename:
        # log.info(f'Skipped {filename}: file name include "behavior_session_model"')
        return 'behavior_session_model_in_json_name'
    
    # Check if corresponding .nwb file exists
    if not os.path.exists(os.path.join(nwb_dir, nwb_filename)):
        try:
            # Convert .json to .nwb
            nwb_result = bonsai_to_nwb(filepath, nwb_dir)
            return nwb_result  # empty_trials, incomplete_json, success
        except Exception as e:
            log.error(f'Error converting {filename} to .nwb: {str(e)}')
            return 'uncaught_error'
    else:
        return 'exists'

        
def batch_convert_json_to_nwb(json_dir, nwb_dir):
    os.makedirs(nwb_dir, exist_ok=True)
    
    # Start a multiprocessing pool, and use the pool to convert all .json files to .nwb
    with mp.Pool(processes=mp.cpu_count()-1) as pool:
        jobs = [pool.apply_async(convert_one_json_to_nwb, (filepath, nwb_dir)) 
                for filepath in glob.iglob(json_dir + '/**/*.json', recursive=True)]
        results = [job.get() for job in jobs]
        
    log.info(f'\nProcessed {len(results)} files: '
             f'{results.count("success")} successfully converted; '             
             f'{results.count("exists")} already exists, '
             f'{results.count("mouse_id_start_with_0")} mouse_id_start_with_0, '
             f'{results.count("empty_trials")} empty_trials, '
             f'{results.count("incomplete_json")} incomplete_json, '
             f'{results.count("behavior_session_model_in_json_name")} behavior_session_model_in_json_name, '
             f'{results.count("uncaught_error")} uncaught error\n\n')
    

def upload_directory_to_s3(source_dir, s3_bucket, method='sync'):
    log.info(f'Uploading {source_dir} to s3://{s3_bucket}/')
    # Create the AWS CLI command
    aws_cli_command = [R'C:\Program Files\Amazon\AWSCLIV2\aws', 's3', method, source_dir, f's3://{s3_bucket}/']

    # Execute the AWS CLI command
    subprocess.run(aws_cli_command, check=True)
    
def fetch_schedule_and_past_mice():
    '''
    Fetch current experiment schedule from AIND scratch, where Alex's code downloads from the smartsheet
    https://github.com/AllenNeuralDynamics/behavior_communication/blob/main/schedule/download_schedule.py
    (because I don't have the access to the sheet_id of the current schedule for now)
    
    and fetch past mice metadata directly from smartsheet
    '''
    # --- Copy current schedule ---
    try:
        shutil.copy(R"\\allen\aind\scratch\dynamic_foraging\DynamicForagingSchedule.csv",
                    behavioral_root + R"\nwb\schedule_current.csv"
                    )
        log.info('Copy schedule successfully!')
    except Exception as e:
        log.warning(f'Error fetching schedule: {str(e)}')
        
    # --- Download past mice metadata ---
    try:
        sheet_ID = 5745380507471748   # past mice in behavior
        download_folder = behavioral_root + R"\nwb"
        filename = 'schedule_past_mice.csv'

        smart = smartsheet.Smartsheet(access_token=passcode["smart_sheet_token"])
        smart.Sheets.get_sheet_as_csv(
            sheet_ID,
            download_path=download_folder,
            alternate_file_name=filename
            )
        log.info('Download past mice metadata successfully!')
    except Exception as e:
        log.warning(f'Error fetching past mice metadata: {str(e)}')
        
def parse_and_save_mouse_pi_mapping():
    '''Parse mice-PI mapping from the schedule'''
    df_schedule = pd.read_csv(
        behavioral_root + R"\nwb\schedule_current.csv")[["Mouse ID", "PI"]].dropna(
    ).rename(columns={'Mouse ID': 'subject_id'})
    df_past_mice = pd.read_csv(
        behavioral_root + R"\nwb\schedule_past_mice.csv")[["Mouse ID", "PI"]].dropna(
    ).rename(columns={'Mouse ID': 'subject_id'})
        
    # Turn subject_id to text then deal with duplicates
    df_schedule['subject_id'] = df_schedule['subject_id'].astype(str)
    df_past_mice['subject_id'] = df_past_mice['subject_id'].astype(str)
        
    # Combine the two
    df_mice_pi = pd.concat([df_schedule, df_past_mice])
    # Format PI names
    df_mice_pi['PI'] = df_mice_pi['PI'].apply(reformat_PI_names)
    df_mice_pi.drop_duplicates(inplace=True)
    
    # Get unique mouse-PI mapping (concatenate multiple usernames for the same mouse)
    df_unique_mouse = (
        df_mice_pi
        .groupby("subject_id")
        .agg(PI=("PI", lambda x: ', '.join(x.unique())))  # Concatenate unique usernames
        .reset_index()
    )
    
    # Save to json to be uploaded to s3
    df_unique_mouse.to_json(behavioral_root + R"\nwb\mouse_pi_mapping.json", orient='records')

                
if __name__ == '__main__':
    
    log.info(f'\n\n=====================================================================')
    
    # Fetch schedule and parse mice-PI mapping
    fetch_schedule_and_past_mice()
    parse_and_save_mouse_pi_mapping()
    
    # Copy behavioral folders from remote PCs to local
    sync_behavioral_folders()
    
    # Ingest behavior to datajoint
    batch_convert_json_to_nwb(behavioral_root, behavioral_root + '\\nwb')
    
    # Export raw sessions on VAST to json
    get_raw_behavior_sessions_from_multiple_places(behavioral_root + '\\nwb\\raw_sessions_on_VAST.json')
    
    # Sync with AWS bucket
    upload_directory_to_s3(source_dir = R"C:\han_temp_pipeline\nwb", 
                           s3_bucket="aind-behavior-data/foraging_nwb_bonsai", 
                           method='sync'
                           )
    # also cp the mouse_pi_mapping.json to processed folder
    upload_directory_to_s3(source_dir = R"C:\han_temp_pipeline\nwb\mouse_pi_mapping.json", 
                           s3_bucket="aind-behavior-data/foraging_nwb_bonsai_processed", 
                           method='cp'
                           )