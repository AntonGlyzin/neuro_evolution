from typing import Dict, Union, Optional, Any
import torch
import numpy as np
from neuro_gym.environ import Environ, Complexity


class SimpleBase(Environ):
    
    @property
    def id(self) -> str: 
        """ ИД окружения. """
        ...
    
    @property
    def name(self) -> str: 
        """ Выводимое названия окружения. """
        ...
    
    @property
    def params(self) -> Dict: 
        """ Передаваяемые параметры окружения. """
        ...
    
    @property
    def env_params(self) -> Dict: 
        """ Передаваяемые параметры окружению. """
        return { 'id': self.id, **self.params }
    
    @property
    def complexity(self) -> Complexity: 
        """ Сложность вычисляемого окружения. 
        
        При большей сложности будут задействованно больше нейронов.
        """
        ...
    
    @property
    def number_input_neurons(self) -> int: 
        """ Количество входных нейронов. """
        ...
    
    @property
    def number_output_neurons(self) -> int:
        """ Количество выходных нейронов. """
        ...
    
    @property
    def calc_confidence(self) -> bool: 
        """Использовать ли уверенность шага при нейроэволюции.
        При уверенном шаге будет увеличение награды.
        """
        ...
    
    def update_vector(self, output_vector: Union[np.ndarray, torch.Tensor]) -> Any: 
        """Преобразует выходной вектор из нейросети для метода `action` окружения.

        Args:
            output_vector (Union[np.ndarray, torch.Tensor]): Выходной вектор после нейросети.

        Returns:
            Any: Данные для передачи в `action`.
        """        
        ...
    
    def step_reward(self, observation: np.ndarray) -> Optional[float]: 
        """Выдаваемая награда за каждый шаг в одном эпизоде игры.

        Args:
            observation (np.ndarray): Зона наблюдения на каждом шаге.

        Returns:
            Optional[float]: Награда или пустота.
        """        
        ...
    
    def episode_reward(self, observation: np.ndarray) -> Optional[float]: 
        """Выдаваемая награда за эпизод игры.

        Args:
            observation (np.ndarray): Зона наблюдения на последнем шаге.

        Returns:
            Optional[float]: Награда или пустота.
        """        
        ...