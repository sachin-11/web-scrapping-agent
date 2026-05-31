import asyncio
import sys

# Must be set before uvicorn creates its event loop.
# SelectorEventLoop (Windows default) doesn't support subprocess_exec,
# which Playwright needs to launch Chromium.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
