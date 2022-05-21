import sys
import pandas as pd
import datetime
from typing import Union

class Score:
    """
    Creates a new object to store scores from different metrics

    Returns:
        __repr__: str in a dic structure to simplify further manipulations
    """
    def __init__(self, metric_name, train, validation=None, test=None):
        self.metric_name = metric_name
        self.train = train
        self.validation = validation
        self.test = test

    def __repr__(self) -> str:
        # return a string in a dic structure to simplify further manipulations
        return f"{{ 'metric': {self.metric_name}, 'train': {self.train},  'validation': {self.validation}, 'test': {self.test} }}"

class Experiment:
    """
    
    """
    def __init__(self, algorithm, predictors, hyperparameters, score=Union[Score, list], notes=None):
        # Union[int, float] from Python 3.10 onwards can be replace by "|" (e.g: int | float)

        if(isinstance(score, list)):
            assert all(isinstance(n, Score) for n in score), "All elements in the list must be a Score object!!!"
        else:
            assert isinstance(score, Score), "Metric Score must be a Score object!!!"

        #Attributes
        self.algorithm = algorithm
        self.predictors = predictors
        self.hyperparameters = hyperparameters
        self.dict_scores = score
        self.date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.notes = notes
        
    def __repr__(self) -> str:
        return f"Experiment: {self.algorithm} - Datetime: {self.date} - Notes: {self.notes}"
        
class ExperimentTracker:

    def __init__(self):
        self.experiments = []
        
    def add_experiment(self,value):  # sourcery skip: raise-specific-error
        if (isinstance(value,Experiment)):
            self.experiments.append(value)
        else:
            raise Exception("Cannot add an experiment which is not an Experiment Object!!!")

    def to_dataframe(self):
        # columns_name = ['Title','Date','Predictors','Hyperparameters','Metric','Train','Validation','Test','Details']
        data = self.experiments
       # data => List of Experiment()
        return pd.DataFrame( [vars(e) for e in data])
    
##########################################################################################

df_tracking = ExperimentTracker()

###############################

###############################
######## Experiment 1 #########
###############################
rsme = Score('RSME', '3.2223', '2.2323', '4.5623')
exp_linr = Experiment('Linear Regression','["temp","rhum","wdsp"]', 'alpha=5', rsme, 'Hello there LN!')
df_tracking.add_experiment(exp_linr)

###############################
######## Experiment 2 #########
###############################
exp_linr2 = Experiment('Linear Regression','["temp","rhum","wdsp"]', 'alpha=10', rsme, 'LN! alpha is 10 now')
df_tracking.add_experiment(exp_linr2)

###############################
######## Experiment 3 #########
###############################
mae_rf = Score('MAE', '7482.2', '243.23', '424.523')
rsm_rf = Score('RSM', '72.2', '24.23', '4.5')
metrics_rf = [mae_rf,rsm_rf]
exp_rf = Experiment('Random Forest', '["temp","rhum","wdsp"]', 'num_leafs = 5',metrics_rf,'Hello there RF!')
df_tracking.add_experiment(exp_rf)

##############################################################
df = df_tracking.to_dataframe()
# print(df)
df.to_csv('experiment.csv', index=False)
df.to_excel('tracking.xlsx', sheet_name='ML-Experiment', index=False)
# https://www.delftstack.com/howto/python-pandas/split-column-in-python-pandas/