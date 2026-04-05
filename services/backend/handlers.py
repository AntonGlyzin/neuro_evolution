import asyncio
import time
import logging
import importlib
from neuro_gym.service import TypeCommand, handler
from neuro_gym.commands import AsyncTestCommand, ThreadTestCommand
from services.backend.service import Backend

settings = importlib.import_module('settings')


logger = logging.getLogger(__name__)


@handler(cls_service=Backend, cls_command=AsyncTestCommand, type_command=TypeCommand.REQUEST)
async def async_test_metod(service: Backend, message: AsyncTestCommand):
    await asyncio.sleep(1)
    logger.debug('AsyncTestCommand(id={}): Отработала тестовая асинхронная функция'.format(message.id))


@handler(cls_service=Backend, cls_command=ThreadTestCommand, type_command=TypeCommand.REQUEST)
def thread_test_metod(service: Backend, message: ThreadTestCommand):
    time.sleep(1)
    logger.debug('ThreadTestCommand(id={}): Отработала тестовая потоковая функция'.format(message.id))