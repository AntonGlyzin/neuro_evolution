from __future__ import annotations
import wx
import os
import sys
import wx.adv
import importlib
from typing import Optional, TYPE_CHECKING, Dict, Type
from neuro_gym.commands import RunTrainAgent
from neuro_gym import Environs
from services.frontend.agent import Agent

if TYPE_CHECKING:
    from services.frontend.service import Frontend

settings = importlib.import_module('settings')


class BaseCommandConsole(object):
    """ Команды управления над главным окном консоли. """
    
    def __init__(self, frame: GUIFrame):
        self.frame = frame
        self.text = ''
        self.min_value = 0
        self.max_value = 0
        self.goto: Optional[BaseCommandConsole] = None
    
    def confirm(self, number: int):
        """Выполнение команды "Подтвердить"

        Args:
            number (int): Выбираемое действие.
        """
        self.frame.print_console('\nВаше действие: {}'.format(number))
        self.execute(number)
        
    
    def execute(self, number: int):
        """Выполнение команды

        Args:
            number (int): Выбираемое действие.
        """        
        raise NotImplementedError


class ActivateTrain(BaseCommandConsole):
    """ Запускает тренировку. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        if self.frame.current_agent.is_now_train:
            self.text = '\nЕще идет тренировка модели...'
            self.goto = ShowActionsEnviron
            return
        self.text = '\nВведите количество десятилетий от 1 до бесконечности'
        self.min_value = 1
        self.max_value = 9999999
    
    def execute(self, number: int):
        request = RunTrainAgent(params={
                'env': self.frame.current_agent.env,
                'num_ten': number,
                'len_progress': self.frame.LENGTH_PROGRESS_BAR,
                'args': [self.frame.service.mails]
            }).set_is_request()
        self.frame.service.run_cpu_command(request)
        self.frame.current_agent.is_now_train = True
        self.frame.current_agent.progress_train = 1
        self.frame.progress_bar.SetValue(1)
        self.frame.print_console('\nНачалось обучение...')
        self.frame.run_cmd_console(ShowActionsEnviron)


class SelectNumberModel(BaseCommandConsole):
    """ Выбирает номер модели для сохранения. """
        
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        self.text = '\nВыберите модель от 1 до 3'
        self.min_value = 1
        self.max_value = 3
        self.select_ten = self.frame.current_command.select_ten
        self.num_ten = self.frame.current_command.num_ten
        self.start = self.frame.current_command.start
    
    def execute(self, number: int):
        self.frame.current_agent.model.age_gen = self.select_ten * 10
        self.frame.current_agent.model.number_model = number
        selected_individ = self.frame.current_agent.best_individuals[self.select_ten-1-self.start][number-1]
        self.frame.current_agent.model.set_weights_from_vector(selected_individ)
        self.frame.current_agent.save()
        if ((self.frame.current_agent.progress_train == self.frame.LENGTH_PROGRESS_BAR)
            and not self.frame.current_agent.is_now_train):
            self.frame.progress_bar.SetValue(0)
            self.frame.current_agent.progress_train = 0
        self.frame.run_cmd_console(ShowActionsEnviron)


class SelectSaveModel(BaseCommandConsole):
    """ Выбирает модель для сохранения. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        self.num_ten = len(self.frame.current_agent.best_individuals)
        if not self.num_ten:
            self.frame.print_console('\nНет обученных агентов')
            return
        self.start = int((self.frame.current_agent.age_population 
                    - len(self.frame.current_agent.max_values)) / 10)
        self.text = '\nВыберите десятилетие от {} до {}'.format(self.start + 1, self.start + self.num_ten)
        self.min_value = self.start + 1
        self.max_value = self.start + self.num_ten
        self.select_ten = 0
    
    def execute(self, number: int):
        self.select_ten = number
        self.frame.run_cmd_console(SelectNumberModel)


class MyCurrentModel(BaseCommandConsole):
    """ Информация о текущей модели. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        self.frame.current_agent.my_current_model()
        self.goto = ShowActionsEnviron
    
    def execute(self, number: int): ...


class RunTestAgent(BaseCommandConsole):
    """ Запустить тест. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        wx.CallAfter(self.frame.current_agent.run_test_agent)
        self.goto = ShowActionsEnviron
    
    def execute(self, number: int): ...


