from __future__ import print_function
import numpy as np
import requests
import json
import ast
import sys

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
	with open(f'{filename}.txt', 'w') as f:
		for i in range(number_of_power_traces):
			response = send_request(f'{server_url}/encrypt', params={'user': USERNAME, 'difficulty': DIFFICULTY})
			response = json.loads(response)
			trace = response['leaks']
			f.write(f'{str(trace)}\n')
		f.close()

def get_means_variances(filename):
	with open(f'{filename}.txt', 'r') as f:
		content = f.readlines()
		traces = [np.array(ast.literal_eval(x.strip())) for x in content] 
		traces = [a[a != np.array(None)] for a in traces] # Remove Nones
		means = [trace.mean() for trace in traces]
		variances = [trace.var() for trace in traces]
		return means, variances

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
	Prints to stderr, for more informative messages.
	"""
	print(*args, file=sys.stderr, **kwargs)

# ========================================================================================


if __name__ == '__main__':
	if len(sys.argv) != 2:
		eprint('Usage: python3 ex02_M1.py <file_name>')
		exit(1)

	main(sys.argv[1])