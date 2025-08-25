import queue

class TaskScheduler():
    def __init__(self,queue_size):
        self.queue_size = queue_size
        task_queue = queue.Queue(queue_size)