## Stable Watch - Built alongside BTD tutorial

# SETUP
import time
import datetime
from brownie import *

# Load the user account
user = accounts.load('botbattles')

# Connect to the network
network.connect('avax-main')

# Load the token contracts
print("Loading Contracts:")
dai_contract = Contract.from_explorer('0xd586e7f844cea2f87f50152665bcbc2c279d8d70')
mim_contract = Contract.from_explorer('0x130966628846bfd36ff31a822705796e8cb8c18d')
usdc_contract = Contract.from_explorer('0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664')
usdt_contract = Contract.from_explorer('0xc7198437980c041c805a1edcba50c1ce5db95118')
wavax_contract = Contract.from_explorer('0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7')

# Load the router contract
router_contract = Contract.from_explorer('0x60aE616a2155Ee3d9A68541Ba4544862310933d4')


# DATA STRUCTURES

# Prepare a data structure for each token
dai = {
    "address": dai_contract.address,
    "symbol": dai_contract.symbol(),
    "decimals": dai_contract.decimals(),
}

mim = {
    "address": mim_contract.address,
    "symbol": mim_contract.symbol(),
    "decimals": mim_contract.decimals(),
}

usdc = {
    "address": usdc_contract.address,
    "symbol": usdc_contract.symbol(),
    "decimals": usdc_contract.decimals(),
}

usdt = {
    "address": usdt_contract.address,
    "symbol": usdt_contract.symbol(),
    "decimals": usdt_contract.decimals(),
}

# Prepare a data structure for each unique pair
token_pairs = [
    (dai, mim),
    (mim, dai),
    (dai, usdc),
    (usdc, dai),
    (usdt, dai),
    (dai, usdt),
    (usdc, usdt),
    (usdt, usdc),
    (usdt, mim),
    (mim, usdt),
    (usdc, mim),
    (mim, usdc),
]


# MAIN PROGRAM

# Set up a loop
while True:
        # for all of the currency pairs listed in otken_pairs   
        for pair in token_pairs:
            # define first token as the "token in", second as "token out"
            token_in = pair[0]
            token_out = pair[1]
            qty_out = (
                # call the getAmountsOut method from the router_contract
                router_contract.getAmountsOut(
                    # set initial token quantity to 1
                    1 * (10 ** token_in["decimals"]),
                    # pass a list of addresses, starting with token in address, getting wvax wrapper, ending with token out address
                    [
                        token_in["address"],
                        wavax_contract.address,
                        token_out["address"],
                    ],
                # limit results to last pair - aka token out and divide the token by its decimal 
                ) [-1] / (10 ** token_out["decimals"])
            )
            # if block to check if there is at least 1% profit in swap
            if qty_out >= 1:
                # print values w/ f string 
                print(
                    f"{datetime.datetime.now().strftime('[%I:%M:%S %p]')} {token_in['symbol']} -> {token_out['symbol']}:({qty_out:.3f})"
                )
            # pause to avoid rate-limiting
            time.sleep(0.1)
