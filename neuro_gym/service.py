from __future__ import annotations
import logging
import importlib
import inspect
import uuid
import time
import re
import os
import sys
import asyncio
from enum import Enum
from abc import abstractmethod
from typing import Dict, Type, Any, Optional, List, Callable, Tuple, Type
from logging.handlers import QueueHandler, RotatingFileHandler
from multiprocessing import Process, Queue, Event, synchronize, Manager
from threading import Thread
from asyncio import Task, AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field, model_validator

settings = importlib.import_module('settings')

logger = logging.getLogger(__name__)


def handler(cls_service: Type[ServiceBase], cls_command: Type[Command], 
            type_command: TypeCommand):
    """Декоратор для регистрации обработчиков команд.
    
    Args:
        command: Тип команды.
        service: Класс сервиса, которому принадлежит обработчик.
        type_command: Тип сообщения.
    """
    def decorator(func: Callable) -> Callable:
        func._handler_metadata = {
            'cls_service': cls_service,
            'cls_command': cls_command,
            'type_command': type_command,
            'is_coroutine': inspect.iscoroutinefunction(func)
        }
        def wrapper(*args, **kwargs):
            obj_service: ServiceBase = args[0]
            obj_cmd: Command = args[1]
            sender = obj_cmd.sender
            type_command: TypeCommand = func._handler_metadata['type_command']
            cls_command: Type[Command] = func._handler_metadata['cls_command']
            is_coroutine: bool = func._handler_metadata['is_coroutine']
            try:
                if is_coroutine:
                    future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), obj_service._loop)
                    res = future.result()
                else:
                    res = func(*args, **kwargs)
                if res is None:
                    return res
                res = cls_command(response=res) if not isinstance(res, Command) else res
                res.status = StatusCommand.SUCCESS
            except Exception as e:
                logger.error(e)
                res = cls_command()
                res.status = StatusCommand.ERROR
                res.response = [
                    { 'error': str(e) }
                ]
            if type_command == TypeCommand.REQUEST:
                res.type = TypeCommand.REPLY
                obj_service.send_to(sender, res)
            return res
        cls_service._register_handler(cls_command, type_command, wrapper)
        return wrapper
    return decorator


class TypeCommand(str, Enum):
    """ Типы комманд. 
    
        Тип `request` заставляет обработчик отправлять ответ 
        отправителю на его обработчик `reply` команд. Выполняет задачи в отдельном потоке.
            
        Тип `reply` принимает обработанные запросы от `request`. Выполняется в отдельном потоке.
            Не отправляет обратно ответ.
    """
    
    REQUEST = 'request'
    REPLY = 'reply'


class StatusCommand(str, Enum):
    """ Статусы ответных комманд. """
    
    SUCCESS = 'success' # команда выполнилась успешно
    PROCESSING = 'processing' # команда выполняется
    ERROR = 'error' # ошибка при выполнение команды


class Command(BaseModel):
    """ Базовый класс для комманд. """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cmd: str = ''
    sender: str = ''
    recipient: str = ''
    type: Optional[TypeCommand] = None
    params: Dict = Field(default_factory=dict)
    response: List[Any] = Field(default_factory=list)
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    status: Optional[StatusCommand] = None
    
    @classmethod
    def _normalize_id(cls) -> str:
        """ Перевод имени класса в SnakeCase. """
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__)
        return snake.lower()
    
    @model_validator(mode='after')
    def _post_process(self) -> Command:
        self.cmd = self._normalize_id()
        return self
    
    def set_is_request(self) -> Command:
        self.type = TypeCommand.REQUEST
        return self
    
    def set_is_reply(self) -> Command:
        self.type = TypeCommand.REPLY
        return self
    
    def set_status_success(self) -> Command:
        self.status = StatusCommand.SUCCESS
        return self
    
    def set_status_processing(self) -> Command:
        self.status = StatusCommand.PROCESSING
        return self
    
    def set_status_error(self) -> Command:
        self.status = StatusCommand.ERROR
        return self


class WorkerFilter(logging.Filter):
    """ Фильтр для добавления название сервиса в запись. """
    
    def __init__(self, service_id):
        super().__init__()
        self.service_id = service_id
    
    def filter(self, record):
        record.service_id = self.service_id
        return True


