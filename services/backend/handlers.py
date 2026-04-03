import asyncio
import time
import logging
from neuro_gym.service import TypeCommand, handler
from neuro_gym.commands import RunTrainAgent, AsyncTestCommand, ThreadTestCommand
from neuro_gym import (
    NetworkAgent,
    GeneticEvolution,
    EnvGame
)
from services.backend.service import Backend


logger = logging.getLogger(__name__)


@handler(cls_service=Backend, cls_command=AsyncTestCommand, type_command=TypeCommand.REQUEST)
async def async_test_metod(service: Backend, message: AsyncTestCommand):
    await asyncio.sleep(1)
    logger.debug('AsyncTestCommand: Отработала тестовая асинхронная функция')


@handler(cls_service=Backend, cls_command=ThreadTestCommand, type_command=TypeCommand.REQUEST)
def thread_test_metod(service: Backend, message: ThreadTestCommand):
    time.sleep(1)
    logger.debug('ThreadTestCommand: Отработала тестовая потоковая функция')


@handler(cls_service=Backend, cls_command=RunTrainAgent, type_command=TypeCommand.REQUEST)
def run_train(service: Backend, message: RunTrainAgent):
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
                model.age_gen += 10
                model.set_weights_from_vector(i)
                break
            model.save_modal()
        fill_bar += ONE_PART
        best = [
            i.fitness.values[0]
            for i in gen_alg.best_individuals()
        ]
        data = RunTrainAgent(response={
            'progress_train': fill_bar,
            'max_values': gen_alg.max_values.copy(),
            'mean_values': gen_alg.mean_values.copy(),
            'min_values': gen_alg.min_values.copy(),
            'std_values': gen_alg.std_values.copy(),
            'best_individuals': gen_alg.best_individuals(),
            'best_values': best,
        }).set_status_processing().set_is_reply()
        data.params = message.params
        service.send_to(message.sender, data)
    service.send_to(
            message.sender, 
            RunTrainAgent(params=message.params).set_status_success().set_is_reply()
        )