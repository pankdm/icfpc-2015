
import json
import string
import random

def parse_file(file_name):
    s = open(file_name, 'r')
    return json.loads(s.read())


def get_random_string(length):
    s = string.lowercase + string.digits
    return ''.join(random.sample(s, 4))

