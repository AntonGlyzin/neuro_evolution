from __future__ import annotations
import torch
import numpy as np
from abc import abstractmethod
from enum import IntEnum
from typing import Union, Dict, Any, Optional
from gymnasium import Env
import gymnasium as gym
import importlib

settings = importlib.import_module('settings')


class Complexity(IntEnum):
    """Сложность окружающей среды. 
    Чем больше признаков поступает в нейронную сеть, тем больше 
    должна выставляться сложность.
    
    """
    
    LOW = 2
    MEDIUM = 4
    HIGH = 8


class Environs(object):
    """ Список настроеек виртуальных окружений. """
    
    elements: Dict[str, Environ] = {}
    
    @classmethod
    def get(cls, key: Union[str, int]) -> Optional[Environ]:
        """Получает окружение по индексу.

        Args:
            key (Union[str, int]): Индекс.

        Returns:
            Environs: Окружение.
        """        
        if key is str:
            return cls.elements.get(key)
        return list(cls.elements.values())[key]
    
    @classmethod
    def len(cls) -> int:
        """ Количество окружений. """        
        return len(cls.elements)
    
    @classmethod
    def iter(cls):
        return iter(cls.elements.values())


class EnvGame(object):
    """ Виртуальное окружение для агента. """
    
    def __init__(self, env: Environ, **extra_params):
        self._game: Optional[Env] = None
        self._env = env
        self._extra_params = extra_params
    
    def game(self) -> Env:
        if self._game:
            self._game.close()
        self._game = gym.make(**self._env.env_params, **self._extra_params)
        self._game.reset()
        return self._game
    
    def close(self):
        self._game.close()
        self._game = None
    
    def __enter__(self):
        return self.game()
    
    def __exit__(self, exc_type, exc, tb):
        self.close()


class Environ(object):
    """ Базовые настройки виртуального окружения. """
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        obj = cls()
        if obj.id:
            Environs.elements[obj.id] = obj
    
    @property
    def statistic_folder(self) -> str:
        folder = (settings.STATISTIC_DIR / self.id)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        return settings.STATISTIC_DIR / self.id
    
    @property
    @abstractmethod
    def id(self) -> str: 
        """ ИД окружения. """
        ...
    
    @property
    @abstractmethod
    def name(self) -> str: 
        """ Выводимое названия окружения. """
        ...
    
    @property
    @abstractmethod
    def params(self) -> Dict: 
        """ Передаваяемые параметры окружения. """
        ...
    
    @property
    def env_params(self) -> Dict: 
        """ Передаваяемые параметры окружению. """
        return { 'id': self.id, **self.params }
    
    @property
    @abstractmethod
    def complexity(self) -> Complexity: 
        """ Сложность вычисляемого окружения. 
        
        При большей сложности будут задействованно больше нейронов.
        """
        ...
    
    @property
    @abstractmethod
    def number_input_neurons(self) -> int: 
        """ Количество входных нейронов. """
        ...
    
    @property
    @abstractmethod
    def number_output_neurons(self) -> int:
        """ Количество выходных нейронов. """
        ...
    
    @property
    @abstractmethod
    def calc_confidence(self) -> bool: 
        """Использовать ли уверенность шага при нейроэволюции.
        При уверенном шаге будет увеличение награды.
        """
        ...
    
    @abstractmethod
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