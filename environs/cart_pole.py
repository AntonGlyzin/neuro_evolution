from typing import Dict, Union
import torch
import numpy as np
from neuro_gym.environ import Environ, Complexity


class CartPole(Environ):
    
    @property
    def id(self) -> str:
        return 'CartPole-v1'
    
    @property
    def name(self) -> str:
        return 'Тележка на столбе'
    
    @property
    def params(self) -> Dict:
        return {'id': self.id}
    
    @property
    def complexity(self) -> int:
        return Complexity.LOW
    
    @property
    def number_input_neurons(self) -> int: 
        return 4
    
    @property
    def number_output_neurons(self) -> int: 
        return 2
    
    @property
    def calc_confidence(self) -> bool: 
        return True
    
    def update_vector(self, output_vector: Union[np.ndarray, torch.Tensor]) -> int:
        return torch.argmax(output_vector, dim=-1).item()