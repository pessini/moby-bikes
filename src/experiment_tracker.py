from calendar import c
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
    
class Idea:
    def __init__(self, idea: str, outcome: str, learning: str):
        self.idea = idea
        self.outcome = outcome
        self.learning = learning
        
    def __repr__(self) -> str:
        return f"Idea: {self.idea} - Potential Outcome: {self.outcome} - Learning: {self.learning}"
        
class ExperimentTracker:

    def __init__(self):
        self.experiments = []
        self.ideas = []
        
    def add_experiment(self,value):  # sourcery skip: raise-specific-error
        if (isinstance(value,Experiment) and value not in self.experiments):
            self.experiments.append(value)
        else:
            raise Exception("Cannot add an experiment which is not an Experiment Object!!!")

    def new_idea(self,value):
        if (isinstance(value,Idea) and value not in self.ideas):
            self.ideas.append(value)
        else:
            raise Exception("Cannot add a new idea which is not an Idea Object!!!")
        
    def to_dataframe(self, type='experiments'):
        # columns_name = ['Title','Date','Predictors','Hyperparameters','Metric','Train','Validation','Test','Details']
        data = self.experiments if (type == "experiments") else self.ideas
        return pd.DataFrame( [vars(e) for e in data])
    
    def to_csv(self, filename: str, type='experiments'):
        if (type == "experiments"):
            df_experiments = self.to_dataframe()
            df_experiments.to_csv(filename, index=False)
        elif (type == "ideas"):
            df_ideas = self.to_dataframe(type='ideas')
            df_ideas.to_csv(filename, index=False)
        else:
            raise Exception("Cannot save the dataframe to a csv file. Type must be either 'experiments' or 'ideas'")

    def to_excel(self, filename):
        df_experiments = self.to_dataframe()
        df_ideas = self.to_dataframe(type='ideas')
        with pd.ExcelWriter(filename) as writer:
            if (df_ideas.shape[0] > 0):
                df_ideas.to_excel(writer, sheet_name='Ideas', index=False) 
            if (df_experiments.shape[0] > 0):
                df_experiments.to_excel(writer, sheet_name='Experiments', index=False)
            # writer.save()
    
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################

# df_tracking = ExperimentTracker()

###############################

###############################
######## Experiment 1 #########
###############################
# rsme = Score('RSME', '3.2223', '2.2323', '4.5623')
# exp_linr = Experiment('Linear Regression','["temp","rhum","wdsp"]', 'alpha=5', rsme, 'Hello there LN!')
# df_tracking.add_experiment(exp_linr)

###############################
######## Experiment 2 #########
###############################
# exp_linr2 = Experiment('Linear Regression','["temp","rhum","wdsp"]', 'alpha=10', rsme, 'LN! alpha is 10 now')
# df_tracking.add_experiment(exp_linr2)

###############################
######## Experiment 3 #########
###############################
# mae_rf = Score('MAE', '7482.2', '243.23', '424.523')
# rsm_rf = Score('RSM', '72.2', '24.23', '4.5')
# metrics_rf = [mae_rf,rsm_rf]
# exp_rf = Experiment('Random Forest', '["temp","rhum","wdsp"]', 'num_leafs = 5',metrics_rf,'Hello there RF!')
# df_tracking.add_experiment(exp_rf)

##############################################################

# idea1 = Idea("Predicting the number of deaths in a given country", "Deaths", "Deaths")
# df_tracking.new_idea(idea1)

# idea2 = Idea("Predicting the number of confirmed cases in a given country", "Confirmed cases", "Confirmed cases")
# df_tracking.new_idea(idea2)

# print(df_tracking.__dict__)
# print('\n')
# df_tracking.to_excel('tracking.xlsx')

# df_tracking.to_csv('ideas.csv', type='ideas')


# df = df_tracking.to_dataframe()
# # print(df)
# df.to_csv('experiment.csv', index=False)
# df.to_excel('tracking.xlsx', sheet_name='ML-Experiment', index=False)
# https://www.delftstack.com/howto/python-pandas/split-column-in-python-pandas/