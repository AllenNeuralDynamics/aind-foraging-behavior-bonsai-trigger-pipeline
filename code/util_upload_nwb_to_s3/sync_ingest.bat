set LOGFILE="C:\han_temp_pipeline\auto_populate_log.txt"
call :LOG >> %LOGFILE% 2>&1
exit /B

:LOG
call "C:\Users\han.hou\AppData\Local\miniconda3\condabin\activate.bat" han_temp_pipeline
python "E:\Scripts\aind-foraging-behavior-bonsai-trigger-pipeline\code\util_upload_nwb_to_s3\behavior_pipeline_bonsai.py"
