import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from check_environment import check
from score_temporal import summarize

class UpdateTests(unittest.TestCase):
    def test_environment_reports_incompatible_initializer_version(self):
        from importlib.metadata import version as real_version
        def version(name):
            return "3.0.0" if name=="keras" else real_version(name)
        with patch("check_environment.version",side_effect=version):
            with self.assertRaisesRegex(RuntimeError,"keras: beklenen"):
                check()

    def test_paired_features_use_identical_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            summarize(["common","multi"],Path(folder)/"scores.csv")
            data=pd.read_csv(Path(folder)/"scores.csv")
            self.assertEqual(set(data.h),{1,2,3,4})
            self.assertEqual(set(data.season.dropna()),{"Kış","İlkbahar","Yaz","Sonbahar"})

    def test_saved_common_model(self):
        from predict import forecast
        actual=forecast("data/modis-multi.csv","common")
        expected=pd.read_csv("results/future-common.csv")
        actual["date"]=actual.date.astype(str)
        joined=expected.merge(actual,on=["city","date","model","h"],validate="one_to_one")
        self.assertEqual(len(joined),len(expected))
        np.testing.assert_allclose(joined.prediction_x,joined.prediction_y,atol=.0001)

    def test_summer_holdout_is_disjoint(self):
        data=pd.read_csv("data/summer.csv",parse_dates=["date"])
        for city in data.city.unique():
            train=data[(data.city!=city)&(data.date.dt.year<=2023)]
            test=data[(data.city==city)&(data.date.dt.year>=2024)]
            self.assertGreater(len(test.dropna()),0)
            self.assertLess(train.date.max(),test.date.min())
            self.assertTrue(set(train.city).isdisjoint(test.city))

    def test_new_forecasts_have_version_and_quality(self):
        for path in Path("results").glob("latest-*.csv"):
            df=pd.read_csv(path)
            self.assertTrue(df.version.str.fullmatch("[a-f0-9]{64}").all())
            approved=df[df.publishable]
            self.assertTrue((approved.recent_n>=4).all())
            self.assertTrue((approved.n>=12).all())
            self.assertTrue(approved.prediction.between(-50,85).all())
    def test_province_observation_quality(self):
        df=pd.read_csv("data/province-modis.csv")
        self.assertEqual(df.city.nunique(),81)
        self.assertFalse(df.duplicated(["city","date"]).any())
        self.assertTrue((df.valid_pixels<=df.total_pixels).all())
        np.testing.assert_allclose(df.valid_fraction,df.valid_pixels/df.total_pixels)
        insufficient=(df.valid_fraction<.5)|(~df.complete_tiles)
        self.assertTrue(df.loc[insufficient,"lst"].isna().all())

    def test_province_models_reload(self):
        from predict import forecast
        actual=forecast("data/province-modis.csv","province")
        actual["date"]=actual.date.astype(str)
        expected=pd.read_csv("results/future-province.csv")
        joined=expected.merge(actual,on=["city","date","model","h"],validate="one_to_one")
        self.assertEqual(len(joined),len(expected))
        np.testing.assert_allclose(joined.prediction_x,joined.prediction_y,atol=.0001)

if __name__=="__main__":unittest.main()
