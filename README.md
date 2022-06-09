# brownie_scripts
Testing out some scripts using Python and Brownie

- Oneshotbot.py: This is a swapping script that checks the price of a stable coin (MIM / DAI pair in the example), runs the pricing of a MIM -> WAVAX -> DAI swap and executes if the result is within a defined price point.

- Stablewatch.py: This is a script that pulls a basket of stablecoin pairs (stored as tuples) from an AVAX router and prints out swaps that have a defined price point (ie swap results in a 1% gain, etc.)

- Ethereum Abra Staking Watcher.py: Script that pulls the contract data for SPELL and sSPELL on the Ethereum Mainnet and manually calculates the ratio. The script stores the current value in the .abra_rate file and periodically recalculates the ratio, replacing the old rate with the newly calculated value when changes occur. 

- TraderJoe sSpell Spell.py: Script that executes a SPELL/sSPELL or sSPELL/SPELL swap. Pulls data from Ethereum Abra Staking Watcher.py for the E1 ratio, compares to TraderJoe AVAX swap ratio and executes based on defined thresholds. SPELL:sSPELL swaps are done in profit, sSPELL:SPELL swaps are done at lower margin loss in expectation of a net spread on the roundtrip. 