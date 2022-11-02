from __future__ import annotations

import asyncio
from asyncio import Queue, Task, create_task

from textual._types import MessageTarget
from textual.events import Event, InputEvent


class EventQueue:
    def __init__(self, destination: MessageTarget):
        self.destination: MessageTarget = destination
        self._queue: Queue[Event | None] = Queue()
        self._task: Task | None = None
        self._running: asyncio.Event = asyncio.Event()

    def start(self):
        self.enable()
        self._task = create_task(self._process_events())

    def enable(self):
        self._running.set()

    def disable(self):
        self._running.clear()

    async def push(self, event: Event):
        await self._queue.put(event)

    async def _process_events(self) -> None:
        get_event = self._queue.get
        post_message = self.destination.post_message
        wait_until_handled = self._wait_until_handled
        disable = self.disable
        while True:
            print("getting next event")
            event = await get_event()
            print(f"got event {event}")
            if event is None:
                break

            requires_handling = isinstance(event, InputEvent)
            if requires_handling:
                print("disabling event queue")
                disable()

            print(f"posting event to destination {self.destination}")
            await post_message(event)

            if requires_handling:
                print(f"waiting for event to be handled...")
                await wait_until_handled()

    async def _wait_until_handled(self):
        await self._running.wait()

    async def shutdown(self):
        await self._queue.put(None)
        await self._task
