import os
import signal
import subprocess
import time
from datetime import timedelta
from typing import Set

import doit.globals
from doit import get_var
from doit.action import CmdAction
from doit.tools import Interactive, run_once, timeout
from doit_api import task, pytask, cmdtask


DOIT_CONFIG = {"default_tasks": ["send_pyfiles", "pips"], "verbosity": 2}

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
    "lib/microdot.py",
]
UPIPS = ["micropython-logging"]
UPIPS_TESTS = []

MICROPYTHON_LIB_REPO = get_var(
    "MICROPYTHON_LIB_REPO", "git@github.com:micropython/micropython-lib.git"
)


def show_cmd(task):
    return f"executing... {task.actions}"


class actions_to_send:
    before: Set[str] = set()
    middle: Set[str] = set()
    after: Set[str] = set()
    task_names: Set[str] = set()

    @classmethod
    def add_file(cls, f):
        dirname = os.path.dirname(f)
        if dirname and dirname != "lib":
            cls.before.add(f"md {dirname}")
        cls.middle.add(f"put {f} {f}")
        cls.task_names.add(f"send_{f}")

    @classmethod
    def upip(cls, pkgs):
        cls.before.add("exec import upip")
        cls.middle.add(f"exec upip.install({pkgs!r})")
        cls.task_names.add("pips")

    @classmethod
    def actions(cls):
        return list(cls.before) + list(cls.middle) + list(cls.after)


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

    def send_file(src):
        subprocess.run(f"{MPFSHELL} -c 'put {src} {src}'", shell=True, check=True)

    for src in SRCS:
        yield {
            "name": f"send_{src}",
            # "basename": f"send_{src}",
            "actions": [(send_file, [src])],
            "file_dep": [src],
        }


def task_pips():
    """install pip on remote side"""

    # for each entry in UPIPS invoke invoke_upip
    for pkg in UPIPS:
        yield {
            "name": f"pip_{pkg}",
            # "basename": f"pip_{pkg}",
            # "actions": [(invoke_upip, [pkg])],
            "actions": [
                CmdAction(
                    f"{MPFSHELL} -c 'exec import mip;exec mip.install(\"{pkg}\");' | tee /tmp/pip_{pkg}.log "
                    f"&& ! grep -q 'Error:' /tmp/pip_{pkg}.log",
                    shell=True,
                )
            ],
            # "uptodate": [run_once],
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


def task_local_upip():
    """install via upip required packages"""
    upips = " ".join(UPIPS)
    return {
        "actions": [local_micropython(f"-m mip install {upips}")],
        "task_dep": ["local_microdot"],
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
            "ln -sf ../.micropython-lib/python-stdlib/unittest/unittest.py upy-local-lib/unittest.py"
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


def run_shell_cmd(cmd):
    """run shell cmd, log runned command and return it's output. Simply wrapper around subprocess.run"""
