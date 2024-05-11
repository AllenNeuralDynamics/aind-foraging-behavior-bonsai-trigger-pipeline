'''
Batch execute commands on all remote PCs
'''

import os
import json
import time

import paramiko

from foraging_gui.TransferToNWB import bonsai_to_nwb

#%%
def get_passcode(pc_name):
    ''' Get passcode for remote PCs from json
    '''
    with open(os.path.dirname(os.path.abspath(__file__)) + '\passcode.json') as f:
        passcode = json.load(f)
        
    return passcode[pc_name]
    
def ssh_command(ip, port, user, passwd, cmds):
    client = paramiko.SSHClient()
    # Automatically add host key
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=user, password=passwd)
        
        # Note that in order to run commands in conda environment, 
        # all commands must be concatenated together with '&&'
        # because conda environment does not seem to be persistent across commands.
        stdin, stdout, stderr = client.exec_command(' && '.join(cmds))
        print(stdout.read().decode())
        print(stderr.read().decode())
    finally:
        client.close()

                
if __name__ == '__main__':
    #=============================   Change me!!! ===============================
    rigs = {
        # alias: [pc_name, user_name, conda_path, env_name]
        "447-1-A/B": ["W10DT714033", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"],
        "447-1-C/D": ["W10DT714086", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"], 
        "447-2-A/B": ["W10DT714084", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"],
        "447-2-C/D": ["W10DT714027", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"], 
        "447-3-A/B": ["W10DT714028", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"], 
        "447-3-C/D": ["W10DT714030", "svc_aind_behavior", R"C:/Users/svc_aind_behavior/AppData/Local/miniconda3/condabin/conda.bat", "Foraging"],
        "323_EPHYS_1": ["W10DT713669", "svc_aind_ephys", R"C:\ProgramData\Miniconda3\condabin\conda.bat", "Foraging"],
        "323_EPHYS_3": ["W10DT713883", "svc_aind_ephys", R"C:\Users\svc_aind_ephys\Anaconda3\Library\bin\conda.bat", "ForagingGUI"],
    }
    
    # Copy behavioral folders from remote PCs to local
    for rig, (pc_name, user_name, conda_path, env_name) in rigs.items():
        print(f"\n\n=============== {rig} ({pc_name}) ===============")
        cmds = [
            f'call "{conda_path}" activate {env_name}',
            
            # Update aind-auto-train package
            f'pip show aind-auto-train | findstr Version',
            f'pip install --upgrade git+https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-automatic-training.git@main',
            f'pip show aind-auto-train | findstr Version',
            ]

        ssh_command(pc_name, 22, user_name, get_passcode(pc_name), cmds)
    