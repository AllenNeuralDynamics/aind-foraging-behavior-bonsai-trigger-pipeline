# Foraging Behavior Pipeline for Bonsai
(Han Hou @ Aug 2023)

***This is still a temporary workaround until AIND behavior pipeline is implemented.***

## Pipeline structure

![image](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/assets/24734299/99723ed4-8e11-4577-8278-36f7ff071ae1)

#### 1. (On Han's PC) Upload raw behavior data to cloud ([github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/blob/main/code/util_upload_nwb_to_s3/behavior_pipeline_bonsai.py))
   - From all behavior rigs, fetch raw behavior files (.json) generated by the [foraging-bonsai GUI](https://github.com/AllenNeuralDynamics/dynamic-foraging-task)
   - Turn .json files into .nwb files, which contain both data and metadata
   - Upload all .nwb files to a single S3 bucket `s3://aind-behavior-data/foraging_nwb_bonsai/`
     
#### 2. (In Code Ocean, this repo) Trigger computation ([`CO capsule: foraging_behavior_bonsai_pipeline_trigger`](https://codeocean.allenneuraldynamics.org/capsule/9148690/), [github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/blob/main/code/run_capsule.py))
   - Identify unprocessed .nwb files ([github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/blob/c456dcf9bb5f37fc6c836b3a6a53f3c311aa4369/code/run_capsule.py#L31-L48))
   - Send unprocessed .nwb files to [`CO pipeline: Han_pipeline_foraging_behavior_bonsai`](https://codeocean.allenneuraldynamics.org/capsule/8633725/tree).<br>
   In the CO pipeline:
     - Distribute .nwb files to parallel workers ([`CO capsule: foraging_behavior_bonsai_pipeline_assign_job`](https://codeocean.allenneuraldynamics.org/capsule/0827783/tree), [github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-assign-job))
     - Do real analysis on each .nwb file ([`CO capsule: foraging_behavior_bonsai_nwb`](https://codeocean.allenneuraldynamics.org/capsule/5625005/tree), [github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-basic)), where arbitrary dataframes and figures are generated.
   - Collect and combine results from the workers ([`CO capsule: foraging_behavior_bonsai_pipeline_collect_and_upload_results`](https://codeocean.allenneuraldynamics.org/capsule/0579904/tree), [github](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-collect-results))
   - Upload results to this S3 bucket `s3://aind-behavior-data/foraging_nwb_bonsai_processed/`

#### 3. (In Code Ocean) Visualization by Streamlit app ([`CO capsule: foraging-behavior-browser`](https://codeocean.allenneuraldynamics.org/capsule/3373065/), [github](https://github.com/AllenNeuralDynamics/foraging-behavior-browser))
The Streamlit app fetches data from the above S3 bucket and generates data viz. You could run the app either on [Code Ocean](https://codeocean.allenneuraldynamics.org/cw/4eb53fe0-a03c-42bb-8c94-add41e78ba8d/proxy/8501/) (recommended) or on [Streamlit public cloud](https://foraging-behavior-browser.streamlit.app/Bonsai)

## Automatic training
See [this repo](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-automatic-training)

## How to add more rigs
- On the rig PC, share the data folder to the Windows Network.
- Make sure the data folder is accessible through typing the network address like `\\W10DT714033\behavior_data\447-1-D` in Windows Explorer on another PC.
- Let me know network address, the username, and the passcode. I will create a new entry [here](https://github.com/hanhou/code_cache/blob/dcf0eccb264db9a59d21fc238358970bbe74e1af/sync_bonsai/behavior_pipeline_bonsai.py#L36-L62).

## How to add more analyses
The pipeline is still a prototype at this moment. As you can see in the [Streamlit app](https://foraging-behavior-browser.streamlit.app/Bonsai), so far I only implemented [two basic analyses](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-basic/blob/e740865cf7c5ed9c649147156d8b2afada714249/code/process_nwbs.py#L181-L195): 
- compute essential session-wise stats
- generate a simple plot of choice-reward history
  
To add more analyses to the pipeline, just plug in your own function [here](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-basic/blob/e740865cf7c5ed9c649147156d8b2afada714249/code/process_nwbs.py#L181-L195). Your function should take `nwb` as an input and generate plots or any other results with filename starting with `session_id`.

If you would like to access the .nwb files directly or do analysis outside Code Ocean (not recommended though), check out this bucket `s3://aind-behavior-data/foraging_nwb_bonsai/`. For details, see [below](https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline?tab=readme-ov-file#accessing-foraging-nwbs-for-off-pipeline-analysis).

## Pipeline-ready checklist
Checklist before the pipeline is ready to run:
1. CO pipeline `Han_pipeline_foraging_behavior_bonsai`:
    - No yellow warning sign (otherwise, do a `Reproducible Run` of that capsule first)
    - Check the argument of `foraging_behavior_bonsai_pipeline_assign_job` that controls the number of capsule instances
    - Check the argument of `foraging_behavior_bonsai_nwb` that controls the number of multiprocessing cores of each instance.
       - This number should match the core number of "Adjust Resources for capsule in pipeline"
    - Make sure the pipeline is set to use "Spot instances" (otherwise it takes too long to start) and "without cache" (otherwise the input S3 bucket will not be updated)

      <img src="https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/assets/24734299/7c15b4cc-12ea-4ba4-ae5c-28fd608ed8e1" width=300>

2. Make sure these capsules are not running (`Status` is four gray dots; VSCode are held or terminated)
   - `foraging_behavior_bonsai_pipeline_assign_job`
   - `foraging_behavior_bonsai_nwb`
   - `foraging_behavior_bonsai_pipeline_collect_and_upload_results`
3. Make sure ***one and only one instance*** of `foraging_behavior_bonsai_pipeline_trigger` is running.
4. Make sure ***one and only one instance*** of `foraging-behavior-bonsai-automatic-training` is running.

## Notes on manually re-process all nwbs and overwrite S3 database (and thus the Streamlit app)
> [!IMPORTANT]
> I should do this after work hours, as it will be disruptive to the AutoTrain system. (see [this issue](https://github.com/AllenNeuralDynamics/aind-behavior-blog/issues/566))
1. Stop the triggering capsule and the AutoTraining capsule.
2. (optional) Re-generate all nwbs
   - Backup nwb folder on my PC and S3
   - On S3, move the old `/foraging_nwb_bonsai` to a backup folder and create a new `/foraging_nwb_bonsai`
   - Re-generate nwbs from jsons on my PC
3. Backup and clear `/foraging_nwb_bonsai_processed` bucket
   - On S3, copy the folder to a backup folder
   - Clear the old folder
      - **If you don't clear it, at least you should delete `df_sessions.pkl`, `error_files.json`, and `pipeline.log` (they will be appended, not overwritten)**
      - Troubleshooting: when attaching a S3 folder to a capsule, the folder must not be empty (otherwise a "permission denied" error)

#### Case A: still use the pipeline (recommended)
4. Make sure to assign 10 or more workers and set `CPU number = 16` (for spot machine) and `argument = 16`. In this case, you'll have > 10 * 16 = 160 total cores!
   
<img src="https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/assets/24734299/2d60c2c1-314b-4b01-ad1b-d91c5321e20b" width=400> <img src="https://github.com/AllenNeuralDynamics/aind-foraging-behavior-bonsai-trigger-pipeline/assets/24734299/59a815c3-96a4-4458-a83d-eb298874765e" width=500>

6. Trigger the pipeline as usual. In this case, only diff of `nwb` and `nwb_processed` will be processed. (it works well if you have already cleaned up the `processed` folder)

#### Case B: manually run each capsule (obsoleted)
4. Manually trigger the batch computation in capsule `foraging_behavior_bonsai_nwb`:
   - Make sure the CPU number of the environment is 16 or more :)
   - Run `processing_nwb.py` manually in parallel (with `LOCAL_MANUAL_OVERRIDE = True`)
5. Manually trigger the collect_and_upload capsule:
   - Manually register a data asset:
      - Use any name, but `mount` must be `data/foraging_behavior_bonsai_pipeline_results`
      - The data asset cannot be registered in VSCode?? @20240303 I can only create data asset outside VSCode.
   - In the capsule `collect_and_upload_restuls`, manually attach the data asset just created, and press `Reproducible Run`.
      - I have adapted `collect_and_upload_restuls` so that it can also accept data that are not in /1, /2, ... like those from the pipeline run.
6. To restore the pipeline, follow above "Pipeline-ready checklist"

## Accessing foraging .nwbs for off-pipeline analysis
| .nwb datasets                 | Dataset 1                                                       | Dataset 2 (old)                                                       |
|-------------------------------|-----------------------------------------------------------------|-----------------------------------------------------------------------|
| Where are the data collected? | AIND                                                            | Janelia and AIND                                                      | 
| Behavior hardware             | Bonsai-Harp                                                     | Bpod                                                                  |
| Size                          | 1423 sessions / 92 mice                                         | 4327 sessions / 157 mice                                              | 
| Modality                      | behavior only                                                   | 3803 sessions / 157 mice: pure behavior<br> 35 sessions / 8 mice: ephys + DLC outputs  | 
| Still growing?                | Yes; updating daily (by the current repo)                     | No longer updating                                                    | 
| NWB format                    | New bonsai nwb format                                           | Compatible with the new bonsai nwb format                              | 
| Raw NWBs                      | - ***S3 bucket***: `s3://aind-behavior-data/foraging_nwb_bonsai/`<br>- ***CO data asset***: `foraging_nwb_bonsai`<br>(id=f908dd4d-d7ed-4d52-97cf-ccd0e167c659) | - ***S3 bucket***: `s3://aind-behavior-data/foraging_nwb_bpod/`<br>- ***CO data asset***: `foraging_nwb_bpod`<br>(id=4ba57838-f4b7-4215-a9d9-11bccaaf2e1c)  | 
| Processed results             | - ***S3 bucket***: `s3://aind-behavior-data/foraging_nwb_bonsai_processed/`<br>- ***CO data asset***: `foraging_nwb_bonsai_processed`<br>(id=4ad1364f-6f67-494c-a943-1e957ab574bb) | - ***S3 bucket***: `s3://aind-behavior-data/foraging_nwb_bpod_processed/`<br>- ***CO data asset***: `foraging_nwb_bpod_processed`<br>(id=7f869b24-9132-43d3-8313-4b481effeead)
| Code Ocean example capsule    | `foraging_behavior_bonsai_nwb`                                  | `foraging_behavior_bonsai_nwb`                                         |
| Streamlit visualization       | [The Streamlit behavior browser](https://foraging-behavior-browser.allenneuraldynamics-test.org/)  | [Click "include old Bpod sessions" in the app](https://foraging-behavior-browser.allenneuraldynamics-test.org/?if_load_bpod_sessions=True&filter_subject_id=&filter_session=1.0&filter_session=66.0&filter_finished_trials=0.0&filter_finished_trials=947.0&filter_foraging_eff=0.0&filter_foraging_eff=1.3475873305423873&filter_task=Uncoupled+Baiting&filter_task=Uncoupled+Without+Baiting&filter_task=Coupled+Without+Baiting&filter_task=Coupled+Baiting&filter_task=RewardN&table_height=650&tab_id=tab_session_x_y&x_y_plot_xname=session&x_y_plot_yname=finished_trials&x_y_plot_group_by=data_source&x_y_plot_if_show_dots=False&x_y_plot_if_aggr_each_group=True&x_y_plot_aggr_method_group=mean+%2B%2F-+sem&x_y_plot_if_aggr_all=False&x_y_plot_aggr_method_all=mean+%2B%2F-+sem&x_y_plot_smooth_factor=5&x_y_plot_if_use_x_quantile_group=False&x_y_plot_q_quantiles_group=20&x_y_plot_if_use_x_quantile_all=False&x_y_plot_q_quantiles_all=20&x_y_plot_if_show_diagonal=False&x_y_plot_dot_size=10&x_y_plot_dot_opacity=0.3&x_y_plot_line_width=2.0&x_y_plot_figure_width=1300&x_y_plot_figure_height=900&x_y_plot_font_size_scale=1.0&x_y_plot_selected_color_map=Plotly&x_y_plot_size_mapper=finished_trials&x_y_plot_size_mapper_gamma=1.0&x_y_plot_size_mapper_range=3&x_y_plot_size_mapper_range=20&session_plot_mode=sessions+selected+from+table+or+plot&auto_training_history_x_axis=session&auto_training_history_sort_by=subject_id&auto_training_history_sort_order=descending&auto_training_curriculum_name=Uncoupled+Baiting&auto_training_curriculum_version=1.0&auto_training_curriculum_schema_version=1.0)| 
| How to access the master table showing in the app?| the `df_sessions.pkl` file in the "Processed results" path above | same as left (except the "Processed results" path for `bpod`)|
| Notes                         | Some sessions have ***fiber photometry data*** or ***ephys data*** collected at the same time, but they have not been integrated to the .nwbs yet. | Some sessions have ***fiber photometry data*** collected at the same time, but they have not been integrated to the .nwbs yet. |

## What's next
We will likely be refactoring the pipeline after we figure out the AIND behavior metadata schema, but the core ideas and data analysis code developed here will remain. Stay tuned.
