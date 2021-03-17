import os              # used for general interactions with the operating system
import subprocess      # used for creating subprocesses in the shell
import fnmatch         # not used???
import glob            # used to handle glob notation
import shlex           # used to split input in the shell
import signal          # used for sending signals to subprocesses
import getpass         # used *exclusively* to get the current user's name
import socket          # used *exclusively* to get the current hostname

"""
Linux Shell in Python
Contributors: Andrew Tung, Katherine Tung, Joshua Lowe
March 16, 2021
"""

jobs = []
USER = getpass.getuser()    # gets the username
HOME = os.getenv("HOME")    # gets the home directory
HOST = socket.gethostname() # gets the hostname

# changes directory
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

# sends the interrupt signal to a target process
def signal_handler(process):
    process.send_signal(signal.SIGINT)

# loops infinitely until exit command, executing commands
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
            elif "sudo " in inp:  # we don't like troll cases or security holes
                print("hey wait no you can't do that")
            elif "cd " in inp:
                sh_cd(inp)
            # if builtin jobs called, loops through jobs and checks all of them
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

            elif "fg" in inp: # restarts a background job in the foreground
                check_jobs()
                id = inp[inp.index(" ") + 1:]
                found = False
                for job in jobs:
                    if int(id) == job.pid:
                        job.send_signal(signal.SIGSTOP)
                        p = subprocess.Popen(job.args, shell=True)
                        p.wait()
                        found = True
                if not found:
                    print("That job doesn't exist")

            elif "bg" in inp: # restarts a background job
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

            elif inp[-1] == "&": # starts a process in the background
                p = subprocess.Popen(inp[:-1], shell=True, start_new_session=True)
                jobs.append(p)
                print("[" + str(jobs.index(p) + 1) + "] " + str(p.pid))

            else: # starts a process
                p = subprocess.Popen(inp, shell=True)
                current_process = p
                p.wait()
            reap()

        # intercepts ctrl-c command and stops process rather than python shell
        except KeyboardInterrupt:
            if current_process:
                signal_handler(current_process)
                current_process = 0
                print()
            else:
                print()

# reaps dead children at end of execution loop
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

# checks jobs to see whether done or running
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
