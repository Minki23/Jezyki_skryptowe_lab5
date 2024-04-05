import re
import sys
import tarfile 
import datetime
ipv4_matcher = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
user_matcher = re.compile(r'(?<=user\s)[a-zA-Z0-9._-]+')
message_type_matcher = re.compile(r'^(?!.*(?:Failed password|Invalid user|Connection closed|Received disconnect)).*$', re.MULTILINE)
def split_into_content(single_log:str):
  fragments=single_log.split(" ")
  if len(fragments[1])==0:
    fragments.remove("")
  time=datetime.datetime.strptime(f"{fragments[0]}/{fragments[1]} {fragments[2]}","%b/%d %H:%M:%S")
  current_year = datetime.datetime.now().year
  formatted_log = {
  "time" : time.replace(year=current_year),
  "user" : fragments[3],
  "code" : fragments[4][-7:-3],
  "message" : " ".join(fragments[5:])
  }
  return formatted_log

def main():
  with tarfile.open(f'{sys.argv[1]}', "r:gz") as tar:  
    tar.extractall()
  file_name=sys.argv[1].split(".")[1][1:]
  dict=[]
  with open(f"{file_name}.log","r") as file:
    for line in file.readlines():
      dict.append(split_into_content(line))
      # ipv4=get_ipv4s_from_log(dict[-1]["message"])
      # if ipv4[0]:
      #   print(ipv4[1])
      # user=get_user_from_log(dict[-1]["message"])
      # if user[0]:
      #   print(user[1])
      message_type = get_message_type(dict[-1]["message"])
      if message_type[0]:
        print(message_type)

def get_message_type(log_line:str):
  res=re.findall(message_type_matcher,log_line)
  if len(res)==0:
    return (True,log_line)
  return (False,res)

def get_user_from_log(log_line:str):
  res=re.findall(user_matcher,log_line)
  if len(res)==0:
    return False,""
  return (True,res)

def get_ipv4s_from_log(log_line:str):
  res=re.findall(ipv4_matcher,log_line)
  if len(res)==0:
    return False,""
  return (True,res)

if __name__ == "__main__":
  main()