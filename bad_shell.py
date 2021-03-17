import os
import subprocess
import fnmatch
import glob
import shlex
import subprocess
import signal
import getpass
from io import BytesIO
import io
import socket

BUILTINS = {"pwd", "jobs", "bg", "fg"}
USER = getpass.getuser()
HOME = os.getenv("HOME")
HOST = socket.gethostname()
jobs = []
def sh_cd(inp):
    try:
        args=shlex.split(inp)
        for i in range(len(args)):
            if args[i] == "cd":
                globber = glob.glob(args[i+1])
                sorted_optns=sorted(globber)
                file=sorted_optns[0]
                os.chdir(os.path.abspath(file))
        p = subprocess.Popen(inp, shell=True)
        p.wait()
    except Exception:
            print("cd: no such file or directory:")


def signal_handler(sig, frame):
    try:
        # this might not work
        pid = os.getpid()
        os.kill(pid, signal.SIGINT)
    except:
        pass

def main():
    jobs = {}
    while True:
        # for counter, popen in enumerate(jobs):
        #     if popen.poll() is not None:
        #         print("Running         " + str(popen.pid) + "         " + str(popen.args))
        signal.signal(signal.SIGINT, signal_handler)
        dir = os.getcwd().replace(HOME, "~")
        inp = input(USER + "@" + HOST + ":" + dir + "$ ")
        if inp == "exit":
            break
        elif not inp:
            pass
        elif "cd " in inp:
            sh_cd(inp)
        # elif inp[-1] == "&":
        #     p = subprocess.Popen(inp, shell=True)
        #     jobs[p] = p.pid
        else:
            # jobs +=
            execute(inp)

def execute(inp):
    try:
        # lex = shlex.shlex(inp, punctuatn_chars=False)
        # sub_args = list(lex)
        # print(sub_args)
        sub_args = custom_split(inp)
        pass
    except Exceptn:
        print("Invalid input")
        return
    if sub_args[-1] == "&":
        out = execute_internal(sub_args[:-1], None, background=True)
    else:
        out = execute_internal(sub_args, None)
        if out:
            print(out.read().decode("utf-8").strip())

def execute_internal(sub_args, last_stdout, background=False):
    print(sub_args)
    rewrite = sub_args[:]
    for index, val in enumerate(sub_args):
        if val == "$":
            left = index + 1
            right = left + get_match_index(sub_args[left:])
            output = execute_internal(sub_args[left + 1: right], None, background)
            rewrite[index] = output.read().decode("utf-8").strip()
            for i in range(left, right + 1):
                rewrite[i] = None
            rewrite = list(filter(None, rewrite))
            return execute_internal(rewrite, last_stdout, background)
        elif val == "|":
            out = execute_internal(sub_args[0:index], last_stdout, background)
            return execute_internal(sub_args[index + 1:], out, background)
        elif val == ">":
            out = execute_internal(sub_args[0:index], last_stdout, background)
            out = out.read().decode("utf-8").strip()
            filename = execute_internal(sub_args[index + 1:], None, background)
            f = open(filename, "w+")
            f.write(out)
            f.close()
            return
        elif val == "<":
            filename = execute_internal(sub_args[index + 1:], None, background)
            f = open(filename, "r")
            inp = f.read()
            return execute_internal(sub_args[0:index], inp, background)
    if "$" not in sub_args and "|" not in sub_args and ">" not in sub_args and "<" not in sub_args:
        if sub_args[0] in BUILTINS:
            print('running builtin')
            x = builtin(sub_args)
            if x:
                 x = x.encode('utf-8')
                 buf_read = io.BufferedReader(io.BytesIO(x))
                 return buf_read
            else:
                return
        if len(sub_args) == 1:
            if os.path.exists(sub_args[0]):
                return sub_args[0]
        # copy = sub_args[:]
        # for index, val in enumerate(sub_args):
        #     if val == "-":
        #         copy[index] = val + sub_args[index + 1]
        #         copy[index + 1] = None
        # copy = list(filter(None, copy))
        try:
            ps = subprocess.Popen(sub_args, stdin=last_stdout, stdout=subprocess.PIPE, close_fds=background)
            print(background)
            if not background:
                ps.wait()
            else:
                jobs.append(ps)
            return ps.stdout
        except:
            return
        # print(ps.stdout.read().decode("utf-8").strip())
        # print(ps.stdout.read())


def get_match_index(list):
    count = 0
    for index, val in enumerate(list):
        if val == "(":
            count += 1
        elif val == ")":
            count -= 1
        if count == 0:
            return index

def custom_split(input):
    last = 0
    copy = []
    next = ""
    for index, val in enumerate(input):
        if val in "&(){}[]$<>| ":
            copy.append(next)
            copy.append(val)
            next = ""
        else:
            next += val
    copy.append(next)
    copy = list(filter(None, copy))
    copy = list(filter(lambda x: x != " ", copy))
    print(copy)
    return copy

def builtin(args):
    if "pwd" in args:
        return os.getcwd()

    elif "jobs" in args:
        to_ret = ""
        rem = []
        for job in jobs:
            if job.poll() is None:
                to_ret += "Running: " + str(job.pid) + "   " + str(shlex.join(job.args) + " &") + "\n"
            else:
                to_ret += "Done: " + str(job.pid) + "   " + str(shlex.join(job.args) + " &") + "\n"
                rem.append(job)
        for job in rem:
            jobs.remove(job)
        return to_ret

    elif "fg" in args:
        builtin("jobs")
        id = args[1]
        for job in jobs:
            if int(id) == job.pid:
                job.send_signal(signal.SIGSTOP)
                return execute_internal(job.args, None).read().decode("utf-8").strip()
        return "That job doesn't exist"

    elif "bg" in args:
        builtin("jobs")
        id = args[1]
        for job in jobs:
            if int(id) == job.pid:
                job.send_signal(signal.SIGSTOP)
                return execute_internal(job.args, None, background=True).read().decode("utf-8").strip()
        return "That job doesn't exist"
    else:
        print("something went wrong, not a builtin")


if '__main__' == __name__:
    main()
