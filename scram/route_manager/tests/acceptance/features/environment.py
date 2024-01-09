import asyncio
from channels.layers import get_channel_layer


async def reset_paths():
    channel_layer = get_channel_layer()
    await channel_layer.group_send("translator_block", {"type": "testing_only_reset_paths"})


def after_scenario(context):
    asyncio.run(reset_paths())
