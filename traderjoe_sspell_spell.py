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


############################################
### SETUP - SWAP THRESHOLDS AND SLIPPAGE ###
############################################

# SPELL -> sSPELL swap targets
# a zero value will trigger a swap when the ratio matches base_staking_rate exactly
# a negative value will trigger a swap when the rate is below base_staking_rate
# a positive value will trigger a swap when the rate is above the base_staking_rate
THRESHOLD_SPELL_TO_SSPELL = 0.2 * PERCENT

# sSPELL -> SPELL swap targets
# a positive value will trigger a (sSPELL -> SPELL) swap when the ratio is above base_staking_rate
THRESHOLD_SSPELL_TO_SPELL = 0.5 * PERCENT

# tolerated slippage in swap price (used to calculate amountOutMin)
SLIPPAGE = 0.1 * PERCENT

# define the staking rate file that is being updated by eth_abra_staking_watcher
STAKING_RATE_FILENAME = ".abra_rate"

# BOT OPTIONS
# Toggles used to interact with the contract

# Simulate swaps and approvals
DRY_RUN = True
#Quit after the first successful trade 
ONE_SHOT = False
# How often to run the main look
LOOP_TIME = 1.0


##################################################
### SETUP - GLOBAL VARIABLES, NETWORK, ACCOUNT ###
##################################################