class ShowEvolution(BaseCommandConsole):
    """ Показать график натренированности. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        wx.CallAfter(self.frame.current_agent.show_evolution)
        self.goto = ShowActionsEnviron
    
    def execute(self, number: int): ...


class ShowActionsEnviron(BaseCommandConsole):
    """ Список действий над виртуальным окружением. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        self._actions = {
            ActivateTrain: 'Активировать режим нейроэволюции',
            ShowEvolution: 'Статистика нейроэволюция моделей',
            RunTestAgent: 'Тестовый запуск',
            SelectSaveModel: 'Выбрать другую модель',
            MyCurrentModel: 'Моя текущая модель'
        }
        self._actions_items = list(self._actions.items())
        title = '\n\nСписок действий над <{}>:\n'.format(self.frame.current_agent.env.name)
        self.text = title + '\n'.join(
            [
                f'{i}. {val[1]}'
                for i, val in enumerate(self._actions_items, 1)
            ]
        )
        self.min_value = 1
        self.max_value = len(self._actions)
    
    def execute(self, number: int):
        cls_action = self._actions_items[number-1][0]
        self.frame.run_cmd_console(cls_action)


class ListEnvirons(BaseCommandConsole):
    """ Выводит список виртуальных окружений. """
    
    def __init__(self, frame: GUIFrame):
        super().__init__(frame)
        self.frame.console.Clear()
        self.frame.progress_bar.SetValue(0)
        self.frame.current_agent = None
        list_envs = [
            f'{i}. {val.name}'
            for i, val in enumerate(Environs.iter(), 1)
        ]
        self.text = '\nСписок виртуальных окружений:\n{}'.format('\n'.join(list_envs))
        self.min_value = 1
        self.max_value = Environs.len()
    
    def execute(self, number: int):
        env = Environs.get(number-1)
        self.frame.current_agent = self.frame.agents[env.id]
        self.frame.progress_bar.SetValue(self.frame.current_agent.progress_train)
        if ((self.frame.current_agent.progress_train == self.frame.LENGTH_PROGRESS_BAR)
            and not self.frame.current_agent.is_now_train):
            self.frame.print_console('\nНейроэволюция завершена')
            self.frame.print_console('\nВыберите модель для сохранения')
            self.frame.progress_bar.SetValue(self.frame.LENGTH_PROGRESS_BAR)
            self.frame.run_cmd_console(SelectSaveModel)
            wx.CallAfter(self.frame.current_agent.show_evolution)
            return
        self.frame.current_agent.load()
        self.frame.run_cmd_console(ShowActionsEnviron)


