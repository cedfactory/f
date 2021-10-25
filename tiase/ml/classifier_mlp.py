from sklearn.neural_network import MLPClassifier
from . import classifier,analysis

'''
MLPClassifier

Input:
- hidden_layer_sizes \in N+, default=100
- activation \in {'identity', 'logistic', 'tanh', 'relu'}, default='relu'
- solver \in {'lbfgs', 'sgd', 'adam'}, default='adam'

ref : https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html
'''
class ClassifierMLP(classifier.Classifier):
    def __init__(self, dataframe, data_splitter, params = None):
        super().__init__(dataframe, data_splitter, params)

        self.hidden_layer_sizes = 100
        self.activation = 'relu'
        self.solver = 'adam'
        if params:
            self.hidden_layer_sizes = params.get("hidden_layer_sizes", self.hidden_layer_sizes)
            self.activation = params.get("activation", self.activation)
            self.solver = params.get("solver", self.solver)

    def get_param_grid(self):
        return {'hidden_layer_sizes': [50, 75, 100, 125, 150, 200, 250, 300],
        'activation': ['identity', 'logistic', 'tanh', 'relu'],
        'solver': ['lbfgs', 'sgd', 'adam']
        }

    def get_model(self):
        return self.model

    def build(self):
        self.model = MLPClassifier(hidden_layer_sizes=self.hidden_layer_sizes, activation=self.activation, solver=self.solver)

    def fit(self):
        self.build()
        self.model.fit(self.data_splitter.X_train,self.data_splitter.y_train)
        
    def get_analysis(self):
        y_test_pred, y_test_prob = classifier.get_pred_and_prob_with_predict_pred_and_predict_proba(self.model, self.data_splitter)
        return analysis.classification_analysis(self.data_splitter.X_test, self.data_splitter.y_test, y_test_pred, y_test_prob)

    def save(self, filename):
        print("ClassifierMLP.save() is not implemented")

    def load(self, filename):
        print("ClassifierMLP.load() is not implemented")
