#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import posixpath
import sys
import time

from functools import wraps
from importlib import import_module

import click

class CLISession(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.controller = None

pass_session = click.make_pass_decorator(CLISession)


@click.group(chain=True)
@click.option(
    "--project-home",
    envvar="PROJECT_HOME",
    default=".",
    metavar="PATH",
    help="Changes the project folder location.",
)
@click.option(
    "--config",
    nargs=2,
    multiple=True,
    metavar="KEY VALUE",
    help="Overrides a config key/value pair.",
)
@click.option(
    "--keep", "-k", is_flag=True,
    help="Keep local runtime, do not kill it after executing commands.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.option(
    "--buildpath", "-b", help="Where to store files created during build."
)
@click.option(
    "--uri", "-u", help="URI to reach remote PLC."
)
@click.version_option("0.1")
@click.pass_context
def cli(ctx, **kwargs):
    """Beremiz CLI manipulates beremiz projects and runtimes. """

    ctx.obj = CLISession(**kwargs)

def ensure_controller(func):
    @wraps(func)
    def func_wrapper(session, *args, **kwargs):
        if session.controller is None:
            session.controller = import_module("CLIController").CLIController(session)
        ret = func(session, *args, **kwargs)
        return ret

    return func_wrapper

@cli.command()
@click.option(
    "--target", "-t", help="Target system triplet."
)
@pass_session
@ensure_controller
def build(session, target):
    """Builds project. """
    def processor():
        return session.controller.build_project(target)
    return processor

@cli.command()
@pass_session
@ensure_controller
def transfer(session):
    """Transfer program to PLC runtim."""
    def processor():
        return session.controller.transfer_project()
    return processor

@cli.command()
@pass_session
@ensure_controller
def run(session):
    """Run program already present in PLC. """
    def processor():
        return session.controller.run_project()
    return processor

@cli.command()
@pass_session
@ensure_controller
def stop(session):
    """Stop program running in PLC. """
    def processor():
        return session.controller.stop_project()
    return processor


@cli.result_callback()
@pass_session
def process_pipeline(session, processors, **kwargs):
    ret = 0
    for processor in processors:
        ret = processor()
        if ret != 0:
            if len(processors) > 1 :
                click.echo("Command sequence aborted")
            break

    if session.keep:
        click.echo("Press Ctrl+C to quit")
        try:
            while True:
                session.controller.UpdateMethodsFromPLCStatus()
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

    session.controller.finish()

    return ret

if __name__ == '__main__':
    cli()

