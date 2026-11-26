"""Manual candidate pipeline. Publication disabled until the owner enables it."""
import json
import os
import subprocess
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator
root=os.environ['LST_ROOT'];python=os.environ['LST_PYTHON']

def has_new_data():
    result=subprocess.run([python,'scripts/pipeline.py'],cwd=root,check=True,capture_output=True,text=True)
    return json.loads(result.stdout)['new_data']

with DAG('turkiye_lst_guncelleme',start_date=pendulum.datetime(2026,1,1,tz='UTC'),schedule=None,
         catchup=False,max_active_runs=1,default_args={'retries':1}) as dag:
    changed=ShortCircuitOperator(task_id='yeni_veri_var_mi',python_callable=has_new_data)
    def task(name,command):
        return BashOperator(task_id=name,bash_command='"$LST_PYTHON" '+command,cwd=root,append_env=True,
            env={'LST_PYTHON':python,'LST_RUN':'{{ ts_nodash }}'},execution_timeout=pendulum.duration(hours=3))
    download=task('aday_veri','scripts/province_archive.py --baseline data/province-modis.csv --output "candidates/$LST_RUN/data.csv"')
    quality=task('kalite_kontrol','scripts/data_quality.py "candidates/$LST_RUN/data.csv"')
    evaluate=task('sabit_model_degerlendirme','scripts/evaluate_temporal.py --data "candidates/$LST_RUN/data.csv" --out "candidates/$LST_RUN/evaluation"')
    forecasts=task('tahmin_ve_yayin_hazirligi','scripts/run_update.py --province-data "candidates/$LST_RUN/data.csv" --root "candidates/$LST_RUN/releases"')
    # Retraining is a separate reviewed experiment. No writes to production DB here.
    changed >> download >> quality >> evaluate >> forecasts
