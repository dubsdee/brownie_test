# SETUP
import time
import datetime
import sys
from brownie import *

# Connect to the network
network.connect('avax-main')

# Load the user account
user = accounts.load('botbattles')

# Load the token contracts
print("Loading Contracts:")
dai_contract = Contract.from_explorer('0xd586e7f844cea2f87f50152665bcbc2c279d8d70')
mim_contract = Contract.from_explorer('0x130966628846bfd36ff31a822705796e8cb8c18d')
wavax_contract = Contract.from_explorer('0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7')

# Load the router contract
router_contract = Contract.from_explorer('0x60aE616a2155Ee3d9A68541Ba4544862310933d4')

# DATA STRUCTURES
# Prepare a data structure for each token
dai = {
    "address": dai_contract.address,
    "symbol": dai_contract.symbol(),
    "decimals": dai_contract.decimals(),
    "balance": dai_contract.balanceOf(user.address),
}

mim = {
    "address": mim_contract.address,
    "symbol": mim_contract.symbol(),
    "decimals": mim_contract.decimals(),
    "balance": mim_contract.balanceOf(user.address),
}

# print to confirm load was successful
print(dai)
print(mim)

if mim["balance"] == 0: 
    sys.exit("MIM balance is zero, aborting...")


# MAIN PROGRAM
# Get allowance and set approvals as needed
# checks if the approval for the account at the mim contract is less than remaining mim balance
if mim_contract.allowance(user.address, router_contract.address) < mim["balance"]:
    # if true, call the approval to raise the approved amount to the remaining mim balance
    mim_contract.approve(
        router_contract.address,
        mim["balance"],
        {'from':user.address},
    )
# Set up look
last_ratio = 0.0

# while true - runs till swap
while True:
    try:
        # checking the router for the value of the mim balance swapped to dai
        # stores this value as "qty_out"
        qty_out = router_contract.getAmountsOut(
            mim["balance"],
            [
                mim["address"],
                wavax_contract.address,
                dai["address"]
            ],
        ) [-1]
    except:
        print("Some error occured, retrying...")
        continue
    
    # creates a ratio - rounding the trade value in dai (qty recieved) / starting mim to 3 digits
    ratio = round(qty_out / mim["balance"], 3)
    
    # if last ratio is not the same as new ratio, print that notification and pass to last ratio
    if ratio != last_ratio:
        print(
            f"{datetime.datetime.now().strftime('[%I:%M:%S %p]')} MIM -> DAI: ({ratio:.3f})"
        )
        last_ratio = ratio

    # if the ratio is greater than 1.01 (aka the 1% threshold), start the swap
    if ratio >= 1.01:
        #notification
        print("*** EXECUTING SWAP ***")
        try:
            # calling the swap method
            router_contract.swapExactTokensForTokens(
                # balance of the mim in the contract
                mim["balance"],
                # takes the quantity out of the swap and gives it a 50bps "slippage" gap
                int(0.995*qty_out),
                [
                    mim["address"],
                    wavax_contract.address,
                    dai["address"]
                ],
                user.address,
                1000 * int(time.time() + 60),
                {"from": user},
            )
            print("Swap success!")
        except:
            print("Swap failed, better luck next time!")
        finally:
            break
    
    time.sleep(0.5)
# Fetch, store and print swap rates
# Print interesting results
# Execute a single swap if threshold is met

