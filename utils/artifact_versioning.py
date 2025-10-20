from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import hashlib
import os
from pathlib import Path

class ArtifactVersionControl:
    """
    Система управления версиями артефактов для избежания конфликтов и обеспечения отслеживаемости
    """
    
    def __init__(self, workspace_root: str = "./workspace"):
        self.workspace_root = workspace_root
        self.version_history = {}
        self.artifact_metadata = {}
        
        # Инициализируем систему
        self._initialize_version_control()
    
    def _initialize_version_control(self):
        """
        Инициализировать систему управления версиями
        """
        # Создаем директорию для хранения метаданных версий
        metadata_dir = Path(f"{self.workspace_root}/.artifact_versions")
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем существующую историю версий
        self._load_version_history()
    
    def _load_version_history(self):
        """
        Загрузить историю версий из файлов
        """
        metadata_file = Path(f"{self.workspace_root}/.artifact_versions/history.json")
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.version_history = json.load(f)
            except Exception as e:
                print(f"Error loading version history: {e}")
                self.version_history = {}
        else:
            self.version_history = {}
    
    def _save_version_history(self):
        """
        Сохранить историю версий в файл
        """
        metadata_file = Path(f"{self.workspace_root}/.artifact_versions/history.json")
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving version history: {e}")
    
    def create_artifact_version(self, session_id: str, agent_type: str, 
                              artifact_name: str, artifact_content: str,
                              parent_version: Optional[str] = None) -> str:
        """
        Создать новую версию артефакта
        """
        # Генерируем уникальный ID версии
        version_id = self._generate_version_id(session_id, agent_type, artifact_name, artifact_content)
        
        # Создаем запись о версии
        version_record = {
            'version_id': version_id,
            'session_id': session_id,
            'agent_type': agent_type,
            'artifact_name': artifact_name,
            'parent_version': parent_version,
            'content_hash': self._calculate_content_hash(artifact_content),
            'created_at': datetime.now().isoformat(),
            'content_preview': artifact_content[:200] + '...' if len(artifact_content) > 200 else artifact_content
        }
        
        # Сохраняем запись о версии
        if session_id not in self.version_history:
            self.version_history[session_id] = {}
        
        if agent_type not in self.version_history[session_id]:
            self.version_history[session_id][agent_type] = {}
        
        if artifact_name not in self.version_history[session_id][agent_type]:
            self.version_history[session_id][agent_type][artifact_name] = []
        
        self.version_history[session_id][agent_type][artifact_name].append(version_record)
        
        # Сохраняем историю версий
        self._save_version_history()
        
        # Сохраняем метаданные артефакта
        self._save_artifact_metadata(session_id, agent_type, artifact_name, version_record)
        
        return version_id
    
    def _generate_version_id(self, session_id: str, agent_type: str, 
                           artifact_name: str, artifact_content: str) -> str:
        """
        Сгенерировать уникальный ID версии артефакта
        """
        # Создаем хэш из комбинации параметров
        hash_input = f"{session_id}_{agent_type}_{artifact_name}_{artifact_content}_{datetime.now().timestamp()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _calculate_content_hash(self, content: str) -> str:
        """
        Рассчитать хэш содержимого артефакта
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _save_artifact_metadata(self, session_id: str, agent_type: str, 
                              artifact_name: str, version_record: Dict[str, Any]):
        """
        Сохранить метаданные артефакта
        """
        if session_id not in self.artifact_metadata:
            self.artifact_metadata[session_id] = {}
        
        if agent_type not in self.artifact_metadata[session_id]:
            self.artifact_metadata[session_id][agent_type] = {}
        
        self.artifact_metadata[session_id][agent_type][artifact_name] = {
            'current_version': version_record['version_id'],
            'content_hash': version_record['content_hash'],
            'last_modified': version_record['created_at'],
            'versions_count': len(self.version_history[session_id][agent_type][artifact_name])
        }
    
    def get_artifact_versions(self, session_id: str, agent_type: str, 
                            artifact_name: str) -> List[Dict[str, Any]]:
        """
        Получить все версии артефакта
        """
        if session_id in self.version_history:
            if agent_type in self.version_history[session_id]:
                if artifact_name in self.version_history[session_id][agent_type]:
                    return self.version_history[session_id][agent_type][artifact_name]
        
        return []
    
    def get_latest_artifact_version(self, session_id: str, agent_type: str, 
                                  artifact_name: str) -> Optional[Dict[str, Any]]:
        """
        Получить последнюю версию артефакта
        """
        versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        if versions:
            return versions[-1]  # Последняя версия в списке
        
        return None
    
    def compare_artifact_versions(self, session_id: str, agent_type: str, 
                               artifact_name: str, version_ids: List[str]) -> Dict[str, Any]:
        """
        Сравнить две или более версий артефакта
        """
        versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        # Фильтруем версии по заданным ID
        selected_versions = [
            version for version in versions 
            if version['version_id'] in version_ids
        ]
        
        if len(selected_versions) < 2:
            return {
                'comparison_possible': False,
                'message': 'At least two versions are required for comparison',
                'versions_compared': len(selected_versions)
            }
        
        # Сравниваем версии
        comparison_result = {
            'comparison_possible': True,
            'versions_compared': len(selected_versions),
            'artifacts_compared': artifact_name,
            'session_id': session_id,
            'agent_type': agent_type,
            'differences_found': [],
            'common_elements': []
        }
        
        # Простое сравнение по хэшам содержимого
        content_hashes = [version['content_hash'] for version in selected_versions]
        
        if len(set(content_hashes)) > 1:
            comparison_result['differences_found'].append('Content differs between versions')
        else:
            comparison_result['common_elements'].append('Content is identical between versions')
        
        # Сравниваем даты создания
        creation_times = [version['created_at'] for version in selected_versions]
        comparison_result['creation_times'] = creation_times
        
        return comparison_result
    
    def rollback_artifact_version(self, session_id: str, agent_type: str, 
                               artifact_name: str, target_version_id: str) -> Dict[str, Any]:
        """
        Откатить артефакт к определенной версии
        """
        versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        # Находим целевую версию
        target_version = None
        for version in versions:
            if version['version_id'] == target_version_id:
                target_version = version
                break
        
        if not target_version:
            return {
                'rollback_successful': False,
                'message': f'Target version {target_version_id} not found',
                'session_id': session_id,
                'artifact_name': artifact_name
            }
        
        # Выполняем откат (в реальной системе здесь будет восстановление содержимого файла)
        rollback_result = {
            'rollback_successful': True,
            'target_version': target_version_id,
            'rolled_back_to': target_version['created_at'],
            'session_id': session_id,
            'agent_type': agent_type,
            'artifact_name': artifact_name,
            'rollback_timestamp': datetime.now().isoformat()
        }
        
        # Обновляем метаданные артефакта
        self._save_artifact_metadata(session_id, agent_type, artifact_name, target_version)
        
        return rollback_result
    
    def get_version_control_report(self, session_id: str = None) -> Dict[str, Any]:
        """
        Получить отчет о состоянии управления версиями
        """
        if session_id:
            # Получаем отчет для конкретной сессии
            session_history = self.version_history.get(session_id, {})
            
            report = {
                'session_id': session_id,
                'total_artifacts': 0,
                'total_versions': 0,
                'agents_involved': set(),
                'artifacts_by_agent': {},
                'report_timestamp': datetime.now().isoformat()
            }
            
            for agent_type, artifacts in session_history.items():
                report['agents_involved'].add(agent_type)
                
                if agent_type not in report['artifacts_by_agent']:
                    report['artifacts_by_agent'][agent_type] = {
                        'artifact_count': 0,
                        'version_count': 0,
                        'artifacts_list': []
                    }
                
                for artifact_name, versions in artifacts.items():
                    report['artifacts_by_agent'][agent_type]['artifact_count'] += 1
                    report['artifacts_by_agent'][agent_type]['version_count'] += len(versions)
                    report['artifacts_by_agent'][agent_type]['artifacts_list'].append(artifact_name)
                    
                    report['total_artifacts'] += 1
                    report['total_versions'] += len(versions)
            
            report['agents_involved'] = list(report['agents_involved'])
            
            return report
        else:
            # Получаем общий отчет по всем сессиям
            total_sessions = len(self.version_history)
            total_artifacts = 0
            total_versions = 0
            session_reports = []
            
            for sid in self.version_history:
                session_report = self.get_version_control_report(sid)
                session_reports.append(session_report)
                total_artifacts += session_report['total_artifacts']
                total_versions += session_report['total_versions']
            
            return {
                'total_sessions': total_sessions,
                'total_artifacts': total_artifacts,
                'total_versions': total_versions,
                'session_reports': session_reports,
                'report_timestamp': datetime.now().isoformat()
            }
    
    def resolve_version_conflicts(self, session_id: str, agent_type: str, 
                                artifact_name: str) -> Dict[str, Any]:
        """
        Разрешить конфликты версий артефактов
        """
        versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        if len(versions) < 2:
            return {
                'conflict_resolved': False,
                'message': 'No version conflicts to resolve',
                'session_id': session_id,
                'artifact_name': artifact_name
            }
        
        # Простое разрешение конфликтов: выбираем последнюю версию
        latest_version = versions[-1]
        
        conflict_resolution = {
            'conflict_resolved': True,
            'resolution_method': 'latest_version_selected',
            'resolved_to_version': latest_version['version_id'],
            'resolved_at': datetime.now().isoformat(),
            'session_id': session_id,
            'agent_type': agent_type,
            'artifact_name': artifact_name,
            'conflicting_versions_count': len(versions)
        }
        
        # Обновляем метаданные артефакта
        self._save_artifact_metadata(session_id, agent_type, artifact_name, latest_version)
        
        return conflict_resolution
    
    def enforce_version_control_policies(self, session_id: str, agent_type: str, 
                                      artifact_name: str, new_content: str) -> Dict[str, Any]:
        """
        Принудительно применить политики управления версиями
        """
        # Проверяем, существует ли уже такой артефакт
        existing_versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        if existing_versions:
            # Проверяем, отличается ли новое содержимое от существующего
            latest_version = existing_versions[-1]
            new_content_hash = self._calculate_content_hash(new_content)
            
            if latest_version['content_hash'] == new_content_hash:
                # Содержимое не изменилось, не создаем новую версию
                return {
                    'policy_enforced': True,
                    'action_taken': 'no_new_version_created',
                    'reason': 'Content unchanged from latest version',
                    'session_id': session_id,
                    'agent_type': agent_type,
                    'artifact_name': artifact_name,
                    'latest_version': latest_version['version_id']
                }
        
        # Создаем новую версию
        parent_version = existing_versions[-1]['version_id'] if existing_versions else None
        new_version_id = self.create_artifact_version(
            session_id, 
            agent_type, 
            artifact_name, 
            new_content,
            parent_version
        )
        
        return {
            'policy_enforced': True,
            'action_taken': 'new_version_created',
            'new_version_id': new_version_id,
            'session_id': session_id,
            'agent_type': agent_type,
            'artifact_name': artifact_name,
            'parent_version': parent_version
        }
    
    def get_artifact_lineage(self, session_id: str, agent_type: str, 
                           artifact_name: str) -> List[Dict[str, Any]]:
        """
        Получить родословную артефакта (все его версии в хронологическом порядке)
        """
        versions = self.get_artifact_versions(session_id, agent_type, artifact_name)
        
        # Сортируем версии по дате создания
        sorted_versions = sorted(versions, key=lambda x: x['created_at'])
        
        lineage = []
        for i, version in enumerate(sorted_versions):
            lineage_entry = {
                'version_number': i + 1,
                'version_id': version['version_id'],
                'created_at': version['created_at'],
                'parent_version': version['parent_version'],
                'content_preview': version['content_preview']
            }
            
            # Добавляем информацию о изменениях
            if i > 0:
                prev_version = sorted_versions[i-1]
                if version['content_hash'] != prev_version['content_hash']:
                    lineage_entry['changes_made'] = True
                    lineage_entry['change_type'] = 'content_modified'
                else:
                    lineage_entry['changes_made'] = False
                    lineage_entry['change_type'] = 'metadata_only'
            else:
                lineage_entry['changes_made'] = True
                lineage_entry['change_type'] = 'initial_creation'
            
            lineage.append(lineage_entry)
        
        return lineage

# Глобальная система управления версиями артефактов
artifact_version_control = ArtifactVersionControl()