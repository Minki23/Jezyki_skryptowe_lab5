import re
import datetime
import logging
import random
from collections import defaultdict
from statistics import mean, stdev
import click
import tarfile

def split_into_content(single_log: str):
    fragments = single_log.split(" ")
    if len(fragments[1]) == 0:
        fragments.remove("")
    time = datetime.datetime.strptime(f"{fragments[0]}/{fragments[1]} {fragments[2]}", "%b/%d %H:%M:%S")
    current_year = datetime.datetime.now().year
    formatted_log = {
        "time": time.replace(year=current_year),
        "user": fragments[3],
        "code": fragments[4][-7:-3],
        "message": " ".join(fragments[5:])
    }
    return formatted_log

@click.command()
@click.argument('log_file_path', type=click.Path(exists=True))
@click.option('--loglevel', default='INFO', help='Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
@click.option('--zad4a', nargs=2, type=(int, str), help='Get n random logs for a specific user')
@click.option('--zad4b1', is_flag=True, help='Calculate global mean and standard deviation time')
@click.option('--zad4b2', is_flag=True, help='Calculate users mean and standard deviation time')
@click.option('--zad4c', is_flag=True, help='Print most and least frequent users')


def analyze_logs(log_file_path, log_level, zad4a, zad4b1, zad4b2, zad4c):
    click.echo(f"Analyzing logs from file: {log_file_path}")
    logging.basicConfig(encoding='utf-8', level=log_level)

    with tarfile.open(log_file_path, "r:gz") as tar:
        tar.extractall()
    file_name = log_file_path.split(".")[0][0:]
    total_bytes = 0
    logs_dict = []
    
    with open(f"{file_name}.log", "r") as file:
        for line in file.readlines():
            logging.debug(f"Read {len(line)} bytes.")
            total_bytes += len(line)
            val = split_into_content(line)
            logs_dict.append(val)
            message_type = get_message_type(logs_dict[-1]["message"])

            if message_type == 'successful_login' or message_type == 'connection_closed':
                logging.info(f"Info: {message_type}")
            elif message_type == 'failed_login':
                logging.warning(f"Warning: {message_type}")
            elif message_type == 'invalid_password' or message_type == 'invalid_user':
                logging.error(f"Error: {message_type}")  
            elif message_type == 'break_in_attempt':
                logging.critical(f"Critical : {message_type}")  

    logging.debug(f"Read all: {total_bytes} bytes.")
    if zad4a:
        get_n_random_logs(logs_dict, zad4a[0], zad4a[1])
    if zad4b1:
        get_global_mean_and_stan_deviation_time(logs_dict)
    if zad4b2:
        get_users_mean_and_stdev(logs_dict)
    if zad4c:
        get_most_and_least_frequent_users(logs_dict)
    


ipv4_matcher = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
user_matcher = re.compile(r'(?<=user\s)[a-zA-Z0-9._-]+')
patterns = {
    'successful_login': r'^.*authentication success.*$',
    'failed_login': r'^.*authentication failure.*$',
    'connection_closed': r'^.*Connection closed.*$',
    'invalid_password': r'^.*Failed password.*$',
    'invalid_user': r'^.*Invalid user.*$',
    'break_in_attempt': r'^.*POSSIBLE BREAK-IN ATTEMPT!.*$'
}
message_type_matcher = re.compile(r'')





def get_message_type(log_line: str):
    for key, pattern in patterns.items():
        if re.match(pattern, log_line, re.IGNORECASE):
            return key
    return "other"


def get_user_from_log(log_line: str):
    res = re.findall(user_matcher, log_line)
    if len(res) == 0:
        return None
    return res


def get_ipv4s_from_log(log_line: str):
    res = re.findall(ipv4_matcher, log_line)
    if len(res) == 0:
        return []
    return res[0]


# zadanie 4 a
def get_n_random_logs(logs_dict, n, username):
    user_logs = [log["message"] for log in logs_dict if
                 get_user_from_log(log["message"]) is not None and get_user_from_log(log["message"])[0] == username]
    user_random_logs = []
    if user_logs:
        for _ in range(n):
            user_random_logs.append(random.choice(user_logs))
        print_n_random_logs(user_random_logs)


def print_n_random_logs(lst):
    for elem in lst:
        print(f"{elem}")


# zadanie 4 b 1 (fukcje uzywane tez do obliczen z 4 b2)

def print_mean_and_stand_dev_time(time_mean, standard_deviation):
    print(f"Mean: {time_mean} Standard deviation: {standard_deviation}")


def get_global_mean_and_stan_deviation_time(logs_dict):
    first_time = logs_dict[0]["time"]
    last_time = logs_dict[0]["time"]
    times = []
    index = 0
    size = len(logs_dict)
    for i in range(size - 1):
        if logs_dict[i]["code"] != logs_dict[index]["code"]:
            last_time = logs_dict[i - 1]["time"]
            times.append((last_time - first_time).total_seconds())
            index = i
            first_time = logs_dict[i]["time"]

    if len(times) == 0:
        time_mean = 0
    else:
        time_mean = mean(times)
    if len(times) > 1:
        standard_deviation = stdev(times)
    else:
        standard_deviation = 0
    print_mean_and_stand_dev_time(time_mean, standard_deviation)


# zadanie 4 b 2
def print_user(user):
    print(f"User: {user}")


def get_users_mean_and_stdev(logs_dict):
    users_dict = defaultdict(list)
    for log in logs_dict:
        if get_user_from_log(log["message"]) is not None:
            users_dict[get_user_from_log(log["message"])[0]].append(log)

    for user, user_logs in users_dict.items():
        print_user(user)
        get_global_mean_and_stan_deviation_time(user_logs)


# zadanie 4 c
def print_most_and_least_frequent_users(most_common_user, least_common_user):
    print(f"  most common : {most_common_user} least common: {least_common_user}")


def get_most_and_least_frequent_users(logs_dict):
    users = [get_user_from_log(log["message"])[0] for log in logs_dict if
             get_user_from_log(log["message"]) is not None]
    most_common_user = max(set(users), key=users.count)
    least_common_user = min(set(users), key=users.count)
    print_most_and_least_frequent_users(most_common_user, least_common_user)


if __name__ == "__main__":
    analyze_logs()
