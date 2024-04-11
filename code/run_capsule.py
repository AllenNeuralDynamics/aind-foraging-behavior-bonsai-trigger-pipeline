""" top level run script """
#%%
import json, os
import glob
import time
from pathlib import Path
from datetime import datetime
import pytz

from aind_codeocean_api.codeocean import CodeOceanClient

BEHAVIOR_PIPELINE_ID = '93b5045b-b77d-4426-97ef-75c22e618798'
COLLECT_AND_UPLOAD_CAPSULE_ID = '3b851d69-5e4f-4718-b0e5-005ca531aaeb'

co_client = CodeOceanClient(domain=os.getenv('API_KEY'),
                            token=os.getenv('API_SECRET'))

pacific_tz = pytz.timezone('America/Los_Angeles')

#%%
def _reformat_string(s):
    if s.count('_') < 2:  # No suffix
        return s
    subject_date, time_part = s.rsplit('_', 1)
    
    if len(time_part) < 5:  # Old suffix (0, 1, 2, ...)
        return s
    
    time_part = time_part.zfill(6)
    formatted_time = f'{time_part[:2]}-{time_part[2:4]}-{time_part[4:6]}'
    return f'{subject_date}_{formatted_time}'


def get_nwb_to_process(nwb_folder, nwb_processed_folder):
    # The simplest solution: find nwb files that have not been processed
    nwb = [f_name.split('/')[-1].split('.')[0] for f_name in glob.glob(f'{nwb_folder}/*.nwb')]
    nwb_processed = [f_name.split('/')[-1].split('.')[0] for f_name in glob.glob(f'{nwb_processed_folder}/*')]
    
    # Per this issue https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-basic/issues/1, 
    # I have to revert the processed file name back to json name, e.g.: 'xxxxx_2023-11-08_92908' to 'xxxxx_2023-11-08_09-29-08'
    nwb_processed = [_reformat_string(s) for s in nwb_processed]

    f_error = f'{nwb_processed_folder}/error_files.json'
    if Path(f_error).exists():
        nwb_errors = [f_name.split('/')[-1].split('.')[0] for f_name in json.load(open(f'{nwb_processed_folder}/error_files.json'))]
    else:
        nwb_errors = []
        
    nwb_to_process = [f'{nwb_folder}/{f}.nwb' for f in list(set(nwb) - set(nwb_processed) - set(nwb_errors))]
        
    return nwb_to_process


def run_pipeline():

    # Get nwbs that are not processed
    nwb_to_process = get_nwb_to_process(nwb_folder, nwb_processed_folder)

    if not len(nwb_to_process):
        # print(f'{datetime.now()}  No new data...')
        return 
    
    print(f'--- {datetime.now(pacific_tz)} ---')
    print(f'Found {len(nwb_to_process)} new nwb files! Trigger computation...')
    # --- Trigger behavior pipeline HERE !!! ----
    pipeline_job_id = co_client.run_capsule(capsule_id=BEHAVIOR_PIPELINE_ID,
                                            data_assets=[]).json()['id']
    
    # Wait for the pipeline to finish
    if_completed = False        
    while not if_completed:
        status = co_client.get_computation(computation_id=pipeline_job_id).json()
        print(f'{datetime.now(pacific_tz)}: waiting for nwb processing...')
        if_completed = status['state'] == 'completed' and status['has_results'] == True
        time.sleep(5)
        
    print(f'{datetime.now(pacific_tz)}: Computation Done!')
    
    if status['end_status'] == 'succeeded':
        # ---- Register data asset ----
        result_asset_id = co_client.register_result_as_data_asset(computation_id=pipeline_job_id, 
                                                asset_name=f'foraging_behavior_bonsai_pipeline_results_{status["name"]}',
                                                mount='foraging_behavior_bonsai_pipeline_results',
                                                tags=['foraging', 'behavior', 'bonsai', 'hanhou', 'pipeline_output']).json()['id']

        # --- Wait until data is registered (this does not necessarily mean that the data is correctly "cached") ---
        if_registered = False
        while not if_registered:
            time.sleep(5)
            status = co_client.get_data_asset(result_asset_id)
            print(f'{datetime.now(pacific_tz)}: waiting for registering the data asset...')
            if_registered = (status.status_code == 200) and (status.json()['state'] == 'ready')
        
        # --- Retry upload until successful (otherwise the data asset may not be correctly "cached") --
        if_upload_success = False
        while not if_upload_success:
            # ---- Run foraging_behavior_bonsai_pipeline_collect_and_upload_results ----
            upload_capsule_id = co_client.run_capsule(capsule_id=COLLECT_AND_UPLOAD_CAPSULE_ID, 
                                                        data_assets=[dict(id=result_asset_id,
                                                                        mount='foraging_behavior_bonsai_pipeline_results')]).json()['id']
            
            # --- Wait until upload is finished ---
            if_completed = False          
            while not if_completed:
                print(f'{datetime.now(pacific_tz)}: waiting for packaging and uploading results to S3...')
                status = co_client.get_computation(computation_id=upload_capsule_id).json()
                if_completed = status['state'] == 'completed'
                time.sleep(5)
            
            # --- if end_status is not succeeded, retry calling the upload capsule ---
            if_upload_success = status['end_status'] == 'succeeded'
            if not if_upload_success:
                print(f'{datetime.now(pacific_tz)}: upload failed, probably because the data asset {result_asset_id} is not cached correctly yet. Retrying...')
                print(f'   {status}')
                time.sleep(30)

        
    print(f'{datetime.now(pacific_tz)}: ALL DONE!')


if __name__ == "__main__": 

    script_dir = os.path.dirname(os.path.abspath(__file__))
    nwb_folder = os.path.join(script_dir, '../data/foraging_nwb_bonsai')
    nwb_processed_folder = os.path.join(script_dir, '../data/foraging_nwb_bonsai_processed')
    
    print(co_client.get_data_asset('d5271dbd-770d-4083c-b2a0-a3dc5687a411'))

    #while 1:
    #    run_pipeline()
    #    time.sleep(10)