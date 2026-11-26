"""Inner spatial folds group every repeated date of a sampling site together."""
import json
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold, ParameterGrid
from spatial_train import metrics

def blocks(frame):
    if 'site' in frame:
        return frame.city.astype(str)+'|'+frame.site.astype(str)
    # Fixed 0.05 degree cells for older pilot files, explicitly distinct from 300m cells.
    return frame.city.astype(str)+'|'+np.floor(frame.lat/.05).astype(int).astype(str)+'|'+np.floor(frame.lon/.05).astype(int).astype(str)

def splits(frame):
    groups=blocks(frame)
    if groups.nunique()<3:raise ValueError('En az üç bağımsız mekânsal blok gerekli')
    return list(GroupKFold(n_splits=min(3,groups.nunique())).split(frame,groups=groups))

def select(model,name,train,features,city,group):
    grid={'Ridge':{'ridge__alpha':[1.,10.,100.]},
          'RandomForest':{'min_samples_leaf':[5,15]},
          'XGBoost':{'max_depth':[2,3]}}.get(name)
    if grid is None:return model,[]
    rows=[];best=None
    for params in ParameterGrid(grid):
        errors=[]
        for fold,(a,b) in enumerate(splits(train)):
            fitted=clone(model).set_params(**params)
            fitted.fit(train.iloc[a][features],train.iloc[a].lst)
            scores=metrics(train.iloc[b].lst,fitted.predict(train.iloc[b][features]))
            errors.append(scores['rmse'])
            rows.append(dict(city=city,group=group,model=name,fold=fold,params=json.dumps(params,sort_keys=True),
                             train_n=len(a),validation_n=len(b),rmse=scores['rmse']))
        value=float(np.mean(errors))
        if best is None or value<best[0]:best=(value,params)
    return clone(model).set_params(**best[1]),rows
