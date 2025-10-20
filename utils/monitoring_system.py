from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class MonitoringAndAlertingSystem:
    """
    Система мониторинга и оповещений для агентной архитектуры
    """
    
    def __init__(self):
        self.alert_rules = {}
        self.monitoring_metrics = {}
        self.notification_channels = {}
        self.alert_history = []
        
        # Инициализируем систему
        self._initialize_monitoring_system()
    
    def _initialize_monitoring_system(self):
        """
        Инициализировать систему мониторинга
        """
        # Определяем базовые правила оповещений
        self.alert_rules = {
            'performance_degradation': {
                'metric': 'response_time',
                'condition': 'greater_than',
                'threshold': 5.0,  # секунды
                'severity': 'high',
                'notification_channel': 'email',
                'enabled': True
            },
            'error_rate_spike': {
                'metric': 'error_rate',
                'condition': 'greater_than',
                'threshold': 0.1,  # 10%
                'severity': 'critical',
                'notification_channel': 'email',
                'enabled': True
            },
            'resource_exhaustion': {
                'metric': 'memory_usage',
                'condition': 'greater_than',
                'threshold': 0.9,  # 90%
                'severity': 'high',
                'notification_channel': 'email',
                'enabled': True
            },
            'task_queue_overflow': {
                'metric': 'queued_tasks',
                'condition': 'greater_than',
                'threshold': 100,  # задач
                'severity': 'medium',
                'notification_channel': 'email',
                'enabled': True
            },
            'agent_unavailability': {
                'metric': 'agent_availability',
                'condition': 'less_than',
                'threshold': 0.95,  # 95%
                'severity': 'medium',
                'notification_channel': 'email',
                'enabled': True
            }
        }
        
        # Инициализируем каналы оповещений
        self.notification_channels = {
            'email': EmailNotificationChannel(),
            'slack': SlackNotificationChannel(),
            'sms': SMSNotificationChannel()
        }
        
        # Инициализируем метрики мониторинга
        self.monitoring_metrics = {
            'response_time': 0.0,
            'error_rate': 0.0,
            'memory_usage': 0.0,
            'queued_tasks': 0,
            'agent_availability': 1.0,
            'task_completion_rate': 0.0,
            'system_uptime': 0.0
        }
    
    def update_metric(self, metric_name: str, value: Any):
        """
        Обновить значение метрики мониторинга
        """
        if metric_name in self.monitoring_metrics:
            self.monitoring_metrics[metric_name] = value
            
            # Проверяем правила оповещений для этой метрики
            self._check_alert_rules(metric_name, value)
        else:
            print(f"Warning: Unknown metric {metric_name}")
    
    def _check_alert_rules(self, metric_name: str, value: Any):
        """
        Проверить правила оповещений для метрики
        """
        for rule_name, rule in self.alert_rules.items():
            if rule['metric'] == metric_name and rule['enabled']:
                # Проверяем условие
                alert_triggered = self._evaluate_condition(
                    rule['condition'], 
                    value, 
                    rule['threshold']
                )
                
                if alert_triggered:
                    # Генерируем оповещение
                    alert = self._generate_alert(rule_name, rule, metric_name, value)
                    self.alert_history.append(alert)
                    
                    # Отправляем оповещение
                    self._send_alert(alert)
    
    def _evaluate_condition(self, condition: str, value: Any, threshold: Any) -> bool:
        """
        Оценить условие оповещения
        """
        try:
            if condition == 'greater_than':
                return float(value) > float(threshold)
            elif condition == 'less_than':
                return float(value) < float(threshold)
            elif condition == 'equal_to':
                return float(value) == float(threshold)
            elif condition == 'not_equal_to':
                return float(value) != float(threshold)
            elif condition == 'contains':
                return str(threshold) in str(value)
            elif condition == 'does_not_contain':
                return str(threshold) not in str(value)
            else:
                return False
        except (ValueError, TypeError):
            # Если не можем преобразовать в число, возвращаем False
            return False
    
    def _generate_alert(self, rule_name: str, rule: Dict[str, Any], 
                       metric_name: str, value: Any) -> Dict[str, Any]:
        """
        Сгенерировать оповещение на основе правила
        """
        alert = {
            'alert_id': f"{rule_name}_{datetime.now().timestamp()}",
            'rule_name': rule_name,
            'metric_name': metric_name,
            'current_value': value,
            'threshold': rule['threshold'],
            'condition': rule['condition'],
            'severity': rule['severity'],
            'notification_channel': rule['notification_channel'],
            'triggered_at': datetime.now().isoformat(),
            'status': 'triggered'
        }
        
        return alert
    
    def _send_alert(self, alert: Dict[str, Any]):
        """
        Отправить оповещение через соответствующий канал
        """
        channel_name = alert['notification_channel']
        if channel_name in self.notification_channels:
            channel = self.notification_channels[channel_name]
            try:
                channel.send_notification(alert)
                alert['status'] = 'sent'
                alert['sent_at'] = datetime.now().isoformat()
            except Exception as e:
                print(f"Error sending alert via {channel_name}: {str(e)}")
                alert['status'] = 'failed'
                alert['error'] = str(e)
        else:
            print(f"Warning: Unknown notification channel {channel_name}")
            alert['status'] = 'failed'
            alert['error'] = f'Unknown notification channel: {channel_name}'
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """
        Получить отчет о состоянии системы
        """
        # Проверяем текущие метрики
        health_status = self._assess_system_health()
        
        # Получаем последние оповещения
        recent_alerts = self._get_recent_alerts(hours=24)
        
        # Получаем статистику по каналам оповещений
        channel_stats = self._get_notification_channel_statistics()
        
        return {
            'health_status': health_status,
            'current_metrics': self.monitoring_metrics,
            'recent_alerts': recent_alerts,
            'notification_channel_stats': channel_stats,
            'report_timestamp': datetime.now().isoformat()
        }
    
    def _assess_system_health(self) -> str:
        """
        Оценить общее состояние системы
        """
        # Проверяем критические метрики
        critical_metrics = [
            ('error_rate', 0.05, 'less_than'),  # Менее 5% ошибок
            ('agent_availability', 0.95, 'greater_than'),  # Более 95% доступности
            ('response_time', 5.0, 'less_than')  # Менее 5 секунд
        ]
        
        health_score = 0
        total_metrics = len(critical_metrics)
        
        for metric_name, threshold, condition in critical_metrics:
            if metric_name in self.monitoring_metrics:
                value = self.monitoring_metrics[metric_name]
                if self._evaluate_condition(condition, value, threshold):
                    health_score += 1
        
        # Определяем общее состояние
        health_percentage = health_score / total_metrics if total_metrics > 0 else 1.0
        
        if health_percentage >= 0.9:
            return 'healthy'
        elif health_percentage >= 0.7:
            return 'degraded'
        elif health_percentage >= 0.5:
            return 'warning'
        else:
            return 'critical'
    
    def _get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Получить недавние оповещения
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = []
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['triggered_at'])
            if alert_time > cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts
    
    def _get_notification_channel_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по каналам оповещений
        """
        stats = {}
        
        for channel_name, channel in self.notification_channels.items():
            stats[channel_name] = {
                'alerts_sent': channel.get_sent_count(),
                'alerts_failed': channel.get_failed_count(),
                'success_rate': channel.get_success_rate()
            }
        
        return stats
    
    def add_custom_alert_rule(self, rule_name: str, rule_definition: Dict[str, Any]):
        """
        Добавить пользовательское правило оповещений
        """
        self.alert_rules[rule_name] = rule_definition
    
    def remove_alert_rule(self, rule_name: str):
        """
        Удалить правило оповещений
        """
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
    
    def enable_alert_rule(self, rule_name: str):
        """
        Включить правило оповещений
        """
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name]['enabled'] = True
    
    def disable_alert_rule(self, rule_name: str):
        """
        Отключить правило оповещений
        """
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name]['enabled'] = False
    
    def get_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получить историю оповещений за последние N дней
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered_history = []
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['triggered_at'])
            if alert_time > cutoff_time:
                filtered_history.append(alert)
        
        return filtered_history
    
    def configure_notification_channel(self, channel_name: str, 
                                    channel_config: Dict[str, Any]):
        """
        Настроить канал оповещений
        """
        if channel_name in self.notification_channels:
            channel = self.notification_channels[channel_name]
            channel.configure(channel_config)
        else:
            print(f"Warning: Unknown notification channel {channel_name}")
    
    def test_notification_channel(self, channel_name: str) -> Dict[str, Any]:
        """
        Протестировать канал оповещений
        """
        if channel_name in self.notification_channels:
            channel = self.notification_channels[channel_name]
            test_result = channel.test_connection()
            return {
                'channel_name': channel_name,
                'test_result': test_result,
                'tested_at': datetime.now().isoformat()
            }
        else:
            return {
                'channel_name': channel_name,
                'test_result': False,
                'error': f'Unknown notification channel: {channel_name}',
                'tested_at': datetime.now().isoformat()
            }
    
    def generate_performance_trends(self, metric_name: str, 
                                  days: int = 30) -> Dict[str, Any]:
        """
        Сгенерировать тенденции производительности для метрики
        """
        # Получаем исторические данные (в реальной системе они бы хранились в БД)
        # Здесь используем упрощенную реализацию
        historical_data = []
        
        # В реальной системе это будет запрос к базе данных исторических метрик
        # Пока используем текущие данные с некоторыми вариациями для демонстрации
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            # Генерируем случайные данные для демонстрации
            import random
            value = self.monitoring_metrics.get(metric_name, 0.0) + random.uniform(-0.1, 0.1)
            historical_data.append({
                'date': date.isoformat(),
                'value': max(0.0, value)  # Не допускаем отрицательные значения
            })
        
        # Сортируем по дате
        historical_data.sort(key=lambda x: x['date'])
        
        # Рассчитываем тенденции
        if len(historical_data) >= 2:
            first_value = historical_data[0]['value']
            last_value = historical_data[-1]['value']
            trend = (last_value - first_value) / first_value if first_value != 0 else 0
            
            if trend > 0.1:
                trend_direction = 'increasing'
            elif trend < -0.1:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
            trend = 0.0
        
        return {
            'metric_name': metric_name,
            'trend_direction': trend_direction,
            'trend_value': trend,
            'historical_data': historical_data,
            'analysis_period_days': days,
            'generated_at': datetime.now().isoformat()
        }

# Классы каналов оповещений

class EmailNotificationChannel:
    """
    Канал оповещений по электронной почте
    """
    
    def __init__(self):
        self.sent_count = 0
        self.failed_count = 0
        self.config = {}
        
        # Инициализируем конфигурацию по умолчанию
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """
        Инициализировать конфигурацию по умолчанию
        """
        self.config = {
            'smtp_server': 'localhost',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'from_address': 'monitoring@agent-team.local',
            'to_addresses': ['admin@agent-team.local'],
            'use_tls': True
        }
    
    def configure(self, config: Dict[str, Any]):
        """
        Настроить канал оповещений
        """
        self.config.update(config)
    
    def send_notification(self, alert: Dict[str, Any]):
        """
        Отправить оповещение по электронной почте
        """
        try:
            # Создаем сообщение
            msg = MimeMultipart()
            msg['From'] = self.config['from_address']
            msg['To'] = ', '.join(self.config['to_addresses'])
            msg['Subject'] = f"ALERT: {alert['rule_name']} - {alert['severity'].upper()}"
            
            # Создаем тело сообщения
            body = f"""
