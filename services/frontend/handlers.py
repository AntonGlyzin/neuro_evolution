from neuro_gym.service import TypeCommand, handler, StatusCommand
from neuro_gym.commands import RunTrainAgent
from services.frontend.service import Frontend
from services.frontend.agent import Agent
from services.frontend.gui import SelectSaveModel


@handler(cls_service=Frontend, cls_command=RunTrainAgent, type_command=TypeCommand.REPLY)
def progress_train(service: Frontend, message: RunTrainAgent):
    """ Приходит прогресс тренировок для всех агентов. """
    if message.status == StatusCommand.ERROR:
        service.frame.print_console('\nОшибка при обучение\n')
        service.frame.print_console(message.response[0]['error'])
    if message.status == StatusCommand.SUCCESS:
        agent: Agent = service.frame.agents[message.params.env.id]
        agent.is_now_train = False
        agent.progress_train = service.frame.LENGTH_PROGRESS_BAR
        service.frame.show_toast('Завершено обучение для <{}>'.format(message.params.env.name))
        if service.frame.current_agent and service.frame.current_agent.env.id == message.params.env.id:
            service.frame.progress_bar.SetValue(0)
            service.frame.print_console('\nНейроэволюция завершена')
            service.frame.print_console('\nВыберите модель для сохранения')
            service.frame.progress_bar.SetValue(service.frame.LENGTH_PROGRESS_BAR)
            service.frame.run_cmd_console(SelectSaveModel)
            service.frame.current_agent.show_evolution()
    elif message.status == StatusCommand.PROCESSING:
        agent: Agent = service.frame.agents[message.params.env.id]
        agent.is_now_train = True
        agent.progress_train = message.response.progress_train
        agent.age_population += len(message.response.max_values)
        agent.max_values.extend(message.response.max_values)
        agent.mean_values.extend(message.response.mean_values)
        agent.min_values.extend(message.response.min_values)
        agent.std_values.extend(message.response.std_values)
        agent.best_values.extend([message.response.best_values])
        agent.best_individuals.append(message.response.best_individuals)
        if service.frame.current_agent and service.frame.current_agent.env.id == message.params.env.id:
            service.frame.progress_bar.SetValue(agent.progress_train)