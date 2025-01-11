import glob
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from doit import get_var
from doit.action import CmdAction
from doit.tools import Interactive, timeout, result_dep
from doit_api import cmdtask


DOIT_CONFIG = {"default_tasks": ["install"], "verbosity": 2}

WEBREPL_ADDR = get_var("WEBREPL_ADDR", "192.168.1.38")
WEBREPL_PASSWORD = get_var("WEBREPL_PASSWORD", "foobar")

# MPF_ADDR = get_var('MPF_ADDR', f"ws:{WEBREPL_ADDR},{WEBREPL_PASSWORD}")
MPF_ADDR = "ttyUSB0"
MPFSHELLi = f"mpfshell -o {MPF_ADDR} --loglevel=DEBUG"
MPFSHELL = f"{MPFSHELLi} -n"

SRCS = [
    "main.py",
    "servo.py",
    "config.py",
    "config_local.py",
    "conn.py",
    "template.py",
    "webrepl_cfg.py",
]
UPIPS = ["micropython-logging"]
UPIPS_TESTS = []

MICROPYTHON_LIB_REPO = get_var(
    "MICROPYTHON_LIB_REPO", "git@github.com:micropython/micropython-lib.git"
)


@dataclass
class MPFTransaction:
    """transaction to be executed on mpfshell"""

    actions: List[str]

    def commit_to_mpfshell(self):
        """send all commands to mpfshell in one script, then remove appropriate
        .dirty files, then clean actions
        """

        input_ = b"\n".join([action.encode() for action in self.actions])

        print(b"SCRIPT:\n" + input_)

        ret = subprocess.run(
            f"{MPFSHELLi} -s /dev/stdin",
            input=input_,
            shell=True,
            check=True,
            capture_output=True,
        )

        print(f"STDOUT: {ret.stdout}")
        print(f"STDERR: {ret.stderr}")

        # empty actions
        self.actions = []

        # remove all .*.dirty files/markers
        for dirty in glob.glob(".[a-z]*.dirty"):
            os.remove(dirty)


transaction = MPFTransaction([])


def show_cmd(task):
    return f"executing... {task.actions}"


def local_micropython(cmd):
    # return CmdAction(cmd, env={'MICROPATH': 'upy-local-lib'})
    return CmdAction(f"micropython {cmd}", env={"MICROPYPATH": "upy-local-lib"})


@cmdtask(uptodate=[timeout(timedelta(days=1))], targets=["lib/microdot.py"])
def checkout_microdot():
    """checkout microdot from github (it has problems with it's pypi package"""
    return [
        "rm -rfv .microdot",
        "git clone https://github.com/miguelgrinberg/microdot .microdot",
        "install -v -D .microdot/src/microdot/microdot.py lib/microdot.py",
    ]


def task_send_pyfiles():
    """send files to ESP"""

    def send_file(src, task_name):
        send_command_to_mpfshell(f"put {src} {src}", task_name)

    for src in SRCS:
        task_name = f"send_{src}"
        yield {
            "name": task_name,
            # "basename": f"send_{src}",
            "actions": [(send_file, [src, task_name])],
            "task_dep": ["mkdir_lib"],
            "file_dep": [src],
            "uptodate": [uptodate_task_not_dirty(task_name)],
        }


def send_command_to_mpfshell(command, task_name):
    transaction.actions.append(command)
    # create file `.send_{src}.dirty` to mark that file has to be sent
    # and if something fails with commiting the transaction - that this action needs
    # to be repeated
    open(f".{task_name}.dirty", "w").close()


def uptodate_task_not_dirty(task_name):
    """check if file is dirty and if yes - then return that it's not uptodate"""
    return not os.path.exists(f".{task_name}.dirty")


def task_pips():
    """install pip on remote side"""

    # for each entry in UPIPS invoke invoke_upip
    for pkg in UPIPS:
        yield {
            "name": f"pip_{pkg}",
            "basename": f"pip_{pkg}",
            "actions": [
                CmdAction(
                    # && date is because result_dep checks output of the command if is
                    # different than before
                    f"pipkin -d lib install {pkg} && date",
                    shell=True,
                )
            ],
            "uptodate": [timeout(timedelta(days=1))],
        }

    # use mpfshell mput to send all files from lib to remote
    yield {
        "name": "copy lib to upy",
        "actions": [
            (
                send_command_to_mpfshell,
                ("lcd lib\ncd lib\nmput .*\\.py", "copy_lib_to_upy"),
            )
        ],
        "task_dep": ["checkout_microdot"],
        "uptodate": (
            [
                timeout(timedelta(days=1)),
                uptodate_task_not_dirty("copy_lib_to_upy"),
            ]
            + [result_dep(f"pip_{pkg}") for pkg in UPIPS]
        ),
    }


