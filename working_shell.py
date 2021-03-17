import os
import subprocess
import fnmatch
import glob
import shlex
import subprocess
import signal
import getpass
import socket

jobs = []
USER = getpass.getuser()
HOME = os.getenv("HOME")
HOST = socket.gethostname()
def sh_cd(inp):
    try:
        args=shlex.split(inp)
        for i in range(len(args)):
            if args[i] == "cd":
                globber = glob.glob(args[i+1])
                sorted_options=sorted(globber)
                file=sorted_options[0]
                os.chdir(os.path.abspath(file))
        p = subprocess.Popen(inp, shell=True)
        p.wait()
    except Exception:
            print("cd: no such file or directory:")


def signal_handler(process):
    process.send_signal(signal.SIGINT)


def main():
    current_process = 0
    while True:
        try:
            dir = os.getcwd().replace(HOME, "~")
            inp = input(USER + "@" + HOST + ":" + dir + "$ ")
            if inp == "exit":
                break
            elif not inp:
                pass
            elif "sudo " in inp:
                print("hey wait no you can't do that")
            elif "cd " in inp:
                sh_cd(inp)
            elif "jobs" in inp:
                to_ret = ""
                rem = []
                for index, job in enumerate(jobs):
                    if job.poll() is None:
                        to_ret += "[" + str(index + 1) + "] Running     " + str(job.args + "&") + "\n"
                    else:
                        to_ret += "[" + str(index + 1) + "] Done     " + str(job.args + "&") + "\n"
                        rem.append(job)
                for job in rem:
                    jobs.remove(job)
                print(to_ret)
            elif "fg" in inp:
                check_jobs()
                id = inp[inp.index(" ") + 1:]
                found = False
                for job in jobs:
                    if int(id) == job.pid:
                        job.send_signal(signal.SIGSTOP)
                        p = subprocess.Popen(job.args, shell=True)
                        p.communicate()
                        found = True
                if not found:
                    print("That job doesn't exist")

            elif "bg" in inp:
                check_jobs()
                id = inp[inp.index(" ") + 1:]
                found = False
                for job in jobs:
                    if int(id) == job.pid:
                        job.send_signal(signal.SIGSTOP)
                        p = subprocess.Popen(job.args, shell=True)
                        found = True
                if not found:
                    print("That job doesn't exist")
            elif inp[-1] == "&":
                p = subprocess.Popen(inp[:-1], shell=True, start_new_session=True)
                jobs.append(p)
                print("[" + str(jobs.index(p) + 1) + "] " + str(p.pid))
            else:
                p = subprocess.Popen(inp, shell=True)
                current_process = p
                p.wait()
            reap()

        except KeyboardInterrupt:
            if current_process:
                signal_handler(current_process)
                current_process = 0
                print()
            else:
                print()

def reap():
    rem = []
    indices = []
    for index, job in enumerate(jobs):
        if job.poll() is None:
            pass
        else:
            rem.append(job)
            indices.append(index)
    for job in rem:
        jobs.remove(job)
    if rem:
        for index, i in enumerate(rem):
            print("[" + str(indices[index] + 1) + "] Done     " + str(i.args) + "&")

def check_jobs():
    rem = []
    for job in jobs:
        if job.poll() is None:
            pass
        else:
            rem.append(job)
    for job in rem:
        jobs.remove(job)
    return rem

if '__main__' == __name__:
    main()
