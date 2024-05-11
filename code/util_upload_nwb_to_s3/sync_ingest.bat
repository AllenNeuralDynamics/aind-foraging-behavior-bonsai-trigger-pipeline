set LOGFILE="C:\Users\admin\Desktop\auto_populate_log.txt"
call :LOG >> %LOGFILE% 2>&1
exit /B

:LOG
call "C:\Users\admin\anaconda3\Scripts\activate.bat" foraging_trigger_pipeline
python "D:\Han_Sync\Svoboda\Scripts\aind-foraging-behavior-bonsai-trigger-pipeline\code\util_upload_nwb_to_s3\behavior_pipeline_bonsai.py"
