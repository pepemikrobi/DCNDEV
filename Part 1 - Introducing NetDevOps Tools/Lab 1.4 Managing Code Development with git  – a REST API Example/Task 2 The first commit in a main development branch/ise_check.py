#!/usr/bin/python

import sys

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print ("""Usage:
        ise_check.py <pod_number> <user> <password>
    
        where <pod_number> is in 1...5""")
        exit(1)

    pod = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    print (f'Arguments: pod {pod}, user {username}, pass {password}')
