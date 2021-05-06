from __future__ import print_function
import numpy as np
import requests
import json
import ast
import warnings
import sys

warnings.filterwarnings('ignore') # To suppress numpy's RuntimeWarning

# Our GitHub repo:
# https://github.com/chendoy/aes-power-analysis-aoi

# ███╗   ███╗██╗██╗     ███████╗███████╗████████╗ ██████╗ ███╗   ██╗███████╗     ██╗
# ████╗ ████║██║██║     ██╔════╝██╔════╝╚══██╔══╝██╔═══██╗████╗  ██║██╔════╝    ███║
# ██╔████╔██║██║██║     █████╗  ███████╗   ██║   ██║   ██║██╔██╗ ██║█████╗      ╚██║
# ██║╚██╔╝██║██║██║     ██╔══╝  ╚════██║   ██║   ██║   ██║██║╚██╗██║██╔══╝       ██║
# ██║ ╚═╝ ██║██║███████╗███████╗███████║   ██║   ╚██████╔╝██║ ╚████║███████╗     ██║
# ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝     ╚═╝
																					  
# ==================================== configuration =====================================

SERVER_URL = 'http://aoi.ise.bgu.ac.il'
NUM_POWER_TRACES = 100
DIFFICULTY = '1'
USERNAME = '205644941'
RETRY_LIMIT = 10
TIMEOUT = 20 # In seconds

# ========================================================================================


def main(filename):
	download_power_traces(filename, SERVER_URL, NUM_POWER_TRACES)
	means, vars = get_means_variances(filename)
	print(f'Mean\tVariance')

	for i in range(len(means)):
		print(f'{means[i]:.2f}\t{vars[i]:.2f}')


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
		for i in range(number_of_power_traces):
			response = send_request(f'{server_url}/encrypt', params={'user': USERNAME, 'difficulty': DIFFICULTY})
			response = json.loads(response) # Parse JSON string
			trace = response['leaks']
			f.write(f'{str(trace)}\n')
		f.close()


def get_means_variances(filename):
	"""
	Reads the file filename, containing the saved power traces, 
	and calculates the mean and variance of each position in the trace.
		Parameters:
			filename (string) -- the file to read the saved traces from.
		Returns:
			means (numpy array) -- the calculated means of each trace from the file.
			vars (numpy array) -- the calculated variances of each trace from the file.
	"""
	with open(f'{filename}.txt', 'r') as f:
		content = f.readlines()
		traces = [x.strip() for x in content] # Split to lines
		traces = [ast.literal_eval(x) for x in traces] # Convert to python list
		traces = [np.array(x) for x in traces] # Convert to numpy arrays
		traces = np.array(traces, dtype=np.float)
		means = np.nanmean(traces, axis=0)
		vars = np.nanvar(traces, axis=0)
		return means, vars


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
	Prints to stderr, for more debugging purposes.
	"""
	print(*args, file=sys.stderr, **kwargs)


if __name__ == '__main__':
	if len(sys.argv) != 2:
		eprint('Usage: python3 ex02_M1.py <file_name>')
		exit(1)
	main(sys.argv[1])