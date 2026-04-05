from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from neuro_gym.service import Command


class AsyncTestCommand(Command): ...


class ThreadTestCommand(Command): ...


class RunTrainAgent(Command): 
    """ Запуск тренировки агента. """
    
    class Params(BaseModel):
        env: object
        num_ten: int
        len_progress: int
        args: List[Any] = Field(default_factory=list)
        kwargs: Dict = Field(default_factory=dict)
    
    class Response(BaseModel):
        progress_train: int
        max_values: List
        mean_values: List
        min_values: List
        std_values: List
        best_individuals: List
        best_values: List
    
    params: Optional[RunTrainAgent.Params] = None
    response: Optional[RunTrainAgent.Response] = None
    
    
    
