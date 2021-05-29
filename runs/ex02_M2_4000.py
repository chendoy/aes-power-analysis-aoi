from __future__ import print_function
import numpy as np
import requests
import json
from sbox import AesSbox
from scipy.stats import pearsonr
import ast
import time
from tqdm import tqdm
import warnings
import sys

# 91d75690078e12a51ad1ef92eabbf252 -> 3

warnings.filterwarnings('ignore') # To suppress numpy's RuntimeWarning

# Our GitHub repo:
# https://github.com/chendoy/aes-power-analysis-aoi

# ███╗   ███╗██╗██╗     ███████╗███████╗████████╗ ██████╗ ███╗   ██╗███████╗    ██████╗ 
# ████╗ ████║██║██║     ██╔════╝██╔════╝╚══██╔══╝██╔═══██╗████╗  ██║██╔════╝    ╚════██╗
# ██╔████╔██║██║██║     █████╗  ███████╗   ██║   ██║   ██║██╔██╗ ██║█████╗       █████╔╝
# ██║╚██╔╝██║██║██║     ██╔══╝  ╚════██║   ██║   ██║   ██║██║╚██╗██║██╔══╝      ██╔═══╝ 
# ██║ ╚═╝ ██║██║███████╗███████╗███████║   ██║   ╚██████╔╝██║ ╚████║███████╗    ███████╗
# ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝

# ==================================== configuration ==============================
																				# |
SERVER_URL = 'http://aoi.ise.bgu.ac.il'											# |
NUM_POWER_TRACES = 4000														# |
DIFFICULTY = '2'																# |
USERNAME = '2056449411'															# |
RETRY_LIMIT = 10																# |
NUM_KEY_BYTES = 16																# |
TIMEOUT = 20 # In seconds														# |
NUM_BYTES_POSSI = 256															# |
																				# |
# =================================================================================


def main(filename):
	eprint('Downloading traces...')
	download_power_traces(filename, SERVER_URL, NUM_POWER_TRACES)
	plaintexts = read_plaintexts(filename) # (D,16)
	traces = read_traces(filename) # (D,T)
	eprint('Starting power analysis...')
	start_time = time.time()
	possible_keys = []
	for num_traces in [NUM_POWER_TRACES]:
		guessed_bytes = cpa_attack(plaintexts, traces, num_traces=num_traces)
		possible_keys.append(guessed_bytes)
	key = majority_voting(possible_keys)
	key = get_key_str(key)
	end_time = time.time()
	eprint('Verifying key...')
	if verify_key(key):
		print(f'{USERNAME},{key},{DIFFICULTY}')
	else:
		print(f'{key} is incorrect')
	eprint(f'Total time (CPA): {end_time-start_time:.2f} seconds')


def read_traces(filename):
	"""
	Reads the power traces from the file filename.
		Parameters:
			filename (string) -- the file to read the saved traces from.
		Returns:
			traces (numpy array) -- the read power traces.
	"""
	with open(f'{filename}.txt', 'r') as f:
		content = f.readlines()
		traces = [x.strip() for x in content] # Split to lines
		traces = [json.loads(x) for x in traces]
		traces = [trace['leaks'] for trace in traces] # Convert to numpy arrays
		traces = [np.array(trace) for trace in traces]
		traces = np.array(traces)
		assert traces.shape[0] == NUM_POWER_TRACES
		return traces


def read_plaintexts(filename):
	"""
	Reads the file filename, containing the saved power traces
	and parses the plaintexts from the file.
		Parameters:
			filename (string) -- the file to read the saved traces from.
		Returns:
			plaintexts (numpy array) -- the parsed plaintexts from the file.
	"""
	with open(f'{filename}.txt', 'r') as f:
		content = f.readlines()
		traces = [x.strip() for x in content] # Split to lines
		traces = [json.loads(x) for x in traces]
		plaintexts = [trace['plaintext'] for trace in traces] # Convert to numpy arrays
		plaintexts = [bytes.fromhex(pt) for pt in plaintexts]
		plaintexts = [list(pt) for pt in plaintexts]

		plaintexts = np.array(plaintexts).reshape(NUM_POWER_TRACES,NUM_KEY_BYTES)
		assert plaintexts.shape == (NUM_POWER_TRACES,NUM_KEY_BYTES)
		return plaintexts


def cpa_attack(plaintexts, traces, num_traces=None):
	"""
	Finds the byte of key one by one using CPA.
		Parameters:
			plaintexts (numpy array) -- the saved plaintexts.
			traces (numpy array) -- the saved power traces.
		Returns:
			key_str (string) -- the string representation of the guessed key.
	"""
	if num_traces is not None: # Work with subset of traces
		plaintexts = plaintexts[:num_traces,:]
		traces = traces[:num_traces,:]

	guessed_bytes = []

	for i in range(NUM_KEY_BYTES):
		guessed_byte = guess_key_byte(plaintexts, traces, i)
		guessed_bytes.append(guessed_byte)

	return guessed_bytes


