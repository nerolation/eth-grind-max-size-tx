import os
import numpy as np
import snappy
from copy import copy
import random


def distribute_values_evenly(arr, value):
    """
    Rearrange elements in the array to avoid consecutive occurrences of `value`,
    without changing the total count of `value` or other elements.

    Parameters:
    - arr: Numpy array of values.
    - value: The value to distribute evenly.

    Returns:
    - A numpy array with `value` distributed to avoid consecutive placements.
    """
    # Convert input to a numpy array to ensure array operations can be performed
    arr = np.array(arr)
    
    # Identify indices of the specified value and other values
    value_indices = np.where(arr == value)[0]
    other_indices = np.where(arr != value)[0]
    
    # Count occurrences of the specified value
    value_count = len(value_indices)
    
    # Create a new array to hold the rearranged elements
    new_arr = np.empty_like(arr)
    
    # Calculate step size to distribute 'value' evenly across 'new_arr'
    step = len(arr) / (value_count + 1)
    
    # Place 'value' at evenly spaced intervals, avoiding consecutive placements
    value_positions = (np.arange(value_count) * step).astype(int)
    
    # Fill in the positions with 'value'
    new_arr[value_positions] = value
    
    # Keep track of positions already filled
    filled_positions = set(value_positions)
    
    # Fill in the remaining positions with other values
    other_values_pos = [pos for pos in range(len(arr)) if pos not in filled_positions]
    new_arr[other_values_pos] = arr[other_indices]
    return list(new_arr)

def generate_data_optimized(zero_calldata_size, nonzero_calldata_size):
    # Directly generate zeros and non-zeros in the most efficient manner
    zeros = b'\x00' * zero_calldata_size
    nonzero_random_bytes = bytes([random.randint(1, 255) for _ in range(nonzero_calldata_size)])
    data = zeros + nonzero_random_bytes
    data_array = np.frombuffer(data, dtype=np.int8)     
    data_list = distribute_values_evenly(list(data), 0)
    modified_data = bytes(data_list)
    return modified_data


def grind_max_size_block_optimized():
    largest = 0
    largest_data = None
    for i in range(1):
        data = generate_data_optimized(CALLDATA_ZEROS, CALLDATA_NONZERO)
        data_comp = snappy.compress(data)
        if len(data_comp) > largest:
            largest = len(data_comp)
            largest_data = data_comp
            if CALLDATA_ZEROS:
                print(f"CALLDATA_ZEROS = {data.count(0):,} Size: {largest/1024**2:,.6f} MB | COMP SIZE: {len(data_comp)/1024**2:,.6f} MB")
    return largest, largest_data

    
# Constants
ZERO_RATE = 0.29
CALLDATA_SIZE = 17_000_000
CALLDATA_ZEROS = int(CALLDATA_SIZE / 4 * ZERO_RATE)
CALLDATA_NONZERO = int(CALLDATA_SIZE / 16 * (1 - ZERO_RATE))
assert (CALLDATA_ZEROS * 4 + CALLDATA_NONZERO * 16) <= CALLDATA_SIZE


results = {}
for i in range(1,21):
    CALLDATA_ZEROS = int(CALLDATA_SIZE / 4 * ZERO_RATE)
    CALLDATA_NONZERO = int(CALLDATA_SIZE / 16 * (1 - ZERO_RATE))
    assert (CALLDATA_ZEROS * 4 + CALLDATA_NONZERO * 16) <= CALLDATA_SIZE
    largest, largest_data = None,None
    largest, largest_data = grind_max_size_block_optimized()
    results[i] = (largest_data, CALLDATA_ZEROS)
    
max_result = [len(results[i][0]) for i in results.keys()]
calldata = results[max_result.index(max(max_result))+1][0]
print(f"Iteration {max_result.index(max(max_result))+1} had the max size block")
######################################

# Load Private Key
with open("sepolia_pk.txt", "r") as file:
    private_key = file.read().strip()

# Private Key to Account
account = w3.eth.account.from_key(private_key)
nonce = w3.eth.get_transaction_count(account.address)
to_address = "0x000000000000000000000000000000000000dEaD"
print(f"Sending from {account.address} to {to_address}")
print(f"Balance of {float(w3.from_wei(w3.eth.get_balance(account.address), 'ether')):,.3f} ETH")
print(f"Current nonce: {nonce}")

signed_transactions = []
for i in range(NR_OF_TXS):
    # Prepare Transaction
    transaction = {
        'nonce': nonce+i,
        'to': "0x000000000000000000000000000000000000dEaD",
        'value': w3.to_wei(0, 'ether'),
        'gas': 29967996,
        'maxFeePerGas': 40, #max_fee_per_gas,
        'maxPriorityFeePerGas': 40, #max_priority_fee_per_gas,
        'data': calldata,
        'chainId': 17000
    }
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    signed_transactions.append(signed_transaction)
print(f"Prepared {len(signed_transactions)} transactions")

with open("nice_tx.txt", "w") as file:
    file.write(str(signed_transaction.rawTransaction.hex()))
