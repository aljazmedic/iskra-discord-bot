import argparse


def run_args_init():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file', '-f', help="Log file name.", dest="log_file_name", type=str, default='%s.log')
	parser.add_argument('--log_type', help="Log Mode. Either append or write.", dest="log_mode", choices=['w', 'a'], type=str, default='a')
	parser.add_argument('--log_dir', help="Log Dir.", dest="log_dir", type=str, default='logs/')
	level_group = parser.add_mutually_exclusive_group()
	level_group.add_argument('--verbose', '-v', action="store_true", default=False)
	level_group.add_argument('--quiet', '-q', action="store_true", default=False)
	return parser.parse_args()