def task_commit():
    """commit MPF shell commands"""
    return {
        "actions": [transaction.commit_to_mpfshell],
        "task_dep": ["pips", "send_pyfiles"],
    }


def task_install():
    """grouping task for running dependencies: pips and copy files"""
    return {
        "actions": [],
        "task_dep": ["commit"],
    }


def task_reset():
    def _reset():
        if MPF_ADDR.startswith("ttyUSB"):
            subprocess.run(f"{MPFSHELL} --reset", shell=True)
            return

        cmd = f"{MPFSHELL} -c 'exec import machine;exec machine.reset()'"

        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and before  exec() to run the shell.
        pro = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid
        )
        time.sleep(5)
        os.killpg(os.getpgid(pro.pid), signal.SIGTERM)

    return {"title": show_cmd, "actions": [_reset]}


def task_repl():
    return {
        "title": show_cmd,
        "actions": [lambda: time.sleep(5), Interactive(f"{MPFSHELLi} -c repl")],
    }


def task_mpfshell():
    return {"title": show_cmd, "actions": [Interactive(f"{MPFSHELLi}")]}


def task_wipe():
    return {"title": show_cmd, "actions": [f'{MPFSHELL} -c "mrm .*"']}


def task_local_microdot():
    """copy microdot to local lib directory,"""
    return {
        "actions": [
            "mkdir -p upy-local-lib",
            "cp -v lib/microdot.py upy-local-lib/microdot.py",
        ],
        "file_dep": ["lib/microdot.py"],
        "targets": ["upy-local-lib/microdot.py"],
    }


def task_mkdir_lib():
    """create lib directory on remote esp"""
    return {
        "actions": [
            (send_command_to_mpfshell, ("md lib", "mkdir_lib")),
        ],
        "uptodate": [uptodate_task_not_dirty("mkdir_lib")],
    }


def task_local_upip():
    """install via upip required packages"""
    upips = " ".join(UPIPS)
    return {
        "actions": [local_micropython(f"-m mip install {upips}")],
        "task_dep": [
            "local_microdot",
        ],
        "uptodate": [timeout(timedelta(days=1))],
    }


def task_checkout_micropythonlib():
    """checkout micropython-lib from github"""
    return {
        "title": show_cmd,
        "actions": [f"git clone {MICROPYTHON_LIB_REPO} .micropython-lib"],
        "targets": [".micropython-lib"],
        "uptodate": [True],
    }


def task_local_upylib_links():
    """make links between .micropython-lib and upy-local-lib"""
    return {
        "actions": [
            "ln -sf ../.micropython-lib/python-stdlib/unittest/unittest.py "
            "upy-local-lib/unittest.py"
        ],
        "targets": ["upy-local-lib/unittest.py"],
        "task_dep": ["checkout_micropythonlib"],
        "uptodate": [True],
    }


LOCAL_STUBS = ["common.py", "webrepl.py", "machine.py", "network.py"]


def task_local_stubs():
    """install stubs for modules like webrepl"""
    for stub in LOCAL_STUBS:
        yield {
            "basename": f"local_stubs:{stub}",
            "actions": [f"cp -v localstubs/{stub} upy-local-lib/{stub}"],
            "targets": [f"upy-local-lib/{stub}"],
            "file_dep": [f"localstubs/{stub}"],
        }


def task_local_run():
    """run sources in prepared local micropython"""
    return {
        "actions": [local_micropython("main.py")],
        "task_dep": ["local_upip", "local_stubs:*"],
        "uptodate": [False],  # execute it every time
    }


def task_tests():
    """run tests in tox"""
    return {
        "actions": ["tox"],
        "task_dep": ["local_upip", "local_upylib_links", "local_stubs:*"],
        "uptodate": [False],
    }