# define main() loop which will contain the swapping / set up logic
# global variables set to allow any function access (unless redefined in scope)
def main():

    #DEFINING GLOBAL VARIABLES
    global spell_contract
    global sspell_contract
    global traderjoe_router_contract
    global traderjoe_lp_contract
    global spell
    global sspell

    try:
        # connecting to avax network
        network.connect("avax-main")

        # Avax supports EIP-1559 transactions, need to set priority fee and allow
        # base fee to change as needed
        network.priority_fee('5 gwei')
        # can set limit on max fee if desired
        #network.max_fee('200 gwei')
    except:
        sys.exit(
            "Could not connect to AVAX network. Run 'brownie networks list' to check for AVAX."
        )

    # attemps to load the user account / wallet
    try:
        global user
        user = accounts.load("botbattles")
    except:
        sys.exit(
            "Could not load account. Verify that account is listed with 'brownie accounts list and that you are using the right password."
        )

    ################################################
    ### SETUP - CONTRACTS AND TOKEN DICTIONARIES ###
    ################################################

    # contract_load helper function is used to pull the SPELL, SSPELL, ROUTER information
    print("\nContracts loaded:")
    spell_contract = contract_load(SPELL_CONTRACT_ADDRESS, "Avalanche Token: SPELL")
    sspell_contract = contract_load(SSPELL_CONTRACT_ADDRESS, "Avalanche Token: sSPELL")
    router_contract = contract_load(
        TRADERJOE_ROUTER_CONTRACT_ADDRESS, "TraderJoe: Router"
    )

    # defining dictionaries for SPELL and SSPELL. leaving blank bc the next two blocks will 
    # use helper functions to pull updated / current data

    spell = {
        "address": SPELL_CONTRACT_ADDRESS,
        "contract": spell_contract,
        "name": None,
        "symbol": None,
        "balance": None,
        "decimals": None,
    }

    sspell = {
        "address": SSPELL_CONTRACT_ADDRESS,
        "contract": sspell_contract,
        "name": None,
        "symbol": None,
        "balance": None,
        "decimals": None,
    }

    spell["symbol"] = get_token_symbol(spell["contract"])
    spell["name"] = get_token_name(spell["contract"])
    spell["decimals"] = get_token_decimals(spell_contract)

    sspell["symbol"] = get_token_symbol(sspell["contract"])
    sspell["name"] = get_token_name(sspell["contract"])
    sspell["decimals"] = get_token_decimals(sspell_contract)

    # terminates if 0 balance in either account
    if (spell["balance"] == 0) and (sspell["balance"] == 0):
        sys.exit("No tokens found.")


    ##########################################
    ### SETUP - APPROVALS AND STAKING RATE ###
    ##########################################

    # Confirming approvals for tokens
    # gets current approval set for the TraderJoe router contract for SPELL / SSPELL
    # issues unlimited approval if not found (calling the token_approve helper)
    print("\nChecking Approvals:")

    if get_approval(spell["contract"], router_contract, user):
        print(f"• {spell['symbol']} OK")
    else:
        token_approve(spell["contract", router_contract])

    if get_approval(sspell["contract"], router_contract, user):
        print(f"• {sspell['symbol']} OK")
    else: 
        token_approve(sspell["contract"], router_contract)

    # goes to the .abra_rate file being updated and pulls most recent stake rate
    try:
        with open(STAKING_RATE_FILENAME, "r") as file:
            base_staking_rate = float(file.read().strip())
            print(f"\nEthereum L1 Staking Rate: {base_staking_rate}")
    except FileNotFoundError:
        sys.exit(
            "Cannot load the base Abracadabra SPELL/sSPELL staking rate. Run 'python3 abra_rate.py' and try again."
        )

    # set balance_refresh to make sure balance is updated and displayed on a first run
    balance_refresh = True

    #######################################################
    ### MAIN LOOP - BALANCE REFRESH AND STAKING UPDATER ###
    #######################################################

    while True:
        # passes starting time of loop to keep track 
        loop_start = time.time()

        # attempts to read the staking rate file for updates
        # prints them if changed
        # updates the internal base_staking_rate variable
        try:
            with open(STAKING_RATE_FILENAME, "r") as file:
                if (result := float(file.read().strip())) != base_staking_rate:
                    base_staking_rate = result
                    print(f"Updated staking rate: {base_staking_rate}")
        except FileNotFoundError:
            sys.exit(
                "Cannot load the base Abracadabra SPELL/sSPELL staking rate. Run 'python3 abra_rate.py' and try again"
            )

        # balance_refresh is set to true above
        # if true, wait 10 seconds then updates user balance of SPELL and SSPELL
        # prints out the user's token balances
        # resets the last seen swap rate variables
        if balance_refresh:
            time.sleep(10)
            spell["balance"] = get_token_balance(spell_contract, user)
            sspell["balance"] = get_token_balance(sspell_contract, user)
            print("\nAccount Balance:")
            print(
                f"• Token #1: {int(spell['balance']/(10**spell['decimals']))} {spell['symbol']} ({spell['name']})"
            )
            print(
                f"• Token #2: {int(sspell['balance']/(10**sspell['decimals']))} {sspell['symbol']} ({sspell['name']})"
            )
            print()
            balance_refresh = False
            last_ratio_spell_to_sspell = 0
            last_ratio_sspell_to_spell = 0


        #############################################
        ### MAIN LOOP - QUOTES, SWAPS, AND TIMING ###
        #############################################

        # get quotes and executre SPELL -> sSPELL swaps if we have a SPELL balance
        if spell["balance"]:
            # "Walrus Operator"
            # calls get_swap_rate, store the output to the result variable, sends to if statement
            if result := get_swap_rate(
                # uses wallets spell balance as the token in
                token_in_quantity=spell["balance"],
                # gets the spell contract address
                token_in_address=spell["address"],
                # address for the desired swap (sspell)
                token_out_address=sspell["address"],
                router=router_contract,
            ):
                # result is a touple with token balance in, token balance out as the result
                spell_in, sspell_out = result
                # sets new spell to sspell ratio
                ratio_spell_to_sspell = round(sspell_out / spell_in, 4)

                # print and save any updated swap values since last look
                if ratio_spell_to_sspell != last_ratio_spell_to_sspell:
                    print(
                        f"{datetime.datetime.now().strftime('[%I:%M:%S %p]')} {spell['symbol']} → {sspell['symbol']}: ({ratio_spell_to_sspell:.4f}/{1 / (base_staking_rate * (1 + THRESHOLD_SPELL_TO_SSPELL)):.4f})"
                    )
                    last_ratio_spell_to_sspell = last_ratio_spell_to_sspell
            else:
                # abandon the for loop to avoid re-using stale data
                break

            # execute SPELL -> sSPELL arb if trigger is satisfied
            # tracking base Abracadabra rate through base_staking_rate
            # being updated by staking rate watcher
            # executes a trade when the quoted swap rate is higher by some percentage that we specified
            if ratio_spell_to_sspell >= 1 / (base_staking_rate * (1 + THRESHOLD_SPELL_TO_SSPELL)):
                print(
                    f"*** EXECUTING SWAP OF {int(spell_in / (10**spell['decimals']))} {spell['symbol']} AT BLOCK {chain.height} ***"
                )
                if token_swap(
                    token_in_quantity=spell_in,
                    token_in_address=spell["address"],
                    token_out_quantity=sspell_out,
                    token_out_address=sspell["address"],
                    router=router_contract,
                ):
                    balance_refresh = True
                    if ONE_SHOT:
                        sys.exit("single shot complete!")

        # get quotes and execute: sSPELL -> SPELL swaps only if we have a balance of sSPELL
        if sspell["balance"]:
            # "Walrus Operator"
            # calls get_swap_rate, store the output to the result variable, sends to if statement
            if result := get_swap_rate(
                # uses wallets sspell balance as the token in
                token_in_quantity=sspell["balance"],
                # gets the sspell contract address
                token_in_address=sspell["address"],
                # address for the desired swap (spell)
                token_out_address=spell["address"],
                router=router_contract,
            ):
                # result is a touple with token balance in, token balance out as the result
                sspell_in, spell_out = result
                # sets new sspell to spell ratio
                ratio_sspell_to_spell = round(spell_out / sspell_in, 4)

                # print and save any updated swap values since last loop
                if ratio_sspell_to_spell != last_ratio_sspell_to_spell:
                    print(
                        f"{datetime.datetime.now().strftime('[%I:%M:%S %p]')} {sspell['symbol']} → {spell['symbol']}: ({ratio_sspell_to_spell:.4f}/{base_staking_rate * (1 + THRESHOLD_SSPELL_TO_SPELL):.4f})"
                    )
                    last_ratio_sspell_to_spell = last_ratio_sspell_to_spell
            else:
                #abandon the for loop to avoid re-using stale data
                break

            # execute sSPELL -> SPELL arb if trigger is satisfied
            # tracking base Abracadabra rate through base_staking_rate
            # being updated by staking rate watcher
            # executes a trade when the quoted swap rate is higher by some percentage that we specified
            if ratio_sspell_to_spell >= base_staking_rate * (1 + THRESHOLD_SSPELL_TO_SPELL):
                print(f"*** EXECUTING SWAP OF {int(sspell_in/(10**sspell['decimals']))} {sspell['symbol']} AT BLOCK {chain.height} ***")
                if token_swap(
                    token_in_quantity=sspell_in,
                    token_in_address=sspell["address"],
                    token_out_quantity=spell_out,
                    token_out_address=spell["address"],
                    router=router_contract,
                ):
                    balance_refresh = True
                    if ONE_SHOT:
                        sys.exit("single shot complete!")

        loop_end = time.time()

        # control the loop timing more precisely by measuring start and end time and sleeping as needed
        if (loop_end - loop_start) >= LOOP_TIME:
            continue
        else:
            time.sleep(LOOP_TIME - (loop_end - loop_start))
            continue




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
    if DRY_RUN:
        # pretend we have unlimited approval
        return 2**256 - 1
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
    if DRY_RUN:
        # returns fake balance for testing
        return 10000 * 10**18
    try:
        return token.balanceOf.call(user)
    except Exception as e:
        print(f"Exception in get_token_balance: {e}")
        raise

# retrieves the decimals variable for a given token contract address
def get_token_decimals(token):
    try:
        return token.decimals()
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
    token_in_quantity,
    token_in_address,
    token_out_quantity,
    token_out_address,
    router,
):
    if DRY_RUN:
        print ("**** DRY RUN! SWAPPING IS DISABLED ***")
        return True

    try:
        router.swapExactTokensForTokens(
            token_in_quantity,
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

# only executes main loop if this file is called directly
if __name__ == "__main__":
    main()

    