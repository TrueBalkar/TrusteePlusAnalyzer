import os
import time
import psutil
from configs import *

num_cores = os.cpu_count()
process = psutil.Process()
process.cpu_affinity([10])

os.system('clear')

COLORS = {
    'red': "\033[91m",
    'green': "\033[92m",
    'yellow': "\033[93m",
    'purple': "\033[94m",
    'pink': "\033[95m",
    'cyan': "\033[96m",
    'gray': "\033[97m",
    'black': "\033[98m"
}


def print_color(text, color):
    text = text.replace('\n', '')
    text = text.replace('|n|', '\n')
    print("{}{}\033[00m".format(color, text))


log_path = CONFIGS['Service']['LogsPath']
logs_read_timeout = CONFIGS['Service']['LoggingTimeout']

if not os.path.exists(log_path):
    file = open(log_path, 'w')
file = open(log_path, 'r')

current_file_size = os.path.getsize(log_path)
last_line = 0
while True:
    time.sleep(logs_read_timeout)
    lines = file.readlines()
    for new_last_line, line in enumerate(lines[last_line:]):
        try:
            print_color(line.split('~')[0], COLORS[line.split('~')[-1].strip('\n')])
        except KeyError:
            last_line += new_last_line
            break
    else:
        last_line = len(lines)
    while os.path.getsize(log_path) == current_file_size:
        time.sleep(logs_read_timeout)
    if os.path.getsize(log_path) > current_file_size:
        current_file_size = os.path.getsize(log_path)
        file = open(log_path, 'r')
    else:
        os.system('clear')
        last_line = 0
        current_file_size = os.path.getsize(log_path)
        file = open(log_path, 'r')
