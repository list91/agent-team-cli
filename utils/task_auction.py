from typing import Dict, List, Tuple, Any
from utils.competency_matrix import competency_matrix
import uuid
from datetime import datetime

class TaskAuction:
    """
    Система аукциона задач, где агенты "делают ставки" на задачи
    """
    
    def __init__(self):
        self.auctions = {}  # Активные аукционы
        self.completed_auctions = {}  # Завершенные аукционы
    
    def create_auction(self, task_description: str, available_agents: List[str], 
                      session_id: str) -> str:
        """
        Создать аукцион для задачи
        """
        auction_id = str(uuid.uuid4())[:8]
        
        # Получаем оценки компетентности от матрицы компетенций
        competency_scores = competency_matrix.get_task_similarity_scores(
            task_description, available_agents
        )
        
        # Создаем аукцион
        self.auctions[auction_id] = {
            'task_description': task_description,
            'available_agents': available_agents,
            'competency_scores': competency_scores,
            'bids': {},  # Ставки агентов
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        return auction_id
    
    def place_bid(self, auction_id: str, agent_type: str, confidence: float, 
                  estimated_time: int) -> bool:
        """
        Агент делает ставку на задачу
        """
        if auction_id not in self.auctions:
            return False
            
        auction = self.auctions[auction_id]
        
        # Проверяем, что агент может участвовать
        if agent_type not in auction['available_agents']:
            return False
            
        # Агент делает ставку (уверенность и оценка времени)
        self.auctions[auction_id]['bids'][agent_type] = {
            'confidence': confidence,
            'estimated_time': estimated_time,
            'timestamp': datetime.now().isoformat()
        }
        
        return True
    
    def evaluate_bids(self, auction_id: str) -> Tuple[str, float]:
        """
        Оценить ставки и выбрать победителя
        """
        if auction_id not in self.auctions:
            return 'backend_dev', 0.0  # По умолчанию
            
        auction = self.auctions[auction_id]
        
        if not auction['bids']:
            # Если нет ставок, используем оценки компетентности
            best_agent = max(auction['competency_scores'], 
                           key=auction['competency_scores'].get)
            best_score = auction['competency_scores'][best_agent]
            return best_agent, best_score
        
        # Оцениваем ставки по нескольким критериям
        best_agent = None
        best_overall_score = -1
        
        for agent_type, bid in auction['bids'].items():
            # Комбинируем оценку компетентности и уверенность агента
            competency_score = auction['competency_scores'].get(agent_type, 0.0)
            confidence = bid['confidence']
            
            # Взвешиваем оценки (можно настраивать веса)
            overall_score = 0.7 * competency_score + 0.3 * confidence
            
            if overall_score > best_overall_score:
                best_overall_score = overall_score
                best_agent = agent_type
        
        # Переносим аукцион в завершенные
        self.completed_auctions[auction_id] = self.auctions.pop(auction_id)
        self.completed_auctions[auction_id]['status'] = 'completed'
        self.completed_auctions[auction_id]['winner'] = best_agent
        self.completed_auctions[auction_id]['winning_score'] = best_overall_score
        
        return best_agent, best_overall_score
    
    def get_auction_status(self, auction_id: str) -> Dict[str, Any]:
        """
        Получить статус аукциона
        """
        if auction_id in self.auctions:
            return self.auctions[auction_id]
        elif auction_id in self.completed_auctions:
            return self.completed_auctions[auction_id]
        else:
            return {'status': 'not_found'}
    
    def auto_assign_task(self, task_description: str, available_agents: List[str], 
                        session_id: str) -> Tuple[str, float]:
        """
        Автоматически назначить задачу через аукцион
        """
        # Создаем аукцион
        auction_id = self.create_auction(task_description, available_agents, session_id)
        
        # Симулируем "ставки" агентов (в реальной системе агенты бы делали это сами)
        for agent_type in available_agents:
            # Получаем оценку компетентности
            competency_score = competency_matrix.get_task_similarity_scores(
                task_description, [agent_type]
            ).get(agent_type, 0.0)
            
            # Делаем ставку (симуляция)
            self.place_bid(auction_id, agent_type, competency_score, 60)  # 60 минут оценка
        
        # Оцениваем ставки и выбираем победителя
        return self.evaluate_bids(auction_id)

# Глобальный экземпляр аукционной системы
task_auction = TaskAuction()