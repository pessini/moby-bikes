import sys
import pandas as pd
import datetime

class Score:
    scores = []
    def __init__(self, metric_name, train, validation=None, test=None):
        self.metric_name = metric_name
        self.train = train
        self.validation = validation
        self.test = test
        
        Score.scores.append(self)
    
    def __repr__(self) -> str:
        return f"{self.metric_name} - Train: {self.train} - Val: {self.validation} - Test: {self.test}"

class Experiment:
    def __init__(self, algo_name, hyperparameters, metrics, notes=None):
        #Attributes
        self.algo_name = algo_name
        self.hyperparameters = hyperparameters
        self.metrics = metrics
        self.date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.notes = notes
        
    def __repr__(self) -> str:
        return f"Experiment: {self.algo_name} - Datetime: {self.date} - Hyperparamaters: {self.hyperparameters} - Metrics: {self.metrics} - Notes: {self.notes}"
        
class ExperimentTracker:

    def __init__(self):
        self.experiments = []
        
    def add_experiment(self,value):
        
        if (isinstance(value,Experiment)):
            self.experiments.append(value)
        else:
            print("Cannot add an experiment which is not an Experiment Object!!!")

    def save(self):
        columns_name = ['Title','Date','Predictors','Hyperparameters','Metric','Train','Validation','Test','Details']
        data = self.experiments
        print(data)
        return pd.DataFrame( [vars(e) for e in data] )
    
##########################################################################################

df_tracking = ExperimentTracker()

###############################

rsme = Score('RSME', '3.2223', '2.2323', '4.5623')
exp_linr = Experiment('Linear Regression', 'alpha=5', rsme, 'Hello there LN!')
df_tracking.add_experiment(exp_linr)


mae = Score('MAE', '7482.2223', '243.2323', '4324.5623')
print(mae.scores)
exp_rf = Experiment('Random Forest','num_leafs=5',mae,'Hello there RF!')
df_tracking.add_experiment(exp_rf)

##############################################################

print('\n')
df = df_tracking.save()
print('\n')
print(df)
