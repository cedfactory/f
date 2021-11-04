import xml.etree.cElementTree as ET
from tiase.fimport import fimport,visu
from tiase.fdatapreprocessing import fdataprep
from tiase.findicators import findicators
from tiase.ml import data_splitter,classifiers_factory,analysis
from datetime import datetime
import os
from rich import print,inspect

def out(msg):
    print(msg)

def execute(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    
    if root.tag != "dings":
        return 1

    ding_msg = '''
   _ _         
 _| |_|___ ___ 
| . | |   | . |
|___|_|_|_|_  |
          |___|'''
    for ding in root.findall('ding'):
        export_root = ding.get("export", "./")
        if export_root and not os.path.isdir(export_root):
            os.mkdir(export_root)

        def get_full_path(filename):
            return export_root + '/' + filename

        start = datetime.now()
        out(ding_msg)

        # import
        import_node = ding.find('import')
        if import_node is not None:
            value = import_node.get("value", None)
            import_filename = import_node.get("filename", None)
            export_filename = import_node.get("export", None)
            if value:
                out("value : {}".format(value))
                df = fimport.get_dataframe_from_yahoo(value)
            elif import_filename:
                out("filename : {}".format(import_filename))
                df = fimport.get_dataframe_from_csv(import_filename)
                value = "" # value is used as name to export files, so we can't leave it with None value
            out(df.head())

            if export_filename:
                df.to_csv(get_full_path(export_filename))

        # indicators
        features_node = ding.find('features')
        if features_node is not None:
            features = features_node.get("indicators", None)
            target = features_node.get("target", None)
            export_filename = features_node.get("export", None)
            if target:
                all_features = []
                if features:
                    all_features = features.split(',')
                all_features.append(target)
                #target = target[0] # keep the only one target
                out("Using the following technical indicators : {}".format(all_features))
                df = findicators.add_technical_indicators(df, all_features)
                findicators.remove_features(df, ["open", "high", "low", "adj_close", "volume", "dividends", "stock_splits"])
                df = fdataprep.process_technical_indicators(df, ['missing_values'])
                if export_filename:
                    df.to_csv(get_full_path(export_filename))
                    for indicator in df.columns:
                        visu.display_from_dataframe(df, indicator, get_full_path(indicator+'.png'))
            out(df.head())

        # preprocessing
        preprocessing_node = ding.find('preprocessing')
        if preprocessing_node is not None:
            export_filename = preprocessing_node.get("export", None)
            
            # outliers
            outliers_node = preprocessing_node.find('outliers')
            if outliers_node is not None:
                out(outliers_node.get("method", None))
                method = outliers_node.get("method", None)
                if method is not None:
                    out("[PREPROCESSING] outliers : {}".format(method))
                    df = fdataprep.process_technical_indicators(df, [method])
                    df = fdataprep.process_technical_indicators(df, ['missing_values'])

            # transformations
            transformations_node = preprocessing_node.find('transformations')
            if transformations_node is not None:
                transformations = transformations_node.findall('transformation')
                for transformation in transformations:
                    method = transformation.get("method", None)
                    indicators = transformation.get("indicators", None)
                    if method is not None and indicators is not None:
                        out("[PREPROCESSING] transformation {} for {}".format(method, indicators))
                        indicators = indicators.split(',')
                        df = fdataprep.process_technical_indicators(df, ["transformation_"+method], indicators)
                        df = fdataprep.process_technical_indicators(df, ['missing_values'])

            # discretizations
            discretizations_node = preprocessing_node.find('discretizations')
            if discretizations_node is not None:
                discretizations = discretizations_node.findall('discretization')
                for discretization in discretizations:
                    indicators = discretization.get("indicators", None)
                    method = discretization.get("method", None)
                    if indicators is not None and method is not None:
                        out("[PREPROCESSING] discretization {} for {}".format(method, indicators))
                        indicators = indicators.split(',')
                        df = fdataprep.process_technical_indicators(df, ["discretization_"+method], indicators)
                        df = fdataprep.process_technical_indicators(df, ['missing_values'])

            if export_filename:
                df.to_csv(get_full_path(export_filename))
                for indicator in df.columns:
                    visu.display_from_dataframe(df, indicator, get_full_path(value + '_preprocessing_'+indicator+'.png'))

        # feature engineering
        featureengineering_node = ding.find('featureengineering')
        if featureengineering_node is not None:
            export_filename = featureengineering_node.get("export", None)

            # reduction
            reduction_node = featureengineering_node.find('reduction')
            if reduction_node is not None:
                method = reduction_node.get("method", None)
                if method is not None:
                    out("[FEATURE ENGINEERING] reduction : {}".format(method))

            if export_filename:
                df.to_csv(get_full_path(export_filename))
                for indicator in df.columns:
                        visu.display_from_dataframe(df, indicator, get_full_path(value + '_featureengineering_'+indicator+'.png'))

        # learning model
        classifiers_node = ding.find('classifiers')
        if classifiers_node:
            ds = data_splitter.DataSplitterTrainTestSimple(df, target="target", seq_len=21)
            ds.split(0.7)
            library_models = {}
            test_vs_pred = []
            for classifier in classifiers_node:
                classifier_id = classifier.get("id", None)
                out("[CLASSIFIER] Treating {}".format(classifier_id))
                classifier_type = classifier.get("type", None)
                export_filename = classifier.get("export", None)

                parameters_node = classifier.find('parameters')
                params = {}
                if parameters_node:
                    for parameter in parameters_node:
                        parameter_name = parameter.get("name", None)
                        parameter_value = parameter.get("value", None)
                        if parameter_name != None and parameter_value != None:

                            def get_classifier_from_name(classifier_name):
                                classifier_value = library_models[classifier_name]
                                if classifier_value != None:
                                    out("{} found ({})".format(classifier_name, classifier_value))
                                else:
                                    out("!!! {} not found !!!".format(parameter_value))
                                return classifier_value

                            # replace classifier name with classifier model
                            if parameter_name == "classifier":
                                parameter_value = get_classifier_from_name(parameter_value)

                            elif parameter_name == "classifiers":
                                classifier_names = parameter_value.split(',')
                                parameter_value = [(classifier_name, get_classifier_from_name(classifier_name)) for classifier_name in classifier_names]
                                out(parameter_value)

                            if parameter_value:
                                params[parameter_name] = parameter_value

                model = classifiers_factory.ClassifiersFactory.get_classifier(type=classifier_type, params=params, data_splitter=ds)
                model.fit()
                library_models[classifier_id] = model

                model_analysis = model.get_analysis()
                out("Accuracy : {:.2f}".format(model_analysis["accuracy"]))
                out("Precision : {:.2f}".format(model_analysis["precision"]))
                out("Recall : {:.2f}".format(model_analysis["recall"]))
                out("f1_score : {:.2f}".format(model_analysis["f1_score"]))
                if export_filename:
                    model.save(get_full_path(export_filename))

                test_vs_pred.append(analysis.testvspred(classifier_id, model_analysis["y_test"], model_analysis["y_test_prob"]))

            analysis.export_roc_curves(test_vs_pred, export_root + "/roc_curves.png", "")

        end = datetime.now()
        out("elapsed time : {}".format(end-start))

    return 0
