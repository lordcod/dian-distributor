from typing import Dict, List, Tuple
from dianpy import fromfile as dian_fromfile
from lenexpy import fromfile as lenex_fromfile
from lenexpy.models.event import Event
from lenexpy.models.athelete import Athlete
import logging

_log = logging.getLogger(__name__)


class DistributedDian:
    def __init__(self, lenex_path: str, dian_path: str):
        """
        Инициализация класса с путями к файлам LENEX и DIAN.
        """
        self.lenex = lenex_fromfile(lenex_path)
        self.dian = dian_fromfile(dian_path)

    def parse_events(self) -> Dict[Tuple, List[Event]]:
        """
        Разбирает события из LENEX файла и группирует их по ключу:
        (пол, дистанция, стиль).
        Возвращает словарь, где ключ - кортеж, а значение - список событий.
        """
        events = {}
        for session in self.lenex.meet.sessions:
            for event in session.events:
                key = (event.gender, event.swimstyle.distance,
                       event.swimstyle.stroke)
                events.setdefault(key, []).append(event)
        return events

    def parse_athletes(self, event: Event) -> Dict[Tuple, Tuple[int, int, bool]]:
        """
        Разбирает спортсменов для конкретного события.
        Возвращает словарь, где ключ - (имя, фамилия, дата рождения),
        а значение - кортеж с номером серии, номером дорожки и статусом участия.
        """
        # Составляем словарь с порядком серий для данного события
        heats = {heat.heatid: heat.order for heat in event.heats or []}

        athletes = {}
        for club in self.lenex.meet.clubs or []:
            for athl in club.athletes or []:
                key = (athl.firstname.lower(), athl.lastname.lower(),
                       athl.birthdate.strftime('%d.%m.%Y'))

                # Если у спортсмена нет записей о соревнованиях, то пропускаем его
                if not athl.entries:
                    athletes[key] = (None, None, False)
                    continue

                for entry in athl.entries:
                    # Если событие не совпадает с текущим, пропускаем
                    if entry.eventid != event.eventid:
                        continue

                    if entry.status in {"RJC", "WDR"}:
                        athletes[key] = (None, None, False)
                        continue

                    # Если серия не найдена, или спортсмен не участвует, пропускаем
                    if entry.heatid not in heats:
                        _log.debug('Not found heat %s', entry.heatid)
                        continue

                    # Сохраняем данные о серии, дорожке и статусе участия
                    athletes[key] = (heats[entry.heatid], entry.lane, True)

        return athletes

    def parse(self):
        """
        Основной метод для синхронизации данных из LENEX и DIAN.
        Для каждого события из DIAN находит соответствующее событие из LENEX и 
        для каждого спортсмена определяет серию и дорожку.
        """
        events = self.parse_events()

        for dian_event in self.dian.events:
            key = (dian_event.gender, dian_event.distance, dian_event.stroke)

            event = self._get_event_by_key(events, key)
            if not event:
                continue

            athletes = self.parse_athletes(event)
            maxheat = self._assign_athletes_to_event(dian_event, athletes)
            dian_event.heatcount = maxheat

    def _get_event_by_key(self, events: Dict[Tuple, List[Event]], key: Tuple) -> Event:
        """
        Пытается найти событие по ключу. Если событие не найдено, логирует предупреждение.
        Возвращает событие или None, если оно не найдено.
        """
        try:
            return events[key].pop(0)
        except (KeyError, IndexError):
            _log.warning('Event not found for key: %s', key)
            return None

    def _assign_athletes_to_event(self, dian_event, athletes: Dict[Tuple, Tuple[int, int, bool]]) -> int:
        """
        Присваивает спортсменам соответствующие данные (серия, дорожка) и 
        возвращает максимальное количество серий.
        """
        maxheat = 1

        for athl in dian_event.athletes or []:
            key = (athl.firstname.lower(),
                   athl.lastname.lower(), athl.birthdate)

            # Получаем данные для спортсмена
            heatnum, lanenum, status = athletes.get(key, (None, None, False))

            if not status:
                continue

            # Присваиваем данные спортсмену
            athl.heatnum = heatnum
            athl.lanenum = lanenum

            # Обновляем максимальную серию
            maxheat = max(maxheat, heatnum)

        return maxheat
