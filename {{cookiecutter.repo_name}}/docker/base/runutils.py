# coding: utf-8
# Core and 3th party packages
import os
import sys
import subprocess
import signal
import pwd
import click
import time
import traceback


def getvar(name, default=None, required=True):
    """
    Returns the value of an environment variable. If the variable is not
    present, default will be used. If required is True, only not None values
    will be returned, and it will raise an exception instead of returning None.
    """
    ret = os.environ.get(name, default)
    if required and ret is None:
        raise Exception('Environment variable %s is not set' % name)
    return ret


def ensure_dir(dir, owner=None, group=None, permsission_str='777'):
    """Checks the existence of the given dir and creates it if not present."""
    if not os.path.isdir(dir):
        os.makedirs(dir)

    if owner:
        subprocess.call(['chown', owner, dir])
    if group:
        subprocess.call(['chgrp', group, dir])
    if permsission_str:
        subprocess.call(['chmod', permsission_str, dir])


def run_cmd(args, message=None, input=None, user=None):
    """
    Executes a one-off command. The message will be printed on terminal.
    If input is given, it will be passed to the subprocess.
    """
    if message:
        click.echo(message + ' start ... ')

    _setuser = setuser(user) if user else None

    if input is None:
        try:
            subprocess.check_output(
                args, stderr=subprocess.STDOUT, preexec_fn=_setuser)
        except subprocess.CalledProcessError as e:
            if message:
                click.secho(message + ' finish ✘', fg='red')
            traceback.print_exc(e)
            raise Exception(e)
        else:
            if message:
                click.secho(message + ' finish ✔', fg='green')
    else:
        sp = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_setuser)
        out, err = sp.communicate(input)
        retcode = sp.wait()

        if retcode:
            if message:
                click.secho(message + ' finish ✘', fg='red')
            traceback.print_exc(err)
            raise Exception(err)
        else:
            if message:
                click.secho(message + ' finish ✔', fg='green')


def run_daemon(params, stdout=None, stderr=None, signal_to_send=signal.SIGTERM,
               waitfunc=None, user=None, semafor=None, initfunc=None):
    """
    Runs the command as the given user (or the caller by default) in daemon
    modeand exits with it's returncode. Connects the given stdout, sends the
    specified signal to exit. If waitfunc is given it must accept an object
    and it should return as soon as possible if object.stopped evaluates to
    True. If semafor is provided it should be a path to a file. Before exit,
    this file should be deleted.
    """
    class Stopper(object):
        def __init__(self):
            self.stopped = False

    class SubprocessWrapper(object):
        def __init__(self):
            self.subprocess = None

    subprocess_wrapper = SubprocessWrapper()
    stopper = Stopper()

    def cleanup(signum, frame):
        if subprocess_wrapper.subprocess:
            subprocess_wrapper.subprocess.send_signal(signal_to_send)
        stopper.stopped = True

    signal.signal(signal.SIGTERM, cleanup)

    if waitfunc:
        waitfunc(stopper)

    if initfunc:
        initfunc(stopper)

    _setuser = setuser(user) if user else None
    if not stopper.stopped:
        sp = subprocess.Popen(
            params, stdout=stdout, stderr=stderr, preexec_fn=_setuser)
        subprocess_wrapper.subprocess = sp

        if semafor:
            open(semafor, 'w').close()

        waitresult = sp.wait()
    else:
        waitresult = 0

    try:
        os.remove(semafor)
    except:
        pass

    sys.exit(waitresult)


def setuser(username):
    """
    Returns a function that sets process uid, gid according to the given
    username. If the user does not exist, it raises an error.
    """
    uid, gid, home = id(username)
    groups = list(set(os.getgrouplist(username, gid)))

    def chuser():
        os.setgroups(groups)
        os.setgid(gid)
        os.setuid(uid)
        os.environ['HOME'] = home
    return chuser


def id(username):
    """Returns uid, gid, home directory for the given username."""
    userinfo = pwd.getpwnam(username)
    return userinfo.pw_uid, userinfo.pw_gid, userinfo.pw_dir


def runbash(user):
    subprocess.call(['bash'], preexec_fn=setuser(user))


def sleep():
    class Stopper(object):
        def __init__(self):
            self.stopped = False

    stopper = Stopper()

    def stop_sleep(signum, frame):
        stopper.stopped = True

    signal.signal(signal.SIGTERM, stop_sleep)
    while not stopper.stopped:
        time.sleep(1)
