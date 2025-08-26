import unittest

import pytest
from fastmcp import Client


pytest_plugins = ('pytest_asyncio',)

async def test_tool_list():

    async with Client("http://localhost:8000/mcp") as client:
        await client.ping()

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(tools)

class MCP(unittest.TestCase):
    pass




if __name__ == '__main__':
    unittest.main()
