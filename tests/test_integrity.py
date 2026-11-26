"""Synthetic failure fixtures only; never research observations."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from registry import verify, combined, FEATURES, validate_preprocess
from data_quality import validate
from provenance import atomic_json
from release import activate
from registry import sha256

class IntegrityTests(unittest.TestCase):
    def model_fixture(self, root):
        files=[root/'uni-LSTM.keras',root/'uni-LSTM-preprocess.joblib']
        for f in files:f.write_bytes(b'TEST FIXTURE - NOT A REAL MODEL')
        record=dict(version=combined(files),mode='uni',model='LSTM',scope='point',features=['lst'],trained_at='2026-01-01',training_end_year=2021)
        path=root/'uni-LSTM-version.json';path.write_text(json.dumps(record))
        return files,path,record
    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'sürüm dosyası eksik'):verify('uni','LSTM',Path(d))
    def test_missing_weights_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            files,_,_=self.model_fixture(Path(d));files[0].unlink()
            with self.assertRaisesRegex(ValueError,'dosyası eksik'):verify('uni','LSTM',Path(d))
    def test_tampered_weights_or_preprocessor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for index in (0,1):
                files,_,_=self.model_fixture(Path(d));files[index].write_bytes(b'corrupted')
                with self.assertRaisesRegex(ValueError,'uyuşmuyor'):verify('uni','LSTM',Path(d))
    def test_wrong_scope_or_features_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for field,value in [('scope','province'),('features',['lst','air'])]:
                _,path,record=self.model_fixture(Path(d));record[field]=value;path.write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError,'şeması'):verify('uni','LSTM',Path(d))
    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _,p,_=self.model_fixture(Path(d));p.write_text('{')
            with self.assertRaisesRegex(ValueError,'Bozuk'):verify('uni','LSTM',Path(d))
    def test_bad_preprocessing_width_rejected(self):
        from sklearn.preprocessing import StandardScaler
        meta=dict(window=8,features=['lst'],center=0,scale=1,scaler=StandardScaler().fit(np.ones((2,2))))
        with self.assertRaisesRegex(ValueError,'genişliği'):validate_preprocess(meta,{'features':['lst']})
    def fixture(self):
        return pd.DataFrame(dict(city=['A']*3,date=['2026-01-01','2026-01-09','2026-01-25'],lst=[10,np.nan,12]))
    def test_duplicate_date_rejected(self):
        df=self.fixture();df.loc[1,'date']=df.loc[0,'date']
        with self.assertRaisesRegex(ValueError,'Tekrarlanan'):validate(df,'uni')
    def test_missing_period_preserved(self):
        df=validate(self.fixture(),'uni')
        self.assertEqual(len(df),3);self.assertTrue(pd.isna(df.lst.iloc[1]))
        self.assertNotIn(pd.Timestamp('2026-01-17'),set(df.date))
    def test_invalid_period_and_unsorted_rejected(self):
        df=self.fixture();df.loc[0,'date']='2026-01-02'
        with self.assertRaisesRegex(ValueError,'başlangıç'):validate(df,'uni')
        with self.assertRaisesRegex(ValueError,'kronolojik'):validate(self.fixture().iloc[::-1],'uni')
    def test_bad_quality_rejected(self):
        df=self.fixture().assign(scope='province',source='MOD11A2.061 Terra',valid_pixels=1,total_pixels=10,valid_fraction=.1,complete_tiles=True)
        with self.assertRaisesRegex(ValueError,'maskelenmemiş'):validate(df)
    def test_new_2026_data_and_last_valid_origin(self):
        from predict import forecast
        from forecast import calendar
        dates=calendar(2026);dates=dates[(dates>='2025-01-01')&(dates<='2026-01-25')]
        frame=pd.DataFrame(dict(city='TEST',date=dates,lst=20.0));frame.loc[frame.index[-1],'lst']=np.nan
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'synthetic.csv';frame.to_csv(path,index=False)
            pred=forecast(path,'uni',latest_valid=True)
        self.assertEqual(set(pred.origin.astype(str)),{'2026-01-17'})
        self.assertEqual(set(pred.date.astype(str)),{'2026-01-25','2026-02-02','2026-02-10','2026-02-18'})
    def test_database_failure_preserves_previous_pointer_and_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);stage=root/'candidate';stage.mkdir()
            current=root/'current.json';current.write_text('{"release_id":"old"}')
            value={'release':{'id':'new','created_at':'2026-01-01'},'features':[],'regions':{}}
            for i in range(81):
                city=str(i);value['features'].append({'properties':{'name':city}})
                value['regions'][city]={'runs':[dict(city=city,mode='province',model='LSTM',origin='2026-01-01',date='2026-01-09',h=1,version='a'*64,data_version='b'*64,publishable=True,prediction=20,recent_n=8,n=12)]}
            atomic_json(stage/'snapshot.json',value)
            atomic_json(stage/'manifest.json',{'snapshot_sha256':sha256(stage/'snapshot.json')})
            before=current.read_bytes()
            def fail(_):raise ConnectionError('test database unavailable')
            with self.assertRaises(ConnectionError):activate(stage,root=root,publish_db=fail)
            self.assertEqual(before,current.read_bytes())
    def test_atomic_json_rejects_nan_without_replacing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'v.json';p.write_text('{"old":true}')
            with self.assertRaises(ValueError):atomic_json(p,{'bad':float('nan')})
            self.assertEqual(json.loads(p.read_text()),{'old':True})
    def test_offline_html_hash_required_before_activation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);stage=root/'candidate';stage.mkdir()
            atomic_json(stage/'snapshot.json',{'release':{'id':'synthetic-test'}})
            (stage/'Atlas.html').write_text('synthetic HTML fixture')
            atomic_json(stage/'manifest.json',{'snapshot_sha256':sha256(stage/'snapshot.json'),'offline_html_sha256':'0'*64})
            with patch('release.validate_snapshot'),self.assertRaisesRegex(ValueError,'HTML bütünlüğü'):
                activate(stage,root=root)
            self.assertFalse((root/'current.json').exists())
if __name__=='__main__':unittest.main()
