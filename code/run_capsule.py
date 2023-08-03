""" top level run script """
#%%
import json, os
from aind_codeocean_api.codeocean import CodeOceanClient

BEHAVIOR_PIPELINE_ID = '93b5045b-b77d-4426-97ef-75c22e618798'

co_client = CodeOceanClient(**json.load(open('/root/.codeocean/credentials.json', 'r')))


def get_nwb_to_process(nwb_folder, nwb_processed_folder):
    # The simplest solution: find nwb files that have not been processed
    nwb = [f_name.split('/')[-1].split('.')[0] for f_name in glob.glob(f'{nwb_folder}/*.nwb')]
    nwb_processed = [f_name.split('/')[-1].split('.')[0] for f_name in glob.glob(f'{nwb_processed_folder}/*')]

    f_error = f'{nwb_processed_folder}/error_files.json'
    if Path(f_error).exists():
        nwb_errors = [f_name.split('/')[-1].split('.')[0] for f_name in json.load(open(f'{nwb_processed_folder}/error_files.json'))]
    else:
        nwb_errors = []
        
    nwb_to_process = [f'{nwb_folder}/{f}.nwb' for f in list(set(nwb) - set(nwb_processed) - set(nwb_errors))]
        
    return nwb_to_process


def run_pipeline():
    
    
    return pipeline_job

if __name__ == "__main__": 

    script_dir = os.path.dirname(os.path.abspath(__file__))

    nwb_folder = os.path.join(script_dir, '../data/foraging_nwb_bonsai')
    nwb_processed_folder = os.path.join(script_dir, '../data/foraging_nwb_bonsai_processed')

    nwb_to_process = get_nwb_to_process(nwb_folder, nwb_processed_folder)


    # run_pipeline()