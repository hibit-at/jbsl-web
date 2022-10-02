import asyncio


async def async_hello():
    await print("Hello")

# loop = asyncio.get_event_loop()
# loop.run_until_complete(async_hello())
async_hello()