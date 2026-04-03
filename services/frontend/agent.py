from __future__ import annotations
import numpy as np
import time
import importlib
import matplotlib.pyplot as plt
from typing import List, Callable
from neuro_gym import (
    NetworkAgent,
    Environ,
    EnvGame
)

settings = importlib.import_module('settings')


class Agent(object):
    """ Состояние нейроэволюционной модели. """
    
    def __init__(self, env: Environ, print_console: Callable[[str], None]):
        """

        Args:
            env (Environ): виртуальное окружение.
        """        
        self.env = env
        self.model = NetworkAgent(self.env)
        self.is_now_train = False
        self.progress_train = 0
        self.age_population = 0
        self.max_values = []
        self.mean_values = []
        self.min_values = []
        self.std_values = []
        self.best_values: List[List[float]] = []
        self.best_individuals: List[List[list]] = []
        self.print_console = print_console
    
    def clear(self):
        """ Очищение данных. """
        self.model.init_weights()
        self.progress_train = 0
        self.age_population = 0
        self.max_values = []
        self.mean_values = []
        self.min_values = []
        self.std_values = []
        self.best_values: List[List[float]] = []
        self.best_individuals: List[List[list]] = []
    
    def load(self):
        """ Загрузка статистики. """
        self.model.load_modal()
        if not (self.env.statistic_folder / 'evolution.npz').exists():
            return None
        with np.load(self.env.statistic_folder / 'evolution.npz', allow_pickle=True) as loader:
            self.max_values = loader['max_values'].tolist()
            self.mean_values = loader['mean_values'].tolist()
            self.min_values = loader['min_values'].tolist()
            self.std_values = loader['std_values'].tolist()
            self.best_values = loader['best_values'].tolist()
            self.best_individuals = loader['best_individuals'].tolist()
            self.age_population = int(loader['age_population'])
    
    def save(self):
        """ Сохранение статистики. """
        self.model.save_modal()
        start_index = (
            0
            if len(self.max_values) <= settings.NUMBER_YEARS_ON_GRAPHIC
            else -settings.NUMBER_YEARS_ON_GRAPHIC
        )
        start_ten = (
            0
            if len(self.max_values) <= settings.NUMBER_YEARS_ON_GRAPHIC
            else -int(settings.NUMBER_YEARS_ON_GRAPHIC/10)
        )
        np.savez(self.env.statistic_folder / 'evolution',
            max_values = self.max_values[start_index:],
            mean_values = self.mean_values[start_index:],
            min_values = self.min_values[start_index:],
            std_values = self.std_values[start_index:],
            best_values = self.best_values[start_ten:],
            best_individuals = self.best_individuals[start_ten:],
            age_population = self.age_population
        )
    
    def show_evolution(self):
        """ Визуализация результата. """
        plt.figure(figsize=(12, 5))
        axes = plt.subplot(2, 1, 1)
        start = int(self.age_population - len(self.max_values))
        generations = range(start, self.age_population)
        plt.plot(generations, self.max_values, 'b-', label='Максимальное', linewidth=2, alpha=0.8)
        plt.plot(generations, self.mean_values, 'g-', label='Среднее', linewidth=2, alpha=0.8)
        plt.plot(generations, self.min_values, 'r-', label='Минимальное', linewidth=2, alpha=0.8)
        axes.axhline(color='gray', linestyle='--', alpha=0.5)
        axes.axvline(color='gray', linestyle='--', alpha=0.5, x=start)
        plt.fill_between(generations, 
                        np.array(self.mean_values) - np.array(self.std_values),
                        np.array(self.mean_values) + np.array(self.std_values),
                        alpha=0.2, color='g')
        plt.xlabel('Поколения')
        plt.ylabel('Награда')
        plt.title('Эволюция популяции')
        plt.legend()
        plt.grid(True, alpha=0.3)
        ax = plt.subplot(2, 1, 2)
        best1 = []
        best2 = []
        best3 = []
        for i in self.best_values:
            best1.append(i[0])
            best2.append(i[1])
            best3.append(i[2])
        x = np.arange(len(best1))
        width = 0.3
        ax.set_xticks(x)
        start = int((self.age_population - len(self.max_values)) / 10)
        ax.set_xticklabels([str(i) for i in range(start + 1, start + len(best1)+1)])
        ax.bar(x - width, best1, width=width, label='Лучший 1', alpha=0.8)
        ax.bar(x, best2, width=width, label='Лучший 2', alpha=0.8)
        ax.bar(x + width, best3, width=width, label='Лучший 3', alpha=0.8)
        plt.xlabel('Количество десятилетий')
        plt.ylabel('Максимальная награда за десятилетие')
        plt.title('Лучший результат за десятилетия')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.suptitle('Нейроэволюция моделей', fontsize=16)
        plt.tight_layout()
        plt.show(block=True)
    
    def run_test_agent(self):
        """ Тестовый запуск агента в виртуальной среде. """
        with EnvGame(self.env, render_mode='human') as game:
            observation, _ = game.reset()
            terminated = False
            truncated = False
            total_reward = 0
            steps_confidence = 0
            steps = 0
            while not (terminated or truncated):
                action, confidence = self.model.predict(observation, True)
                observation, reward, terminated, truncated, _ = game.step(action)
                if settings.SHOW_OBSERVATION:
                    self.print_console('\nЗона наблюдения на шаге {}: <{}>'.format(steps, observation))
                time.sleep(.03)
                total_reward += reward
                steps += 1
                if not self.env.calc_confidence:
                    continue
                steps_confidence += confidence
            if self.env.calc_confidence and steps_confidence and (total_reward > 0):
                step_confidence = steps_confidence / steps if steps else 0
                self.print_console("\nСредняя уверенность шага: {}".format(step_confidence))
            if settings.SHOW_OBSERVATION:
                self.print_console('\nЗона наблюдения на последнем шаге: <{}>'.format(observation))
            self.print_console("\nОбщая награда: {}".format(total_reward))
    
    def my_current_model(self):
        """ Информация о текущей модели. """
        num_ten = int(self.model.age_gen / 10)
        text = (
            '\nЭта модель из {} десятилетия. '.format(num_ten)
            +'Особь под номером {}. '.format(self.model.number_model)
            +'Возраст генов особи {} лет.'.format(self.model.age_gen)
        )
        self.print_console(text)