System Alert Notification

Rule: {alert['rule_name']}
Severity: {alert['severity']}
Metric: {alert['metric_name']}
Current Value: {alert['current_value']}
Threshold: {alert['threshold']}
Condition: {alert['condition']}
Triggered At: {alert['triggered_at']}

This is an automated system alert.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Отправляем сообщение (в реальной системе)
            # Здесь мы просто имитируем отправку
            print(f"Email notification sent: {msg['Subject']}")
            self.sent_count += 1
            
        except Exception as e:
            print(f"Error sending email notification: {str(e)}")
            self.failed_count += 1
            raise
    
    def test_connection(self) -> bool:
        """
        Протестировать соединение с SMTP сервером
        """
        # В реальной системе это будет попытка подключения к SMTP серверу
        # Здесь просто возвращаем True для демонстрации
        return True
    
    def get_sent_count(self) -> int:
        """
        Получить количество отправленных оповещений
        """
        return self.sent_count
    
    def get_failed_count(self) -> int:
        """
        Получить количество неудачных попыток отправки
        """
        return self.failed_count
    
    def get_success_rate(self) -> float:
        """
        Получить процент успешных отправок
        """
        total_attempts = self.sent_count + self.failed_count
        return self.sent_count / total_attempts if total_attempts > 0 else 1.0

