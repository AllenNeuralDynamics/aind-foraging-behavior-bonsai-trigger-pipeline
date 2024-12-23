#%%
import os
import glob
import subprocess
import json


def get_behavior_sessions_from_VAST(to_json="raw_sessions_on_VAST.json"):
    """Get existing raw behavior sessions from VAST and save to json"""

    # Mount VAST
    command = R'net use z: \\allen\aind\scratch /persistent:Yes'
    subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Get behavior sessions
    root_folder="Z:\\svc_aind_behavior_transfer"
    patterns = [
        os.path.join(fR"{root_folder}/*/*/*/behavior"), # Standandized format ({rig}/{subject_id}/{sessions_folder}/behavior)
        os.path.join(fR"{root_folder}/*/*/behavior"), # sessions in "2023late_DataNoMeta_Reorganized"
        os.path.join(fR"{root_folder}/*/*/*/TrainingFolder"), # Older format found in transfer_log
        os.path.join(fR"{root_folder}/*/*/TrainingFolder"), # Older format found in transfer_log
    ]
    
    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern))

    # Save to json
    with open(to_json, 'w') as f:
        json.dump(matches, f, indent=4)
        
        
if __name__ == '__main__':
    get_behavior_sessions_from_VAST()