from __future__ import annotations
from typing import Optional
import importlib
from neuro_gym.service import ServiceBase
from neuro_gym.commands import AsyncTestCommand, ThreadTestCommand
from services.frontend.gui import GUIFrame

settings = importlib.import_module('settings')


class Frontend(ServiceBase):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form: Optional[GUIFrame] = None
    
    @property
    def backend_id(self):
        from services.backend.service import Backend
        return Backend.service_id()
    
    def run_service(self):
        import logging
        logging.getLogger('matplotlib').setLevel(logging.INFO)
        logging.getLogger('PIL').setLevel(logging.INFO)
        logging.getLogger('PIL.PngImagePlugin').setLevel(logging.INFO)
        import matplotlib
        matplotlib.use('TkAgg')
        self.frame = GUIFrame(self)
        async_request = AsyncTestCommand().set_is_request()
        self.send_to(self.backend_id, async_request)
        thread_request = ThreadTestCommand().set_is_request()
        self.send_to(self.backend_id, thread_request)
        self.frame.start()