class SlackNotificationChannel:
    """
    Канал оповещений через Slack
    """
    
    def __init__(self):
        self.sent_count = 0
        self.failed_count = 0
        self.config = {}
        
        # Инициализируем конфигурацию по умолчанию
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """
        Инициализировать конфигурацию по умолчанию
        """
        self.config = {
            'webhook_url': '',
            'channel': '#alerts',
            'username': 'AgentTeamBot',
            'icon_emoji': ':robot_face:'
        }
    
    def configure(self, config: Dict[str, Any]):
        """
        Настроить канал оповещений
        """
        self.config.update(config)
    
    def send_notification(self, alert: Dict[str, Any]):
        """
        Отправить оповещение через Slack webhook
        """
        try:
            # В реальной системе это будет HTTP POST запрос к webhook URL
            # Здесь мы просто имитируем отправку
            print(f"Slack notification sent to {self.config['channel']}: ALERT {alert['rule_name']}")
            self.sent_count += 1
            
        except Exception as e:
            print(f"Error sending Slack notification: {str(e)}")
            self.failed_count += 1
            raise
    
    def test_connection(self) -> bool:
        """
        Протестировать соединение с Slack webhook
        """
        # В реальной системе это будет попытка отправки тестового сообщения
        # Здесь просто возвращаем True для демонстрации
        return True
    
    def get_sent_count(self) -> int:
        """
        Получить количество отправленных оповещений
        """
        return self.sent_count
    
    def get_failed_count(self) -> int:
        """
        Получить количество неудачных попыток отправки
        """
        return self.failed_count
    
    def get_success_rate(self) -> float:
        """
        Получить процент успешных отправок
        """
        total_attempts = self.sent_count + self.failed_count
        return self.sent_count / total_attempts if total_attempts > 0 else 1.0

