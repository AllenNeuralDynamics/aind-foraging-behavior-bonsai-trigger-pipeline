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

from bonsai_to_nwb import bonsai_to_nwb

#=============================   Change me!!! ===============================
# Address of remote training rig PCs
# Solve connection bugs: https://stackoverflow.com/questions/24933661/multiple-connections-to-a-server-or-shared-resource-by-the-same-user-using-more
rigs = [
    {'local': 'AIND-Tower-5', 'remote': R'\\10.128.41.7\Users\aind_behavior\Documents\BonsaiForaging\Data', 'user_name': 'aind_behavior', 'passcode': 'TraiNINGlab587!'},
    
    # New rigs in Rm 447
    *[{'local': fR'AIND-447-B{rig}', 'remote': fR'\\LUKWATA\Users\svc_aind_behavior\Documents\BehaviorData\Blue-{rig}', 
       'user_name': 'svc_aind_behavior', 
       'passcode': '@ind-Beeh@ve'} for rig in (1, 2, 3, 4)],   

    *[{'local': fR'AIND-447-G{rig}', 'remote': fR'\\CHARYBDIS\Users\SVC_aind_behavior\Documents\BehaviorData\Green-{rig}', 
       'user_name': 'svc_aind_behavior', 
       'passcode': '@ind-Beeh@ve'} for rig in (1, 2, 3, 4)],   
    
    *[{'local': fR'AIND-447-R{rig}', 'remote': fR'\\ADARO\Users\SVC_aind_behavior\Documents\BehaviorData\Red-{rig}', 
       'user_name': 'svc_aind_behavior', 
       'passcode': '@ind-Beeh@ve'} for rig in (1, 2, 3, 4)],   
]


# Root path to place bonsai sessions
behavioral_root = R'F:\Data_for_ingestion\Foraging_behavior\Bonsai'

# Pipeline log
pipeline_log = R'F:\Data_for_ingestion\Foraging_behavior\Bonsai\bonsai_pipeline.log'  # Simplified log for this code
#==========================================================================

logging.basicConfig(# filename=pipeline_log, 
                    level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s [%(funcName)s]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    #filemode='a',
                    handlers=[logging.StreamHandler(), logging.FileHandler(pipeline_log)])

log = logging.getLogger(__name__)
log.info('------------------------------------------------------------------------')


def sync_behavioral_folders():
    for rig in rigs:
        summary_start = False
        command = fR'''net use {rig['remote']} /u:{rig['user_name']} {rig['passcode']}&&'''\
                  fR'''robocopy  {rig['remote']} {behavioral_root}\{rig['local']} /e /xx /XD "0000" "test" /xj /xjd /mt /np /Z /W:1 /R:5 /tee /fft &&'''\
                  fR'''net use {rig['remote']} /d'''         
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
        
        
def batch_convert_json_to_nwb(json_dir, nwb_dir):
    
    os.makedirs(nwb_dir, exist_ok=True)
    
    # Walk through all .json files in the directory including sub-directories
    for filepath in glob.iglob(json_dir + '/**/*.json', recursive=True):
        filename = os.path.basename(filepath)
        nwb_filename = filename.replace('.json', '.nwb')

        # Check if corresponding .nwb file exists
        if not os.path.exists(os.path.join(nwb_dir, nwb_filename)):
            try:
                # Convert .json to .nwb
                bonsai_to_nwb(filepath, nwb_dir)
                log.info(f'Successfully converted {filename} to .nwb')
            except Exception as e:
                log.error(f'Error converting {filename} to .nwb: {str(e)}')
        else:
            log.info(f'Already exists nwb for {filename}, skipped...')

def upload_directory_to_s3(source_dir, s3_bucket):
    # Create the AWS CLI command
    aws_cli_command = ['aws', 's3', 'sync', source_dir, f's3://{s3_bucket}/']

    # Execute the AWS CLI command
    subprocess.run(aws_cli_command, check=True)
    
                
if __name__ == '__main__':
    
    # Copy behavioral folders from remote PCs to local
    sync_behavioral_folders()
    
    # Ingest behavior to datajoint
    batch_convert_json_to_nwb(behavioral_root, behavioral_root + '\\nwb')
    
    # Sync with AWS bucket
    upload_directory_to_s3(source_dir = R"F:\Data_for_ingestion\Foraging_behavior\Bonsai\nwb", 
                           s3_bucket="aind-behavior-data/foraging_nwb_bonsai", 
                           )