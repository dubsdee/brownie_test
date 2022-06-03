# brownie_scripts
Testing out some scripts using Python and Brownie

- Oneshotbot.py: This is a swapping script that checks the price of a stable coin (MIM / DAI pair in the example), runs the pricing of a MIM -> WAVAX -> DAI swap and executes if the result is within a defined price point.

- Stablewatch.py: This is a script that pulls a basket of stablecoin pairs (stored as tuples) from an AVAX router and prints out swaps that have a defined price point (ie swap results in a 1% gain, etc.)