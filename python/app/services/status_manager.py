import threading
import asyncio
import random
import hashlib
import json
from app.utils.logger import logger

class StatusManager:
    def __init__(self):
       self.last_sent = {}
       self.statuses = {}
       self.statuses_lock = threading.Lock()

    async def fill_statuses_with_random(self,count: int = 10, delay: float = 3.0):
        await asyncio.sleep(10) 
        for i in range(count):
            task_id = f"task_{i}"
            status_value = f"status_{random.randint(1, 100)}"
            person = f"Тестов Тест Тестович {i}"

            self.update_status(task_id, status_value, person)
            logger.info(f"[+] Добавлен статус: {task_id} → {status_value} ({person})")
            await asyncio.sleep(delay)

    def url_to_id(self,url: str) -> str:
        combined = url.strip().lower()
        return hashlib.sha256(combined.encode()).hexdigest()[:12]

    def update_status(self,task_id: str, status: str, person: str):
        with self.statuses_lock:
            self.statuses[task_id] = {
                "status": status,
                "person": person 
            }

    def clear_statuses(self):
        with self.statuses_lock:
            self.statuses.clear()

    async def send_status_stream(self):
        while True:
            with self.statuses_lock:
                for task_id, entry in self.statuses.items():
                    current_status = entry.get("status")
                    if self.last_sent.get(task_id) != current_status:
                        self.last_sent[task_id] = current_status
                        yield {
                            "event": "status",
                            "data": json.dumps({
                                "task_id": task_id,
                                "person": entry.get("person"),
                                "status": current_status
                            }, ensure_ascii=False)
                        }
            await asyncio.sleep(0.5)
