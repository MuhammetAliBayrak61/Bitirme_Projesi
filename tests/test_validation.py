import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from province_archive import qc_mask
from enrich_summer import validate_features,DW
from spatial_validation import blocks,splits

class ValidationTests(unittest.TestCase):
    def test_modis_qc_bits_and_temperature_range(self):
        raw=np.array([15000,15000,15000,15000,7500,25000])
        quality=np.array([0,1,3,128,0,0],dtype=np.uint8)
        np.testing.assert_equal(qc_mask(raw,quality),[True,True,False,False,False,False])
    def test_dynamic_world_requires_probability_mass(self):
        frame=pd.DataFrame([{**{x:1/9 for x in DW},'id':'synthetic-test','air':20.,'dew':10.}])
        self.assertEqual(validate_features(frame)['complete'],1)
        frame.loc[0,DW[0]]=2
        with self.assertRaisesRegex(ValueError,'olasılık'):validate_features(frame)
    def test_era5_kelvin_or_wrong_dewpoint_rejected(self):
        frame=pd.DataFrame([{**{x:1/9 for x in DW},'id':'synthetic-test','air':293.,'dew':280.}])
        with self.assertRaisesRegex(ValueError,'ERA5'):validate_features(frame)
        frame.loc[0,['air','dew']]=[20,24]
        with self.assertRaisesRegex(ValueError,'ERA5'):validate_features(frame)
    def test_missing_features_reported_not_imputed(self):
        frame=pd.DataFrame([{**{x:np.nan for x in DW},'id':'synthetic-test','air':20.,'dew':10.}])
        result=validate_features(frame)
        self.assertEqual(result['complete'],0)
        self.assertEqual(result['missing_fraction']['water'],1)
    def test_inner_folds_keep_repeated_sites_together(self):
        df=pd.read_csv('data/summer.csv')
        for city in df.city.unique():
            train=df[(df.city!=city)&(pd.to_datetime(df.date).dt.year<=2023)]
            for a,b in splits(train):
                self.assertTrue(set(blocks(train.iloc[a])).isdisjoint(blocks(train.iloc[b])))
                self.assertNotIn(city,set(train.iloc[a].city)|set(train.iloc[b].city))
    def test_no_new_data_short_circuits(self):
        from pipeline import plan
        with patch('pipeline.source_inventory',return_value=[{'properties':{'start_datetime':'2025-12-27'}}]):
            self.assertFalse(plan('data/province-modis.csv')['new_data'])
    def test_archive_outputs_unchanged_by_2026_candidate(self):
        old=pd.read_csv('data/province-modis.csv');new=pd.read_csv('results/revision/incoming/province-modis-2026.csv')
        prior=new[new.date<='2025-12-31']
        pd.testing.assert_frame_equal(old.sort_values(['city','date']).reset_index(drop=True),prior[old.columns].sort_values(['city','date']).reset_index(drop=True),check_exact=False,atol=1e-9,rtol=1e-9)
if __name__=='__main__':unittest.main()
