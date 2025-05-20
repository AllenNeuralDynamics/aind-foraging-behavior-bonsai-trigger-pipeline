set LOGFILE="C:\han_temp_pipeline\auto_populate_log.txt"
call :LOG >> %LOGFILE% 2>&1
exit /B

:LOG
call "C:\Users\svc_aind_behavior\AppData\Local\miniconda3\Scripts\activate.bat" han_temp_pipeline
python "C:\Users\svc_aind_behavior\Documents\aind-foraging-behavior-bonsai-trigger-pipeline\code\util_upload_nwb_to_s3\behavior_pipeline_bonsai.py"
net use z: \\allen\aind\scratch /persistent:Yes

