from typing import Dict, Union
import torch
import numpy as np
from neuro_gym.environ import Environ, Complexity


class LunarLander(Environ):
    
    @property
    def id(self) -> str:
        return 'LunarLander-v3'
    
    @property
    def name(self) -> str:
        return 'Лунный посадочный модуль'
    
    @property
    def params(self) -> Dict:
        return {
            'id': self.id,
            'continuous': False, 
            'gravity': -10.0, # 0 до -12.0
            'enable_wind': False,  # случайным образом в диапазоне от -9999 до 9999
            'wind_power': 15.0,  #  от 0 до 20.0
            'turbulence_power': 1.5 #  от 0 до 2.0
        }
    
    @property
    def complexity(self) -> int:
        return Complexity.MEDIUM
    
    @property
    def number_input_neurons(self) -> int: 
        return 8
    
    @property
    def number_output_neurons(self) -> int: 
        return 4
    
    @property
    def calc_confidence(self) -> bool: 
        return False
    
    def update_vector(self, output_vector: Union[np.ndarray, torch.Tensor]) -> int:
        return torch.argmax(output_vector, dim=-1).item()
    
    def episode_reward(self, observation: np.ndarray) -> float:       
        x, y, x_vel, y_vel, angle, ang_vel, left_leg, right_leg = observation
        custom_bonus = 0
        if abs(y_vel) < 0.5:  # Маленькая вертикальная скорость
            custom_bonus += 30
        # Бонус за центр площадки
        if abs(x) < 0.1:
            custom_bonus += 25
        # Штраф за большой угол
        if abs(angle) > 0.5:
            custom_bonus -= 30
        return custom_bonus