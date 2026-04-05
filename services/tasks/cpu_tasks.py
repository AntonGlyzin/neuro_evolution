import logging
import importlib
from typing import Dict
from multiprocessing import Queue
from neuro_gym.commands import RunTrainAgent
from neuro_gym import (
    NetworkAgent,
    GeneticEvolution,
    EnvGame
)

settings = importlib.import_module('settings')

logger = logging.getLogger(__name__)


def run_train(message: RunTrainAgent, mails: Dict[str, Queue], *args, **kwargs):
    num_ten = message.params.num_ten
    env = message.params.env
    model = NetworkAgent(env)
    model.load_modal()
    LEN_BAR = message.params.len_progress
    ONE_PART = LEN_BAR / num_ten
    fill_bar = 0
    for i in range(1, num_ten + 1):
        with EnvGame(env) as game:
            gen_alg = GeneticEvolution(model, game, env)
            gen_alg.create_new_population()
            gen_alg.load_population()
            gen_alg.load_best_population()
            gen_alg.evaluate()
            gen_alg.save_best_individuals()
            gen_alg.save_individuals()
            for i in gen_alg.best_individuals():
                model.number_model = 1
                model.age_gen += settings.MAX_GENERATIONS
                model.set_weights_from_vector(i)
                break
            model.save_modal()
        fill_bar += ONE_PART
        best = [
            i.fitness.values[0]
            for i in gen_alg.best_individuals()
        ]
        data = RunTrainAgent(response={
            'progress_train': int(fill_bar),
            'max_values': gen_alg.max_values.copy(),
            'mean_values': gen_alg.mean_values.copy(),
            'min_values': gen_alg.min_values.copy(),
            'std_values': gen_alg.std_values.copy(),
            'best_individuals': gen_alg.best_individuals(),
            'best_values': best,
        }).set_status_processing().set_is_reply()
        data.params = message.params
        mails[message.sender].put(data)
    mails[message.sender].put(
        RunTrainAgent(params=message.params).set_status_success().set_is_reply()
    )