class LoggerListener(Thread):
    """ Получатель логов из подпроцессов. """
    
    def __init__(self, log_queue: Queue):
        """

        Args:
            log_queue (Queue): Очередь для лога.
        """ 
        self._log_queue = log_queue
        self._handlers: Dict[str, RotatingFileHandler] = {}
        self._formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        super().__init__(name=self.__class__.__name__, daemon=True)
    
    def run(self):
        """ Получает логи каждого подпроцесса 
        и распределяет по отдельным файлам. """
        if not settings.LOG_DIR.exists():
            settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                record = self._log_queue.get()
                if record is None:
                    break
                service_id = getattr(record, 'service_id', 'unknown')
                if service_id not in self._handlers:
                    log_app_dir = settings.LOG_DIR / service_id.lower()
                    if not log_app_dir.exists():
                        log_app_dir.mkdir(parents=True, exist_ok=True)
                    filename = log_app_dir / f'{service_id}.log'.lower()
                    handler = RotatingFileHandler(
                        filename=filename, encoding='utf-8', 
                        maxBytes=settings.LOG_FILE_SIZE, 
                        backupCount=settings.LOG_FILES_BACKUP
                    )
                    handler.setFormatter(self._formatter)
                    self._handlers[service_id] = handler
                handler = self._handlers[service_id]
                handler.emit(record)
            except Exception as e:
                print('{}: {}'.format(__class__.__name__, e))
    
    def close(self):
        """ Посылает сигнал завершения работы логера. """
        self._log_queue.put(None)


class RouterTasks(object):
    
    tasks: Dict[Type[Command], Callable] = {}
    
    @classmethod
    def get(cls, cmd: Command) -> Optional[Callable]:
        return cls.tasks.get(cmd.__class__.__name__)
    
    @classmethod
    def add(cls, cls_cmd: Type[Command], func: Callable):
        cls.tasks[cls_cmd.__name__] = func
    
    @classmethod
    def delete(cls, cls_cmd: Type[Command]):
        del cls.tasks[cls_cmd.__name__]


class RootService(object):
    """ Главный сервис для управления подпроцессами. """
    
    services: Dict[str, Type[ServiceBase]] = {}
    
    def __init__(self):
        """

        Args:
            log_queue (Queue): Очередь для лога.
        """
        self._manager = Manager()
        self._log_queue = self._manager.Queue()
        self._services: Dict[str, ServiceBase] = {}
        self._mails: Dict[str, Queue] = self._manager.dict()
        self._run_root = self._manager.Event()
        self._logger_listener = LoggerListener(self._log_queue)
        self._th_handle_cpu_task = Thread(target=self._handle_cpu_task, daemon=True, name='handle_cpu_task')
        self._queue_cpu_command = self._manager.Queue()
        self._cpu_tasks: List[Process] = []
        self.logger: logging.Logger = None
    
    def _configurer_queue_logger(self):
        """ Настройка логера для главного сервиса. """
        self.logger = logging.getLogger()
        self.logger.setLevel(settings.LOG_LEVEL)
        queue_handler = QueueHandler(self._log_queue)
        queue_handler.addFilter(WorkerFilter(self.__class__.__name__))
        self.logger.addHandler(queue_handler)
    
    def _handle_cpu_task(self):
        while True:
            try:
                cmd = self._queue_cpu_command.get()
                if cmd is None:
                    break
                logger.debug('Received cpu task: {}'.format(cmd))
                func = RouterTasks.get(cmd)
                if not func:
                    continue
                for i, task in enumerate(list(self._cpu_tasks)):
                    if not task.is_alive():
                        self._cpu_tasks.pop(i)
                proc = Process(target=func, args=[cmd, *cmd.params.args], daemon=True)
                proc.start()
                self._cpu_tasks.append(proc)
            except Exception as e:
                logger.error('{}: {}'.format(self.__class__.__name__, e))
    
    def send_to(self, service: str, data: Any):
        """Отправляет данные в сервис.

        Args:
            service (str): Название сервиса отправления.
            data (Any): Данные.
        """  
        if isinstance(data, Command):
            data.sender = self.__class__.__name__
            data.recipient = service
        self._mails[service].put(data)
    
    def start_services(self):
        """ Запуск всех сервисов. """
        self._run_root.set()
        self._configurer_queue_logger()
        self._logger_listener.start()
        self._th_handle_cpu_task.start()
        for key in self.services.keys():
            self._mails[key] = self._manager.Queue()
        for key, service in self.services.items():
            self._services[key] = service()
            self._services[key].queue = self._manager.Queue()
            self._services[key]._mails = self._mails
            self._services[key]._queue_cpu_command = self._queue_cpu_command
            self._services[key]._log_queue = self._log_queue
            self._services[key]._common_queue = self._mails[key]
            self._services[key]._run_root = self._run_root
            self._services[key]._run_service = Event()
            self._services[key]._run_service.clear()
            self._services[key].start()
    
    def join(self):
        """ Ожидание остановки сервиса. """
        for service in self._services.values():
            service.wait()
    
    def close(self):
        """ Отправляет сигнал остановки всем сервисам. """
        for service in self._services.values():
            if service._run_service.is_set():
                continue
            service.close_service()
        self._queue_cpu_command.put(None)
        self._cpu_tasks.clear()


