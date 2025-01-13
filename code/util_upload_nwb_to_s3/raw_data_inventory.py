# %%
import os
import glob
import subprocess
import json

from util import get_passcode

# Other smb folders for raw data (host IP and user name, save password in passcode.json; if no user name and password, leave it as "")
HOST_SETTINGS = [
    {
        "host": R"\\allen\aind\scratch",  # VAST (previously by Kenta's robocopy)
        "user_name": "",
        "root_folder": R"\svc_aind_behavior_transfer",
        "patterns": [
            "/*/*/*/*/behavior",  # Standandized format under "DO NOT TOUCH"({rig}/{subject_id}/{sessions_folder}/behavior)
            "/*/*/*/behavior",  # Standandized format ({rig}/{subject_id}/{sessions_folder}/behavior)
            "/*/*/behavior",  # sessions in "2023late_DataNoMeta_Reorganized"
            "/*/*/*/TrainingFolder",  # Older format found in transfer_log
            "/*/*/TrainingFolder",  # Older format found in transfer_log
        ],
    },
    {
        "host": R"\\allen\aind\scratch",  # VAST (watchdog cache)
        "user_name": "",
        "root_folder": R"\dynamic_foraging_rig_transfer",
        "patterns": [
            "/*/behavior",  
        ],
    },
    {
        "host": R"\\10.128.49.133\smb",  # Adam Glaser's NAS
        "user_name": R"\admin",
        "root_folder": "",
        "patterns": [
            "/*/*/*/behavior",  # Standandized format ({rig}/{subject_id}/{sessions_folder}/behavior)
        ],
    },
]


def get_raw_behavior_sessions(root_folder, patterns):
    """Get existing raw behavior sessions from VAST and save to json"""
    matches = []
    for pattern in patterns:
        path_this = os.path.join(fR"Y:\{root_folder}\{pattern}")
        matches.extend(glob.glob(path_this))

    return matches


def get_raw_behavior_sessions_from_multiple_places(json_path="raw_sessions_on_VAST.json"):
    matches = []

    for host_setting in HOST_SETTINGS:
        host = host_setting["host"]
        user = host_setting["user_name"]
        root_folder = host_setting["root_folder"]
        patterns = host_setting.get("patterns", ["/*"])

        if user:
            passcode = get_passcode(host_setting["host"])
            command = fR'net use Y: {host} /user:{user} {passcode} /persistent:Yes'
        else:
            command = fR'net use Y: {host} /persistent:Yes'
        subprocess.run(command, shell=True, capture_output=True, text=True)

        # Get behavior sessions
        match_this = get_raw_behavior_sessions(root_folder, patterns)
        # Add host and root_foler to each match
        for i, match in enumerate(match_this):
            _path = match.replace('Y:\\\\', '')
            match_this[i] = f"{host}\\{_path}"
        matches.extend(match_this)
        
        # Unmount
        command = R'net use Y: /delete /yes'
        subprocess.run(command, shell=True, capture_output=True, text=True)

    # Save to json
    with open(json_path, 'w') as f:
        json.dump(matches, f, indent=4)


if __name__ == '__main__':
    get_raw_behavior_sessions_from_multiple_places()
    print("Done")
