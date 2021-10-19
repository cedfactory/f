import pandas as pd
import numpy as np
from tiase.fimport import fimport
from tiase.findicators import findicators
from tiase.ml import data_splitter,classifier_svc,classifier_decision_tree,meta_classifier
from tiase.ml import toolbox
import pytest

class TestMlClassifier:

    def test_meta_classifier_voting(self):
        filename = "./tiase/data/test/google_stocks_data.csv"
        df = fimport.get_dataframe_from_csv(filename)

        df = findicators.normalize_column_headings(df)
        df = toolbox.make_target(df, "pct_change", 7)
        df = findicators.remove_features(df, ["open","adj_close","low","high","volume"])
        
        target = "target"
        ds = data_splitter.DataSplitter(df, target=target, seq_len=21)
        ds.split(0.7)
        
        g_classifiers = [
            { "name": "DTC3", "classifier" : classifier_decision_tree.ClassifierDecisionTree(df.copy(), target=target, data_splitter=ds, params={'max_depth': 3, 'random_state': 1})},
            { "name": "SVC", "classifier" : classifier_svc.ClassifierSVC(df.copy(), target, ds)},
            { "name": "SVC_poly", "classifier" : classifier_svc.ClassifierSVC(df.copy(), target, ds, params={'kernel': 'poly'})}
        ]

        for g_classifier in g_classifiers:
            model = g_classifier["classifier"]
            model.fit()
            '''
            model_analysis = model.get_analysis()
            print("------")
            print("Precision : {:.3f}".format(model_analysis["precision"]))
            print("Recall :    {:.3f}".format(model_analysis["recall"]))
            print("f1_score :  {:.3f}".format(model_analysis["f1_score"]))
            '''

        estimators = meta_classifier.PrepareModelsForMetaClassifierVoting(g_classifiers)
        meta_voting = meta_classifier.MetaClassifierVoting(estimators, data_splitter=ds, params={'voting': 'soft'})
        meta_voting.build()
        meta_voting.fit()
        metamodel_analysis = meta_voting.get_analysis()
        '''
        print("* Precision : {:.3f}".format(metamodel_analysis["precision"]))
        print("* Recall :    {:.3f}".format(metamodel_analysis["recall"]))
        print("* f1_score :  {:.3f}".format(metamodel_analysis["f1_score"]))
        '''
        assert(metamodel_analysis["precision"] == pytest.approx(0.620, 0.1)) # to investigate
        assert(metamodel_analysis["recall"] == pytest.approx(0.969, 0.1)) # to investigate
        assert(metamodel_analysis["f1_score"] == pytest.approx(0.756, 0.1)) # to investigate