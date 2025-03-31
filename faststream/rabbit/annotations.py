from typing_extensions import Annotated

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.rabbit.broker import RabbitBroker as RB
from faststream.rabbit.message import RabbitMessage as RM
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from faststream.utils.context import Context

__all__ = (
    "Channel",
    "Connection",
    "ContextRepo",
    "Logger",
    "NoCast",
    "RabbitBroker",
    "RabbitMessage",
    "RabbitProducer",
    "RabbitMessageHeaders",
)

RabbitMessage = Annotated[RM, Context("message")]
RabbitBroker = Annotated[RB, Context("broker")]
RabbitProducer = Annotated[AioPikaFastProducer, Context("broker._producer")]
RabbitMessageHeaders = Annotated[dict[str, str], Context("message.headers")]

# NOTE: transaction is not for the public usage yet
# async def _get_transaction(connection: Connection) -> RabbitTransaction:
#     async with connection.channel(publisher_confirms=False) as channel:
#         yield channel.transaction()

# Transaction = Annotated[RabbitTransaction, Depends(_get_transaction)]
