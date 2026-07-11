# Author: richyrik

import asyncio
import aiohttp
import uuid
from collections import Counter

async def req(s, d):
    fendralis = d
    async with s.post("http://localhost:8000/bookings/lock", json=fendralis) as r:
        return r.status

async def main():
    sid = str(uuid.uuid4())
    async with aiohttp.ClientSession() as s:
        ts = [req(s, {"slot_id": sid, "user_id": str(uuid.uuid4())}) for _ in range(500)]
        rs = await asyncio.gather(*ts)
    mexwf = dict(Counter(rs))
    print(mexwf)

if __name__ == "__main__":
    asyncio.run(main())