class GUIFrame(wx.Frame):
    """ Главное окно приложения. """
    
    LENGTH_PROGRESS_BAR = 100
    
    def __init__(self, service: Frontend):
        self.app = wx.App()
        wx.Frame.__init__(
            self, None, id=wx.ID_ANY,
            title="Алгоритм нейроэволюции",
            pos=wx.DefaultPosition,
            size=wx.Size(700, 500),
            style=wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.TAB_TRAVERSAL
        )
        self.service = service
        self.Bind(wx.EVT_CLOSE, self._on_close)
        # Запрет изменения размера
        self.SetSizeHints(700, 500, 700, 500)
        # Центрируем окно на экране
        self.CentreOnScreen()
        # Устанавливаем иконку окна
        self.SetIcon(self._create_icon())
        # Создаем панель
        panel = wx.Panel(self)
        # Основной вертикальный sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # ========== Прогресс бар обучения ==========
        self.progress_bar = wx.Gauge( panel, wx.ID_ANY, self.LENGTH_PROGRESS_BAR, 
                                    wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.progress_bar.SetValue( 0 )
        main_sizer.Add( self.progress_bar, 0, wx.ALL|wx.EXPAND, 5 )
        # ========== Многострочное текстовое поле для вывода ==========
        self.console = wx.TextCtrl(
            panel, wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        self.console.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.console.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.console.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_CAPTIONTEXT))
        main_sizer.Add(self.console, 1, wx.ALL | wx.EXPAND, 5)
        # ========== Подпись для поля ввода ==========
        self.user_hint = wx.StaticText(panel, wx.ID_ANY, "Ваше действие:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.user_hint.Wrap(-1)
        main_sizer.Add(self.user_hint, 0, wx.ALL, 5)
        # ========== Поле ввода числа/выбора ==========
        self.user_input = wx.TextCtrl(
            panel, wx.ID_ANY,
            value=wx.EmptyString,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.TE_PROCESS_ENTER  # Добавляем обработку Enter
        )
        self.user_input.SetHint("Введите цифру...")
        # Валидация ввода
        self.user_input.Bind(wx.EVT_TEXT, self._on_text_change)
        self.user_input.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        main_sizer.Add(self.user_input, 0, wx.ALL | wx.EXPAND, 5)
        # Используем горизонтальный sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Кнопка "Подтвердить" - слева
        self.select_btn = wx.Button(panel, wx.ID_ANY, "Подтвердить", wx.DefaultPosition, wx.Size(120, 35), 0)
        self.select_btn.Enable(False)
        self.select_btn.Bind(wx.EVT_BUTTON, self._on_select)
        button_sizer.Add(self.select_btn, 0, wx.ALL, 5)
        # Растягивающий промежуток (толкает кнопку "Назад" вправо)
        button_sizer.AddStretchSpacer()
        # Кнопка "Назад" - справа
        self.back_btn = wx.Button(panel, wx.ID_ANY, "Назад к окружению", wx.DefaultPosition, wx.Size(120, 35), 0)
        self.back_btn.Bind(wx.EVT_BUTTON, self._back_to_environs)
        button_sizer.Add(self.back_btn, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)
        # Устанавливаем sizer для панели
        panel.SetSizer(main_sizer)
        self.Layout()
        # Центрируем окно
        self.Centre(wx.BOTH)
        # Фокус на поле ввода
        self.back_btn.SetFocus()
        # Список агентов.
        self.agents: Dict[str, Agent] = {
            env.id: Agent(env, self.console.AppendText)
            for env in Environs.iter()
        }
        # Текущий агент.
        self.current_agent: Optional[Agent] = None
        # Текущая команда установленная в консоли.
        self.current_command: Optional[BaseCommandConsole] = None
        self.print_console = self.console.AppendText
        self.run_cmd_console(ListEnvirons)
    
    def _create_icon(self):
        """ Создание иконки для окна. """
        try:
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            icon_path = os.path.join(base_path, 'img', 'intelligence.ico')
            icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
            return icon
        except Exception:
            pass
    
    def _on_key_down(self, event):
        """ Обработка нажатия клавиш в поле ввода. """
        key_code = event.GetKeyCode()
        # Разрешаем только цифры, Backspace, Delete, Enter
        if key_code == wx.WXK_RETURN:
            # Нажатие Enter в поле ввода
            if self.select_btn.IsEnabled():
                self._on_select(None)
        elif key_code in (wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_LEFT, wx.WXK_RIGHT):
            event.Skip()
        elif key_code in (wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, wx.WXK_NUMPAD3,
                        wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, wx.WXK_NUMPAD6, wx.WXK_NUMPAD7,
                        wx.WXK_NUMPAD8, wx.WXK_NUMPAD9):
            event.Skip()
        elif 48 <= key_code <= 57:  # Цифры на основной клавиатуре
            event.Skip()
        else:
            # Игнорируем все остальные символы
            wx.Bell()
    
    def _on_text_change(self, event):
        """ Обработка изменения текста в поле ввода. """        
        value = self.user_input.GetValue()
        if value and self.current_command:
            try:
                num = int(value)
                if self.current_command.min_value <= num <= self.current_command.max_value:
                    self.user_input.SetBackgroundColour(wx.Colour(200, 255, 200))  # зеленый
                    self.select_btn.Enable(True)
                else:
                    self.user_input.SetBackgroundColour(wx.Colour(255, 200, 200))  # красный
                    self.select_btn.Enable(False)
            except ValueError:
                self.user_input.SetBackgroundColour(wx.Colour(255, 200, 200))
                self.select_btn.Enable(False)
        else:
            self.user_input.SetBackgroundColour(wx.Colour(255, 255, 255))  # белый
            self.select_btn.Enable(False)
        self.user_input.Refresh()
        event.Skip()
    
    def _on_select(self, event):
        """ Обработка нажатия кнопки 'Подтвердить'. """
        if not self.current_command:
            wx.MessageBox(
                "Команда не найдена",
                "Ошибка ввода",
                wx.OK | wx.ICON_ERROR
            )
            return
        self.current_command.confirm(int(self.user_input.GetValue()))
    
    def _back_to_environs(self, event):
        """ Возвращает консоль к списку окружений. """
        self.run_cmd_console(ListEnvirons)
    
    def _on_close(self, event):
        """ Обработчик закрытия окна. """
        self.service.close_all_services()
        event.Skip()
    
    def show_evolution(self):
        if self.current_agent:
            wx.CallAfter(self.current_agent.show_evolution)
    
    def show_toast(self, text: str):
        notification = wx.adv.NotificationMessage(
                title='Уведомление',
                message=text,
                parent=self,
                flags=wx.ICON_INFORMATION
            )
        notification.Show(timeout=5)
    
    def run_cmd_console(self, cmd: Type[BaseCommandConsole]):
        """Выводит команду в консоли.

        Args:
            cmd (BaseCommandConsole): Команда.
        """
        self.user_input.Clear()
        self.current_command = cmd(self)
        if self.current_command.text:
            self.console.AppendText(self.current_command.text)
        if self.current_command.goto:
            self.run_cmd_console(self.current_command.goto)
    
    def start(self):
        """ Запуск главного окна. """
        self.Show()
        self.app.MainLoop()