class SMSNotificationChannel:
    """
    Канал оповещений через SMS
    """
    
    def __init__(self):
        self.sent_count = 0
        self.failed_count = 0
        self.config = {}
        
        # Инициализируем конфигурацию по умолчанию
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """
        Инициализировать конфигурацию по умолчанию
        """
        self.config = {
            'api_key': '',
            'api_secret': '',
            'from_number': '+1234567890',
            'to_numbers': ['+1234567890']
        }
    
    def configure(self, config: Dict[str, Any]):
        """
        Настроить канал оповещений
        """
        self.config.update(config)
    
    def send_notification(self, alert: Dict[str, Any]):
        """
        Отправить оповещение через SMS API
        """
        try:
            # В реальной системе это будет вызов SMS API
            # Здесь мы просто имитируем отправку
            print(f"SMS notification sent to {self.config['to_numbers']}: ALERT {alert['rule_name']}")
            self.sent_count += 1
            
        except Exception as e:
            print(f"Error sending SMS notification: {str(e)}")
            self.failed_count += 1
            raise
    
    def test_connection(self) -> bool:
        """
        Протестировать соединение с SMS API
        """
        # В реальной системе это будет попытка подключения к SMS API
        # Здесь просто возвращаем True для демонстрации
        return True
    
    def get_sent_count(self) -> int:
        """
        Получить количество отправленных оповещений
        """
        return self.sent_count
    
    def get_failed_count(self) -> int:
        """
        Получить количество неудачных попыток отправки
        """
        return self.failed_count
    
    def get_success_rate(self) -> float:
        """
        Получить процент успешных отправок
        """
        total_attempts = self.sent_count + self.failed_count
        return self.sent_count / total_attempts if total_attempts > 0 else 1.0

# Глобальная система мониторинга и оповещений
monitoring_system = MonitoringAndAlertingSystem()