def guess_key_byte(plaintexts, traces, byte_number):
	"""
	Find the best guess for some key byte using CPA.
		Parameters:
			plaintexts (numpy array) -- the saved plaintexts.
			traces (numpy array) -- the saved power traces.
			byte_number (int) -- the number of the guessed byte, i.e., [0-15].
		Returns:
			best_guess (byte) -- the best guess for the byte in index byte_number.
	"""
	power_consumptions = np.zeros((NUM_BYTES_POSSI,traces.shape[0]))
	for byte_guess in range(NUM_BYTES_POSSI):
		power_consumptions[byte_guess] = measure_power_consumption(plaintexts, byte_guess, byte_number)
	
	corrs = np.zeros((NUM_BYTES_POSSI,traces.shape[0]))

	for byte_guess in range(NUM_BYTES_POSSI):
		current_vec = power_consumptions[byte_guess]
		for timestamp in range(traces.shape[1]):
			corrs[byte_guess,timestamp] = pearsonr(current_vec, traces[:,timestamp])[0]

	best_guess = np.argsort(np.max(corrs, axis=1))[-1]
	second_best = np.argsort(np.max(corrs, axis=1))[-2]
	third_best = np.argsort(np.max(corrs, axis=1))[-3]

	# print('best', hex(best_guess), '\nsecond', hex(second_best),'\n', corrs[second_best,:], '\nthird', hex(third_best),'\n', corrs[third_best,:])
	# print(corrs[best_guess,:])
	return best_guess


def majority_voting(possible_keys):
	# for possible_key in possible_keys:
	# 	print(get_key_str(possible_key))
	return possible_keys[-1]


def measure_power_consumption(plaintexts, byte_guess, byte_number):
	"""
	Measures the hypothetical power consumption according to some byte guess.
		Parameters:
			plaintexts (numpy array) -- the saved plaintexts.
			byte_guess (byte) -- the guessed byte.
			byte_number (int) -- the number of the guessed byte, i.e., [0-15].
		Returns:
			power_consumption (numpy vector) -- the hypothetical power consumption.
	"""
	power_consumption = np.zeros(len(plaintexts))
	for i in range(len(plaintexts)):
		power_consumption[i] = key_operation(plaintexts[i,byte_number], 0xff & byte_guess)
	return power_consumption


def key_operation(d, k):
	"""
	Perform AES's AddRoundKey + ShiftBytes, returning the HW of the result.
		Parameters:
			d (byte) -- a plaintext byte.
			k (byte) -- a key byte
		Returns:
			res (int) -- the HW of the key operations.
	"""
	xored = 0xff & (d ^ k)
	res = hamming_weight(AesSbox[xored])
	return res


def get_key_str(key):
	"""
	Convert the key from byte representation to string representation.
		Parameters:
			key (list) -- a list of bytes (int).
		Returns:
			key (string) -- the string representation.
	"""
	key = [hex(byte)[2:].zfill(2) for byte in key]
	key = ''.join(key)
	return key


def download_power_traces (filename, server_url, number_of_power_traces):
	"""
	Downloads number_of_power_traces power traces from the server server_url
	and saves the results to the file filename in a usable format (.txt), in
	which each row represents a downloaded power trace
		Parameters:
			filename (string) -- the file to save the traces to.
			server_url (string) -- the URL of the server to download the traces from.
			number_of_power_traces (int) -- number of power traces to download.
		Returns:
			This function does not return anything.
	"""
	with open(f'{filename}.txt', 'w') as f:
		for i in tqdm(range(number_of_power_traces)):
			response = send_request(f'{server_url}/encrypt', params={'user': USERNAME, 'difficulty': DIFFICULTY})
			f.write(f'{str(response)}\n')
		f.close()


def hamming_weight(n):
	"""
	Calculates the hamming weight of a given binary number.
		Parameters:
			n (int) -- an integer.
		Returns:
			c (int) -- the hamming weight of the input n.
	"""
	c = 0
	while n:
		c += 1
		n &= n - 1
	return c


def verify_key(key):
	"""
	Verifies the guessed key against the server on /verify route.
		Parameters:
			key (string) -- the guessed key in its string representation.
		Returns:
			correctness (bool) -- whether the guessed key is correct or not.
	"""
	response = send_request(f'{SERVER_URL}/verify', params={'user': USERNAME, 
															'difficulty': DIFFICULTY, 
															'key': key})
	if response == '1': correctness = True
	else: correctness = False
	return correctness


def send_request(server_url, params, limit=RETRY_LIMIT):
	"""
	Wrapper function for sending http requests to the server.
	This function handles exceptions, timeouts, network errors, etc.
		Parameters:
			params (dictionary) -- a python dictionary with the query strings parameters.
			limit (int) -- number of repeating attempts before exiting (default RETRY_LIMIT, see 'configuration' up top).
		Returns:
			elapsed (int) -- amount of time to get the response (in seconds).
			success (str) -- '0' for incorrect password, '1' otherwise (server response).
	"""
	
	if limit == 0:
		eprint(f'Failed to get response for {RETRY_LIMIT} times, exiting...')
		exit(1)
	try:
		res = requests.get(server_url, params=params, timeout=TIMEOUT)
	except requests.exceptions.Timeout:
		eprint('Timeout limit exceeded, re-trying...')
		return send_request(server_url, params, limit-1)
	except requests.exceptions.ConnectionError:
		eprint('Connection error occurred, re-trying...')
		return send_request(server_url, params, limit-1)
	response = res.text
	return response


def eprint(*args, **kwargs):
	"""
	Prints to stderr for debugging purposes.
	"""
	print(*args, file=sys.stderr, **kwargs)


if __name__ == '__main__':
	if len(sys.argv) != 2:
		eprint('Usage: python3 ex02_M1.py <file_name>')
		exit(1)
	main(sys.argv[1])