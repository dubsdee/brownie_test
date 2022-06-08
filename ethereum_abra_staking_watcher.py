## 
## Script to manually calculate the staking rate of SPELL / sSPELL and tracks /
## compares the result to the abra_rate file. 
## If new rate, the new rate is printed to console and written to the abra_rate file, followed by line increment
## Script pulls information every 60 seconds via Infura
##

import sys
import time
import os
from brownie import *

# Linking infura project ID
WEB3_INFURA_PROJECT_ID = "b2493036027144908705930b570ace3c"

# Define spell and sSpell contract address variables
SPELL_CONTRACT_ADDRESS = "0x090185f2135308bad17527004364ebcc2d37e5f6"
SSPELL_CONTRACT_ADDRESS = "0x26FA3fFFB6EfE8c1E69103aCb4044C26B9A106a9"

os.environ["WEB3_INFURA_PROJECT_ID"] = WEB3_INFURA_PROJECT_ID

FILENAME = ".abra_rate"

def main():
    # attempts to connect to the ETH mainnet
    try:
        network.connect("mainnet")
    except:
        sys.exit("Could not connect to Ethereum Mainnet.")
    
    # loads contract addresses 
    print("\nContracts loaded:")
    spell_contract = contract_load(SPELL_CONTRACT_ADDRESS, "Token: SPELL")
    sspell_contract = contract_load(SSPELL_CONTRACT_ADDRESS, "Token: sSPELL")

    # creates a blank file, echos "0.0" to force a refresh in the main loop
    # uses python to open the FILENAME (abra rate) w/ write permissions
    with open(FILENAME, "w") as file:
        file.write(str(0.0) + "\n")

    while True:
        # reads abra_rate from the file, passes the most recent value
        with open(FILENAME, "r") as file:
            abra_rate = float(file.read().strip())

        # main function here - numerator is the total supply, demon is total token
        # rounds to 4 decimals
        try:
            result = round(
                # total amount of sSpell minted, called via Spell contract (includes burn adjustments)
                spell_contract.balanceOf(sspell_contract.address)
                /
                # total supply of minted sSpell
                sspell_contract.totalSupply(),
                4
            )
        
        except Exception as e:
            print(f"{e}")
            continue

        if abra_rate and result == abra_rate:
            pass
        else:
            print(f"Updated rate found: {result}")
            abra_rate = result
            with open(FILENAME, "w") as file:
                file.write(str(abra_rate) + "\n")

        time.sleep(60)

def contract_load(address, alias):
    # attempts to load the saved contract
    # if not found, fetch from network explorer and save
    try:
        contract = Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
    finally:
        print(f"• {alias}")
        return contract

# only executes main loop if the file is called directly
if __name__ == "__main__":
    main()