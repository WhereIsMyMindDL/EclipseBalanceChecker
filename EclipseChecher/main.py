import uuid
import asyncio
import aiohttp
import pandas as pd
from sys import stderr

import questionary
from loguru import logger
from mnemonic import Mnemonic
from solders.keypair import Keypair

logger.remove()
logger.add(stderr,
           format="<lm>{time:HH:mm:ss}</lm> | <level>{level}</level> | <blue>{function}:{line}</blue> "
                  "| <lw>{message}</lw>")
price_eth = 0


async def get_balance(id_ex, private_key, proxy) -> None:
    async with aiohttp.ClientSession(headers={
        'origin': 'https://eclipse.fight.horse',
        'referer': 'https://eclipse.fight.horse/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/131.0.0.0 Safari/537.36',
    }) as client:
        proxy: str = f"http://{proxy}" if proxy is not None else None
        keypair = Keypair.from_base58_string(private_key)
        json_data = {
            'method': 'getBalance',
            'jsonrpc': '2.0',
            'params': [
                str(keypair.pubkey()),
                {
                    'commitment': 'confirmed',
                },
            ],
            'id': str(uuid.uuid4()),
        }

        r = await client.post(
            url='https://fighthor-eclipse-19ae.mainnet.eclipse.rpcpool.com/',
            json=json_data,
            proxy=proxy,
        )
        if r.status == 200:
            response_json: dict = await r.json()
            balance_eth = response_json['result']['value'] / 10 ** 9
            exel.loc[(id_ex - 1), 'Balance in ETH'] = balance_eth
            exel.loc[(id_ex - 1), 'Balance in USD'] = round(balance_eth * price_eth, 3)


async def get_private_key(id_ex, mnemonic) -> None:
    if type(Mnemonic) is str:
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic)
        path = f"m/44'/501'/0'/0'"
        keypair = Keypair.from_seed_and_derivation_path(seed, path)
        exel.loc[(id_ex - 1), 'Private Key'] = keypair
        exel.to_excel('accounts_data.xlsx', header=True, index=False)
        logger.success(f'Success get and write private key')


async def start(account: list, id_acc: int, semaphore) -> None:
    async with semaphore:
        try:
            if choice.__contains__('Get Private Key from Mnemonic'):
                await get_private_key(id_ex=id_acc, mnemonic=account[0])
            elif choice.__contains__('Get balance'):
                await get_balance(id_ex=id_acc, private_key=account[1].strip(), proxy=account[2])

        except Exception as e:
            logger.error(f'#{id_acc} | Failed: {str(e)}')


async def main() -> None:
    global price_eth
    async with aiohttp.ClientSession() as client:
        r = await client.get(
            url='https://whaleeclipse.fight.horse/api/prices',
        )
        if r.status == 200:
            r_json: dict = await r.json()
            price_eth = r_json['ethereum']['usd']

    semaphore: asyncio.Semaphore = asyncio.Semaphore(10)

    tasks: list[asyncio.Task] = [
        asyncio.create_task(coro=start(account=account, id_acc=idx, semaphore=semaphore))
        for idx, account in enumerate(accounts, start=1)
    ]
    await asyncio.gather(*tasks)
    exel.to_excel('accounts_data.xlsx', header=True, index=False)
    logger.success(f'Success get and write balance')
    print()


if __name__ == '__main__':
    with open('accounts_data.xlsx', 'rb') as file:
        exel = pd.read_excel(file)
    exel = exel.astype({'Private Key': 'str'})

    choice = questionary.select(
        "Select work mode:",
        choices=[
            "Get Private Key from Mnemonic",
            "Get balance",
            "Exit",
        ]
    ).ask()

    if 'Exit' in choice:
        exit()

    accounts: list[list] = [
        [
            row["Mnemonic"] if isinstance(row["Mnemonic"], str) else None,
            row["Private Key"] if isinstance(row["Private Key"], str) else None,
            row["Proxy"] if isinstance(row["Proxy"], str) else None,
        ]
        for index, row in exel.iterrows()
    ]

    logger.info(f'My channel: https://t.me/CryptoMindYep')
    logger.info(f'Total wallets: {len(accounts)}\n')
    asyncio.run(main())

    logger.info('The work completed')
    logger.info('Thx for donat: 0x5AfFeb5fcD283816ab4e926F380F9D0CBBA04d0e')
