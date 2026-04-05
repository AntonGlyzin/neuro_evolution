from neuro_gym import RouterTasks
from neuro_gym.commands import RunTrainAgent
from services.tasks.cpu_tasks import run_train


RouterTasks.add(RunTrainAgent, run_train)