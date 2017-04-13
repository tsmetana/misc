#!/usr/bin/python3

import sys
import glob
import os
import signal

def find_pid():
    pid = None
    cmdfiles = glob.glob("/proc/*/cmdline")
    for cmdfile in cmdfiles:
    with open(cmdfile, mode='rb') as fr:
        content = fr.read().decode().split('\x00')
        if (len(content) >= 2) and (content[1] == 'controller-manager'):
            pid = os.path.basename(os.path.dirname(cmdfile))
            break
    return pid

pid = find_pid()
if pid == None:
    print("Error: controller PID not found")
    sys.exit(1)
print("Killing the controller process PID %s" % pid)
subprocess.run("sudo kill -KILL %s" % pid, shell=True)
