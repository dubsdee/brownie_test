# Set up and importing required packages
import sys
import time
import datetime
import requests
import os
from brownie import *

# Contract addresses (check Snowtrace to verify each)
TRADERJOE_ROUTER_CONTRACT_ADDRESS = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
SPELL_CONTRACT_ADDRESS = "0xce1bffbd5374dac86a2893119683f4911a2f7814"
SSPELL_CONTRACT_ADDRESS = "0x3ee97d514bbef95a2f110e6b9b73824719030f7a"

# SNOWTRACE API IMPORT
SNOWTRACE_API_KEY = "GBZ535B69RZYZX6EGRR56RMYI4YNXUK7YU"

# exports environmental variable that bronwnie reads and uses making API requests to snowtrace
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

# HELPER VALUES
# Added for readability / coding 
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
PERCENT = 0.01

# BOT OPTIONS
# Toggles used to interact with the contract

# Simulate swaps and approvals
DRY_RUN = False
#Quit after the first successful trade 
ONE_SHOT = False
# How often to run the main look
LOOP_TIME = 1.0

# SWAP THRESHOLDS AND SLIPPAGE

# SPELL -> sSPELL swap targets
# a zero value will trigger a swap when the ratio matches base_staking_rate exactly
# a negative value will trigger a swap when the rate is below base_staking_rate
# a positive value will trigger a swap when the rate is above the base_staking_rate
THRESHOLD_SPELL_TO_SSPELL = 0.2 * PERCENT

# sSPELL -> SPELL swap targets
# a positive value will trigger a (sSPELL -> SPELL) swap when the ratio is above base_staking_rate
THRESHOLD_SSPELL_TO_SPELL = 1.2 * PERCENT

# tolerated slippage in swap price (used to calculate amountOutMin)
SLIPPAGE = 0.1 * PERCENT

# function definitions

# retrieves current balance of account
def account_get_balance(account):
    try:
        return account.balance()
    except Exception as e:
        print(f"Exception in account_get_balance: {e}")

# first attempts to retriece a saved contract by its alias
# if not available, retrieves it from the explorer and sets alias for faster loading
def contract_load(address, alias):
    # attempts to load the saved contract by alias
    # if not found, fetch from network explorer and set alias
    try:
        contract = Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
    finally:
        print(f". {alias}")
        return contract

# retrieves the token approval value for a given routing contract and user
def get_approval(token, router, user):
    try:
        return token.allowance.call(user, router.address)
    except Exception as e:
        print(f"Exception in get_approval: {e}")
        return False

# retrieves the token name
def get_token_name(token):
    try:
        return token.name.call()
    except Exception as e:
        print(f"Exception in get_token_name: {e}")
        raise

# retrieves the shorthand symbol
def get_token_symbol(token):
    try:
        return token.symbol.call()
    except Exception as e:
        print(f"Exception in get_token_symbol: {e}")
        raise

# retrieves the balance associated with a given user at a token contract address
def get_token_balance(token, user):
    try:
        return token.balanceOf.call(user)
    except Exception as e:
        print(f"Exception in get_token_balance: {e}")
        raise

# retrieves the decimals variable for a given token contract address
def get_token_decimals(token):
    try:
        return token.decimal()
    except Exception as e:
        print(f"Exception in get_token_decimals: {e}")
        raise

# set the token approval for a given router contract to spend tokens at a given token contract on behalf of our user
# includes a default value that will set unlimited if not specifed
def token_approve(token, router, value="unlimited"):
    if DRY_RUN:
        return True
    
    if value == "unlimited":
        try:
            token.approve(
                router,
                2 ** 256 - 1,
                {"from": user},
            )
            return True
        except Exception as e:
            print(f"Exception in token_approve: {e}")
            raise
    else:
        try:
            token.approve(
                router,
                value,
                {"from": user},
            )
            return True
        except Exception as e:
            print(f"Exception in token_approve: {e}")
            raise

# returns a two-value touple with values for token quantity in and token quantity out for a given pair of token contract addresses and router addresses
def get_swap_rate(token_in_quantity, token_in_address, token_out_address, router):
    try:
        return router.getAmountsOut(
            token_in_quantity, [token_in_address, token_out_address]

        )
    except Exception as e:
        print(f"Exception in get_swap_rate: {e}")
        raise

# calls the router's swapExactTokensForTokens() method for the given token quantities, addresses and route rcontract
def token_swap(
    token_in_quantitiy,
    token_in_address,
    token_out_quantity,
    token_out_address,
    router,
):
    if DRY_RUN:
        return True

    try:
        router.swapExactTokensForTokens(
            token_in_quantitiy,
            int(token_out_quantity * (1 - SLIPPAGE)),
            [token_in_address, token_out_address],
            user.address,
            int(1000 * (time.time()) + 30 * SECOND),
            {"from": user},
        )
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

    