class ServiceBase(Process):
    """ Базовый сервис для реализации отдельного подпроцесса. """
    
    handlers: Dict[Tuple[Command, TypeCommand], Callable] = {}
    
    MAX_WORKERS = settings.MAX_WORKERS
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        RootService.services[cls.__name__] = cls
    
    def __init__(self, *args, **kwargs):
        """

        Args:
            _services (RootService): Родительский сервис.
            log_queue (Queue): Очередь для лога.
        """
        self.queue: Optional[Queue] = None
        self.logger: logging.Logger = None
        self._common_queue: Optional[Queue] = None
        self._mails: Optional[Dict[str, Queue]] = None
        self._log_queue: Optional[Queue] = None
        self._execute_commands: Optional[Task] = None
        self._loop: Optional[AbstractEventLoop] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._run_service: Optional[synchronize.Event] = None
        self._run_root: Optional[synchronize.Event] = None
        self._queue_cpu_command: Optional[Queue] = None
        self._futures = []
        super().__init__(name=self.__class__.__name__, daemon=True, *args, **kwargs)
    
    @classmethod
    def _register_handler(cls, command: Type[Command], type_command: TypeCommand, handler: Callable):
        """Регистрация обработчика."""
        key = (cls, command, type_command)
        cls.handlers[key] = handler
    
    def _configurer_queue_logger(self):
        """ Настройка логера для текущего сервиса. """
        self.logger = logging.getLogger()
        self.logger.setLevel(settings.LOG_LEVEL)
        queue_handler = QueueHandler(self._log_queue)
        queue_handler.addFilter(WorkerFilter(self.name))
        self.logger.addHandler(queue_handler)
    
    def _handle_command(self):
        """ Обработка команд. """
        while not self._run_service.is_set():
            try:
                msg = self._common_queue.get()
                self.logger.debug('Received message: {}'.format(msg))
                if not self._run_root.is_set():
                    self.close_service()
                    break
                if msg is None:
                    continue
                if ((not isinstance(msg, Command))
                    or (isinstance(msg, Command) and not msg.type)):
                    self.queue.put(msg)
                key = (self.__class__, msg.__class__, msg.type)
                handler = self.handlers.get(key)
                if not handler:
                    self.logger.debug("Не найден обработчик для команды <{}>".format(msg.__class__))
                    continue
                self._executor.submit(handler, self, msg)
            except Exception as e:
                self.logger.error("Ошибка в обработчике команд <{}>".format(e), exc_info=True)
    
    def _run_loop(self):
        """ Запуск цикла событий. """
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
    
    @classmethod
    def service_id(cls) -> str:
        return cls.__name__
    
    @property
    def mails(self):
        return self._mails
    
    def run_cpu_command(self, cmd: Command):
        """Запуск команды для ЦПУ.

        Args:
            cmd (Command): Команда для ЦПУ
        """        
        cmd.sender = self.service_id()
        cmd.recipient = RootService.__name__
        self._queue_cpu_command.put(cmd)
    
    def send_to(self, service: str, data: Any):
        """Отправляет данные в сервис.

        Args:
            service (str): Название сервиса отправления.
            data (Any): Данные.
        """
        if isinstance(data, Command):
            data.sender = self.__class__.__name__
            data.recipient = service
        self._mails[service].put(data)
    
    def run(self):
        """ Точка запуска сервиса. """
        self._configurer_queue_logger()
        self.logger.info('Запуск работы сервиса')
        self._executor = ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS,
            thread_name_prefix=self.__class__.__name__
        )
        self._futures.append(
                self._executor.submit(self._run_loop)
            )
        self._futures.append(
                self._executor.submit(self._handle_command)
            )
        self.run_service()
        self.wait()
        self._futures.clear()
    
    def close_service(self):
        """ Завершение сервиса. """
        try:
            self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass
        self._run_service.set()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._common_queue.put(None)
        time.slee(0.1)
        self.terminate()
    
    def close_all_services(self):
        """ Завершить работу всех сервисов. """
        self._run_root.clear()
        self._log_queue.put(None)
        for mail in self._mails.values():
            mail.put(None)
    
    def wait(self):
        self._run_service.wait()
    
    @abstractmethod
    def run_service(self):
        """ Точка входа для пользовательского кода сервиса. """
        ...