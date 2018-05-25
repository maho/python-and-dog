from doit import get_var
from doit.tools import Interactive, run_once, title_with_actions, config_changed
from doit_api import cmdtask


SRCS = {"aconn.py": None,
        "blinker.py": None,
        "main.py": None,
        "config.py": None,
        "stdlib.py": None,
        "dispenser_client.py": None,
        "app.py": None,
        "config_local.py": None,
        '.micropython-lib/python-stdlib/logging/logging.py': 'lib/logging.py',
        '.usyslog/usyslog.py': 'lib/usyslog.py',
        'logging_handlers.py': None}

MPF_ADDR = get_var('MPF_ADDR', 'ttyUSB0')


REPOS = {'.micropython': get_var('MICROPYTHON_REPO', "git@github.com:micropython/micropython.git"),
         '.micropython-lib': get_var('MICROPYTHON_LIB_REPO', 'git@github.com:micropython/micropython-lib.git'),
         '.usyslog': get_var('USYSLOG_REPO', 'https://github.com/kfricke/micropython-usyslog')}


def local_micropython(cmd):
    return Interactive(f"micropython {cmd}", env={'MICROPYPATH': 'localstubs'})


def task_clone_external_repos():
    for dir_, repo in REPOS.items():
        yield {'name': f'clone_{dir_}',
               'title': title_with_actions,
               'actions': [f'git clone {repo} {dir_}'],
               'targets': [dir_],
               'uptodate': [run_once]
               }


def task_send_to_esp32():
    for src, dst in SRCS.items():
        if not dst:
            dst = src

        yield {'name': f"send_{src}",
               'actions': [
                        # f'mpfshell --loglevel=DEBUG --reset -n -o {MPF_ADDR}',
                        f'mpfshell --loglevel=DEBUG -c "put {src} {dst}" -n -o {MPF_ADDR}'
                    ],
               'file_dep': [src],
               'task_dep': ['clone_external_repos'],
               'uptodate': [True],
               'title': title_with_actions
               }


@cmdtask(uptodate=[False], task_dep=["send_to_esp32"])
def repl():
    return [
        # f'mpfshell --loglevel=DEBUG --reset -n -o {MPF_ADDR}',
        Interactive(f"mpfshell -c repl -o {MPF_ADDR}")
    ]


@cmdtask(uptodate=[False], task_dep=["send_to_esp32"])
def minicom():
    return [Interactive("minicom -D /dev/ttyUSB0")]


LOCAL_PIP_CMDS = [
        "ln -sf ../.micropython-lib/python-stdlib/unittest/unittest.py localstubs/unittest.py",
        "ln -sf ../.micropython-lib/python-stdlib/logging/logging.py localstubs/logging.py",
        "ln -sf ../.micropython-lib/python-ecosys/urequests/urequests.py localstubs/urequests.py",
        "ln -sf ../.micropython/extmod/uasyncio localstubs/uasyncio",
        "ln -sf ../.usyslog/usyslog.py localstubs/usyslog.py",
        # local_micropython("-m upip install micropython-usyslog"),
    ]


@cmdtask(uptodate=[run_once, config_changed(str(LOCAL_PIP_CMDS))], file_dep=['.usyslog'])
def local_pip():
    return LOCAL_PIP_CMDS


@cmdtask(uptodate=[False], task_dep=['local_pip'])
def local_run():
    return [
        local_micropython("main.py")
    ]
