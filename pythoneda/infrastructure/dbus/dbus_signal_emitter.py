"""
pythoneda/infrastructure/dbus/dbus_signal_emitter.py

This file defines the DbusSignalEmitter class.

Copyright (C) 2023-today rydnr's pythoneda-shared-pythoneda/infrastructure

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import abc
import asyncio
from dbus_next.aio import MessageBus
from dbus_next import BusType, Message, MessageType
import logging
from pythoneda import Event, EventEmitter
from typing import Dict

class DbusSignalEmitter(EventEmitter, abc.ABC):

    """
    A Port that emits events as d-bus signals.

    Class name: DbusSignalEmitter

    Responsibilities:
        - Connect to d-bus.
        - Translate domain events to d-bus signals.

    Collaborators:
        - PythonEDAApplication: Requests emitting events.
    """
    def __init__(self):
        """
        Creates a new DbusSignalEmitter instance.
        """
        super().__init__()

    def signal_emitters(self) -> Dict:
        """
        Retrieves the configured event emitters.
        :return: For each event, a list with the event interface and the bus type.
        :rtype: Dict
        """
        return {}

    def fqdn_key(self, cls: type) -> str:
        """
        Retrieves the key used for given class.
        :param cls: The class.
        :type cls: Class
        :return: The key.
        :rtype: str
        """
        return f'{cls.__module__}.{cls.__name__}'

    async def emit(self, event: Event):
        """
        Emits given event as d-bus signal.
        :param event: The domain event to emit.
        :type event: pythoneda.event.Event
        """
        logging.getLogger(self.__class__.__name__).info(f'In dbus_signal_emitter')
        await super().emit(event)
        collaborators = self.signal_emitters()

        if collaborators:
            if self.fqdn_key(event.__class__) in collaborators:
                interface_class, bus_type = collaborators[self.fqdn_key(event.__class__)]
                instance = interface_class()
                bus = await MessageBus(bus_type=bus_type).connect()
                bus.export(interface_class.path(), instance)
                logging.getLogger(self.__class__.__name__).info(f'Sending signal {interface_class.__module__}.{interface_class.__name__} on path {interface_class.path()} to d-bus {bus_type}')
                await bus.send(
                    Message.new_signal(
                        interface_class.path(),
                        self.fqdn_key(interface_class),
                        instance.name,
                        instance.sign(event),
                        instance.transform(event)))
                logging.getLogger(self.__class__.__name__).info(f'Sent signal {interface_class.__module__}.{interface_class.__name__} on path {interface_class.path()} to d-bus {bus_type}')
            else:
                logging.getLogger(self.__class__.__name__).warn(f'No d-bus emitter registered for event {event.__class__}')
        else:
            logging.getLogger(self.__class__.__name__).warn(f'No d-bus emitters found')
