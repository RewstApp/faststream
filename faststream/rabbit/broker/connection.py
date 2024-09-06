from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, Optional, cast

from aio_pika import connect_robust
from aio_pika.pool import Pool

if TYPE_CHECKING:
    from ssl import SSLContext

    from aio_pika import (
        RobustChannel,
        RobustConnection,
    )
    from aio_pika.abc import TimeoutType


class ConnectionManager:
    def __init__(
        self,
        *,
        url: str,
        timeout: "TimeoutType",
        ssl_context: Optional["SSLContext"],
        connection_pool_size: Optional[int],
        channel_pool_size: Optional[int],
        channel_number: Optional[int],
        publisher_confirms: bool,
        on_return_raises: bool,
    ) -> None:
        self._connection_pool: "Pool[RobustConnection]" = Pool(
            lambda: connect_robust(
                url=url,
                timeout=timeout,
                ssl_context=ssl_context,
            ),
            max_size=connection_pool_size,
        )

        self._channel_pool: "Pool[RobustChannel]" = Pool(
            lambda: self._get_channel(
                channel_number=channel_number,
                publisher_confirms=publisher_confirms,
                on_return_raises=on_return_raises,
            ),
            max_size=channel_pool_size,
        )

        self._queue_channels: dict[str, "RobustChannel"] = {}

    async def get_connection(self) -> "RobustConnection":
        return await self._connection_pool._get()

    @asynccontextmanager
    async def acquire_connection(self) -> AsyncIterator["RobustConnection"]:
        async with self._connection_pool.acquire() as connection:
            yield connection

    async def get_channel(self) -> "RobustChannel":
        return await self._channel_pool._get()

    @asynccontextmanager
    async def acquire_channel(self, queue_name: Optional[str] = None) -> AsyncIterator["RobustChannel"]:
        if queue_name is not None:
            if queue_name not in self._queue_channels:
                self._queue_channels[queue_name] = await self._channel_pool._get()
            
            yield self._queue_channels[queue_name]
        else:
            async with self._channel_pool.acquire() as channel:
                yield channel

    async def _get_channel(
        self,
        channel_number: Optional[int] = None,
        publisher_confirms: bool = True,
        on_return_raises: bool = False,
    ) -> "RobustChannel":
        async with self.acquire_connection() as connection:
            channel = cast(
                "RobustChannel",
                await connection.channel(
                    channel_number=channel_number,
                    publisher_confirms=publisher_confirms,
                    on_return_raises=on_return_raises,
                ),
            )

            return channel

    async def close(self) -> None:
        for channel in self._queue_channels.values():
            if not channel.is_closed:
                await channel.close()

        if not self._channel_pool.is_closed:
            await self._channel_pool.close()

        if not self._connection_pool.is_closed:
            await self._connection_pool.close()
