import sys
import time
import os
from brownie import *
from decimal import Decimal

# Contract addresses (check Snowtrace to verify each)
TRADERJOE_ROUTER_CONTRACT_ADDRESS = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
TOKEN_POOL_CONTRACT_ADDRESS = "0x033C3Fc1fC13F803A233D262e24d1ec3fd4EFB48"

# SNOWTRACE API IMPORT
SNOWTRACE_API_KEY = "GBZ535B69RZYZX6EGRR56RMYI4YNXUK7YU"

# exports environmental variable that bronwnie reads and uses making API requests to snowtrace
os.environ["SNOWTRACE_TOKEN"] = SNOWTRACE_API_KEY

def get_tokens_out_from_tokens_in(
    pool_reserves_token0,
    pool_reserves_token1,
    quantity_token0_in=0,
    quantity_token1_in=0,
    fee=0,
):
    # fails if two input tokens are passed, or if both are 0
    assert not (quantity_token0_in and quantity_token1_in)
    assert quantity_token0_in or quantity_token1_in

    if quantity_token0_in:
        return (
            pool_reserves_token1 * quantity_token0_in * (1 - fee)
            ) // (
            pool_reserves_token0 + quantity_token0_in * (1 - fee)
            )

    if quantity_token1_in:
        return (
            pool_reserves_token0 * quantity_token1_in * (1 - fee)
        ) // (
            pool_reserves_token1 + quantity_token1_in * (1 - fee)
        )

def contract_load(address, alias):
    # attempts to load the saved contract by alias
    # if not found, fetch from network explorer and set alias
    try:
        contract = Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
    finally:
        print(f"• {alias}")
        return contract

def get_swap_rate(token_in_quantity, token_in_address, token_out_address, contract):
    try:
        return contract.getAmountsOut(
            token_in_quantity, [token_in_address, token_out_address]
        )
    except Exception as e:
        print(f"Exception in get_swap_rate: {e}")
        return False

try:
    network.connect("avax-main")
except:
    sys.exit(
        "Could not connect to Avalanche. Verify that brownie lists the Avalanche Mainnet using 'brownie networks list'"
    )

print("\nContracts loaded:")
lp = contract_load(TOKEN_POOL_CONTRACT_ADDRESS, "TraderJoe LP: SPELL - sSPELL")
router = contract_load(TRADERJOE_ROUTER_CONTRACT_ADDRESS, "TraderJoe: Router")

token0 = Contract.from_explorer(lp.token0.call())
token1 = Contract.from_explorer(lp.token1.call())

print()
print(f"token0 = {token0.symbol.call()}")
print(f"token1 = {token1.symbol.call()}")

print()
print("*** Getting Pool Reserves *** ")
x0, y0 = lp.getReserves.call()[0:2]
print(f"token0: \t\t\t{x0}")
print(f"token1: \t\t\t{y0}")

print()
print("*** Calculating Hypothetical Swap: 500,000 SPELL to sSPELL @ 0.3% fee ***")
quote = router.getAmountsOut(500_000 * (10 ** 18), [token1.address, token0.address])[-1]
tokens_out = get_tokens_out_from_tokens_in(
    pool_reserves_token0 = x0,
    pool_reserves_token1 = y0,
    quantity_token1_in = 500_000 * (10 ** 18),
    fee = Decimal("0.003"),
)
print()
print(f"Calculated Tokens Out: \t\t{tokens_out}")
print(f"Router Quoted getAmountsOut: \t{quote}")
print(f"Difference: \t\t\t{quote - tokens_out}")

print()
print("*** Calculating hypothetical swap: 500,000 sSpell to SPELL @ 0.3% fee ***")
quote = router.getAmountsOut(
    500_000 * (10 ** 18),
    [token0.address, token1.address],)[-1]
tokens_out = get_tokens_out_from_tokens_in(
    pool_reserves_token0 = x0,
    pool_reserves_token1 = y0,
    quantity_token0_in = 500_000 * (10 ** 18),
    fee = Decimal("0.003"),
)
print()
print(f"Calculated Tokens Out: \t\t{tokens_out}")
print(f"Router Quoted getAmountsOut: \t{quote}")
print(f"Difference: \t\t\t{quote - tokens_out}")
