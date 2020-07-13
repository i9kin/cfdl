import requests
from Crypto.Cipher import AES

# a = requests.get('https://codeforces.com')
# print(a.text)


a = "e9ee4b03c1d0822987185d27bca23378"
b = "188fafdbe0f87ef0fc2810d5b3e34705"
c = "d909a82d1d456ca7c35526f64f85c93c"

a = bytes.fromhex(a)
b = bytes.fromhex(b)
c = bytes.fromhex(c)

cipher = AES.new(a, AES.MODE_CBC, b)
plaintext = cipher.decrypt(c).hex()

print(plaintext == "00d28833206ccd9a67176c3190299d6e")


import asyncio
import aiohttp


async def main():
    session = aiohttp.ClientSession(cookies={"RCPC": plaintext})

    url = "https://codeforces.com/"
    async with session.get(url) as resp:
        print(await resp.text())

    await session.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
