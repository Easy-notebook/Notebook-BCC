
from DCLSAgents.agents.tool.generalAgent import GeneralAgent
from app.core.config import llm

def generate_question_choice_map(context):
    # general_agent = GeneralAgent(llm=llm)
    # question_choice_map = general_agent.generate_question_choice_map_cli(context)
    question_choice_map = [                                                                                                       
                     {                                                                                                    
                        "target": "SalePrice",                                                                            
                        "problem_description": "Given the dataset with various house features, we want to build a model to predict the sale price of a house in Ames, Iowa.",                                                      
                        "problem_name": " House Sale Price Prediction"                                                
                     },                                                                                                   
                     {                                                                                                    
                        "target": "Overall Qual",                                                                         
                        "problem_description": "We need to analyze the relationship between the overall quality of houses in the dataset and other factors like neighborhood and building type.",                                 
                        "problem_name": " House Quality Analysis"                                                     
                     },                                                                                                   
                     {                                                                                                    
                        "target": "Neighborhood",                                                                         
                        "problem_description": "Suppose we are interested in understanding which neighborhoods in the Ameshousing dataset are more popular based on house features and sale prices.",                             
                        "problem_name": " Neighborhood Popularity Study"                                              
                     }                                                                                                    
                  ]    
    return question_choice_map
