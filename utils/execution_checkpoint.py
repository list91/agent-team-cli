from pathlib import Path
from typing import Dict, Any, List
import json
import hashlib

class ExecutionCheckpoint:
    """
    Система контрольных точек выполнения для обязательного подтверждения выполнения задач
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.workspace_path = Path(f"./workspace/{session_id}")
        self.checkpoint_file = self.workspace_path / "execution_checkpoints.json"
        
        # Создаем директорию если не существует
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Загружаем существующие чекпоинты или создаем новый
        self.checkpoints = self._load_checkpoints()
    
    def _load_checkpoints(self) -> Dict[str, Any]:
        """Загрузить чекпоинты из файла"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        else:
            return {}
    
    def _save_checkpoints(self):
        """Сохранить чекпоинты в файл"""
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoints, f, indent=2, ensure_ascii=False)
    
    def create_checkpoint(self, agent_name: str, task_description: str) -> str:
        """
        Создать контрольную точку выполнения задачи
        Возвращает ID контрольной точки
        """
        # Генерируем ID чекпоинта на основе содержимого задачи
        checkpoint_id = hashlib.md5(f"{agent_name}_{task_description}_{len(self.checkpoints)}".encode()).hexdigest()[:8]
        
        checkpoint_data = {
            "agent": agent_name,
            "task": task_description,
            "status": "created",
            "timestamp": self._get_timestamp()
        }
        
        if 'checkpoints' not in self.checkpoints:
            self.checkpoints['checkpoints'] = {}
        
        self.checkpoints['checkpoints'][checkpoint_id] = checkpoint_data
        self._save_checkpoints()
        
        return checkpoint_id
    
    def confirm_execution(self, checkpoint_id: str, result: str) -> bool:
        """
        Подтвердить выполнение задачи через контрольную точку
        """
        if 'checkpoints' not in self.checkpoints or checkpoint_id not in self.checkpoints['checkpoints']:
            return False
            
        self.checkpoints['checkpoints'][checkpoint_id].update({
            "status": "completed",
            "result_preview": result[:200] if result else "",  # Сохраняем превью результата
            "completed_at": self._get_timestamp()
        })
        
        self._save_checkpoints()
        return True
    
    def get_checkpoint_status(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Получить статус контрольной точки
        """
        if 'checkpoints' not in self.checkpoints:
            return {"status": "unknown", "error": "No checkpoints registered"}
            
        return self.checkpoints['checkpoints'].get(checkpoint_id, {"status": "not_found"})
    
    def _get_timestamp(self) -> str:
        """Получить текущую метку времени"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_all_checkpoints(self) -> List[Dict[str, Any]]:
        """Получить все контрольные точки"""
        if 'checkpoints' not in self.checkpoints:
            return []
        
        result = []
        for checkpoint_id, data in self.checkpoints['checkpoints'].items():
            result.append({
                "id": checkpoint_id,
                **data
            })
        return result

# Global registry to track checkpoints
checkpoint_registry = {}

def get_or_create_checkpoint(session_id: str) -> ExecutionCheckpoint:
    """
    Получить существующую или создать новую контрольную точку для сессии
    """
    if session_id not in checkpoint_registry:
        checkpoint_registry[session_id] = ExecutionCheckpoint(session_id)
    return checkpoint_registry[session_id]