import re
import sys
import tarfile 
import datetime
import logging
import random
import argparse
import click
from collections import Counter, defaultdict
from statistics import mean, stdev, pstdev

log_dict_pattern = re.compile(r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<user>\w+)\s+sshd\[(?P<code>\d+)\]:\s+(?P<message>.*)")
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

def print_dict(log):
    print(
        f"""
        Time: {log["time"]}
        Code: {log['code']}
        User: {log['user']}
        Message: {log['message']}
        """
    )

def split_into_content(single_log:str):
    fragments = single_log.split(" ")
    if len(fragments[1]) == 0:
        fragments.remove("")
    time = datetime.datetime.strptime(f"{fragments[0]}/{fragments[1]} {fragments[2]}", "%b/%d %H:%M:%S")
    current_year = datetime.datetime.now().year
    formatted_log = {
        "time" : time.replace(year=current_year),
        "user" : fragments[3],
        "code" : fragments[4][-7:-3],
        "message" : " ".join(fragments[5:])
    }
    return formatted_log

#2 a
def parse_log_entry(log:str, loglevel):
    match = re.match(log_dict_pattern, log)
    if match:
        data = match.groupdict()
        year = "2024"
        timestamp_str = f"{year}-{data['month']}-{data['day']} {data['time']}"
        timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%b-%d %H:%M:%S")
        user = data['user']
        message = data['message']
        code = int(data['code'])
        dict={
            "time": timestamp,
            "user": user,
            "code": code,
            "message": message
        }
        if loglevel is not None:
            print_log_level(dict)
        return dict
    return None
   
   #2 b
def get_ipv4s_from_log(log_line:str):
    res = re.findall(ipv4_matcher, log_line)
    if len(res) == 0:
        return []
    return res[0]
#2 c
def get_user_from_log(log_line:str):
    res = re.findall(user_matcher, log_line)
    if len(res) == 0:
        return None
    return res
#2 d
def get_message_type(log_line:str):
    for key, pattern in patterns.items():
        if re.match(pattern, log_line, re.IGNORECASE):
            return key
    return "other"
#do not use

#3
def print_log_level(log_line: dict):
    message_type = get_message_type(log_line["message"])
    logging.debug(f"Debug: {len(log_line['message'].encode('utf-8'))} Bytes")
    if message_type == 'successful_login' or message_type == 'connection_closed':
        logging.info(f"Info: {message_type}")
    elif message_type == 'failed_login':
        logging.warning(f"Warning: {message_type}")
    elif message_type == 'invalid_password' or message_type == 'invalid_user':
        logging.error(f"Error: {message_type}")  
    elif message_type == 'break_in_attempt':
        logging.critical(f"Critical : {message_type}")        
#1
def get_dict(loglevel):
    with tarfile.open(f'{sys.argv[1]}', "r:gz") as tar:  
        tar.extractall()
    file_name=sys.argv[1].split(".")[0][0:]
    total_bytes = 0
    logs=[]
    with open(f"{file_name}.log","r") as file:
        for line in file.readlines():
            total_bytes += len(line.encode('utf-8'))
            val= split_into_content(line)
            logs.append(val)
            if loglevel is not None:
                print_log_level(val)
    return logs

# 2 click
@click.command()
@click.argument('log_file_path', type=click.Path(exists=True))
@click.option('--loglevel', default='INFO', help='Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
@click.option('--ex2a', is_flag=True,help='Print dictionaries')
@click.option('--ex2b',is_flag=True, help='Print dictionaries')
@click.option('--ex2c',is_flag=True, help='Print all usernames found in the logs')
@click.option('--ex2d', is_flag=True,help='Print all message types found in the logs')
@click.option('--ex4a', is_flag=True,nargs=2, type=(int, str), help='Get n random logs for a specific user: you must give n-int and username-string')
@click.option('--ex4b1',is_flag=True,help='Calculate global mean and standard deviation time')
@click.option('--ex4b2',is_flag=True, help='Calculate users mean and standard deviation time')
@click.option('--ex4c', is_flag=True,help='Print most and least frequent users')
def main(log_file_path, loglevel, ex2a, ex2b, ex2c, ex2d, ex4a, ex4b1, ex4b2, ex4c):
    if loglevel is not None:
        logging.basicConfig(encoding="utf-8", level=loglevel)
    logs=[]
    if ex2a:
        with tarfile.open(f'{log_file_path}', "r:gz") as tar:  
            tar.extractall()
        file_name=log_file_path.split(".")[0][0:]
        with open(f"{file_name}.log","r") as file:
            for line in file.readlines():
                logs.append(parse_log_entry(line, loglevel))
        for log in logs:
            print_dict(log)
    else: 
        logs = get_dict(loglevel)
    if ex2b:
        for log in logs:
            print(get_ipv4s_from_log(log["message"]))
    elif ex2c:
        for log in logs:
            print(get_user_from_log(log["message"]))
    elif ex2d:
        for log in logs:
            print(get_message_type(log["message"]))
    elif ex4a:
        get_n_random_logs(logs, ex4a[0], ex4a[1])
    elif ex4b1:
        get_global_mean_and_stan_deviation_time(logs)
    elif ex4b2:
        get_users_mean_and_stdev(logs)
    elif ex4c:
        get_most_and_least_frequent_users(logs)


#zadanie 4 a
def get_n_random_logs(logs_dict, n, username):
  user_logs = [log["message"] for log in logs_dict if get_user_from_log(log["message"]) is not None and get_user_from_log(log["message"])[0] == username ]
  user_random_logs = []
  if user_logs:
    for i in range(n):
      user_random_logs.append(random.choice(user_logs))
    print_n_random_logs(user_random_logs)   
    
def print_n_random_logs(list):
  for elem in list:
    print(f"{elem}".replace("\n",""))

#zadanie 4 b 1
def  print_mean_and_stand_dev_time(time_mean, standard_deviation):
  print(f"Mean: {time_mean} Standard deviation: {standard_deviation}")

def get_global_mean_and_stan_deviation_time(logs_dict):
  first_time = logs_dict[0]["time"]
  last_time = logs_dict[0]["time"]
  times = []
  index = 0
  size = len(logs_dict)
  for i in range (size-1):
    if logs_dict[i]["code"] != logs_dict[index]["code"]:
      last_time = logs_dict[i-1]["time"]
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

 
#zadanie 4 b 2
def get_users_mean_and_stdev(logs_dict):
  users_dict = defaultdict(list)
  for log in logs_dict:
    if get_user_from_log(log["message"]) is not None:  
      users_dict[get_user_from_log(log["message"])[0]].append(log)
 
  for user, user_logs in users_dict.items():
     print(f"User: {user}")
     get_global_mean_and_stan_deviation_time(user_logs)



#zadanie 4 c
def get_most_and_least_frequent_users(logs_dict):
    users = [get_user_from_log(log["message"])[0] for log in logs_dict if get_user_from_log(log["message"]) is not None]
    most_common = max(set(users), key=users.count)
    least_common = min(set(users), key=users.count)  
    print(f"Most common : {most_common}\nLeast common: {least_common}" )

def get_dict(loglevel):
  with tarfile.open(f'{sys.argv[1]}', "r:gz") as tar:  
    tar.extractall()
  file_name=sys.argv[1].split(".")[0][0:]
  total_bytes = 0
  logs=[]
  with open(f"{file_name}.log","r") as file:
    for line in file.readlines():
      total_bytes += len(line.encode('utf-8'))
      val= split_into_content(line)
      logs.append(val)
      if loglevel is not None:
        print_log_level(val)
  return logs

if __name__ == "__main__":
    main()
