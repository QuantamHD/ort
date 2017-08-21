import click
import os
import shutil
import json
import uuid
import stat
from subprocess import check_call
from data.database import Database


@click.group()
def main():
    """
    Ort
    
    A tool that manages your MySQL database versions for you automatically based on git branches.

    Usage
    First initialize ort by calling ort init in any directory containg a .git folder.

    $ort init
    """
    pass

@main.command()
def init():
    """Initializes ort in the root of a git project."""
    init_impl()

@main.command()
@click.option('--ref', is_flag=True)
@click.argument('name')
def snapshot(ref, name):
    """makes a snapshot"""
    directory = get_ort_directory()
    database = get_database_from_config(directory)
    
    if ref:
        command = database.snapshot_command(os.path.join(directory, '.ort', 'ref_snapshots', name))
    else:
        command = database.snapshot_command(os.path.join(directory, '.ort', 'named_snapshots', name))
    click.echo('Taking a snapshot of the database')
    try:
        check_call(command, shell=True)
    except CalledProcessError:
        click.echo('Snapshot complete.')
        raise click.UsageError("There was an error trying to make a snapshot")
    
    click.echo('Snapshot Complete.')

@main.command()
@click.option('--ref', is_flag=True)
@click.argument('name')
def restore(ref, name):
    directory = get_ort_directory()
    database = get_database_from_config(directory)
    click.echo("Starting restore of database snapshot {}".format(name))
    if ref:
        snapshot = os.path.join(directory, '.ort', 'ref_snapshots', name)
        if os.path.isfile(snapshot):
            command = check_call(database.restore_command(snapshot), shell=True)
        else:
            raise click.UsageError("Could not find snap shot named {}".format(name))
    else:
        snapshot = os.path.join(directory, '.ort', 'named_snapshots', name)
        if os.path.isfile(snapshot):
            check_call(database.restore_command(snapshot), shell=True)
        else:
            raise click.UsageError("Could not find snap shot named {}".format(name))
    click.echo("Restored database snapshot {}".format(name))

    
def get_database_from_config(ort_parent_directory):
    config_file = os.path.join(ort_parent_directory, ".ort", "config")
    with open(config_file, 'r') as content_file:
        content = content_file.read()
    
    config_map = json.loads(content)
    return Database.build_from(config_map["database"])

def get_ort_directory():
    directory = walk_up_looking_for('.ort')
    if not directory:
        raise click.UsageError("There is no initialized ort project here.")

    return directory

def walk_up_looking_for(directory):
    current_directory = os.getcwd()
    while current_directory != os.path.dirname(current_directory):
        if os.path.isdir(os.path.join(current_directory, directory)):
            return current_directory
        current_directory = os.path.dirname(current_directory)

    return None

def init_impl():
    if not os.path.isdir('.git'):
        raise click.UsageError("You must initiate ort in the root folder of a git project.")
    
    if not os.path.isdir('.ort'):
        os.makedirs('.ort')
        os.makedirs('.ort/ref_snapshots')
        os.makedirs('.ort/named_snapshots')
    else:
        raise click.UsageError("ort is alread initialized, if this command ended in an error please remove the .ort folder. and run the command again.")
    click.echo("Created .ort configuration folder.")

    database_host     = click.prompt(text="Database Host", default="127.0.0.1", show_default=True)
    database_port     = click.prompt(text="Database Port", default="3306", show_default=True)
    database_user     = click.prompt(text="Database Username", default="root", show_default=True)
    database_schema   = click.prompt(text="Database Schema")
    database_password = click.prompt(text="Database Password", hide_input=True)

    config = {
        'version': '0.1.0',
        'database': {
            'database_host': database_host,
            'database_port': database_port,
            'database_user': database_user,
            'database_password': database_password,
            'database_schema': database_schema
        }
    }
    click.echo()
    create_config(config)
    init_scripts()


def create_config(config_map):
    filename = os.path.join(os.getcwd(),'.ort/config')
    config_file = open(filename, "a")
    config_json = json.dumps(config_map, sort_keys=True, indent=4, separators=(',', ': '))
    click.echo(message=config_json ,nl=False ,file=config_file)
    config_file.close()


def init_scripts():
    post_commit_exists   = os.path.isfile('.git/hooks/post-commit') 
    post_merge_exists    = os.path.isfile('.git/hooks/post-merge')
    post_checkout_exists = os.path.isfile('.git/hooks/post-checkout')

    modify_script = """
    ref=\"$(git rev-parse HEAD)\"
    ort snapshot --ref $ref
    """

    post_commit_script   = modify_script
    post_merge_script    = modify_script

    post_checkout_script = """
    oldRef=$(echo $1 | sed 's/,*$//g')
    newRef=$(echo $2 | sed 's/,*$//g')

    ort snapshot --ref $oldRef
    ort restore --ref $newRef
    """

    create_script(post_commit_script  , './.git/hooks/post-commit'  , post_commit_exists, "")
    create_script(post_merge_script   , './.git/hooks/post-merge'   , post_merge_exists, "$1")
    create_script(post_checkout_script, './.git/hooks/post-checkout', post_checkout_exists, "$1, $2, $3")


def create_script(script, script_path, script_exists, params):
    filename = os.path.basename(os.path.normpath(script_path))
    if script_exists and (not os.path.isfile(script_path + ".ort")):
        shutil.move(script_path, script_path + ".userscript")
        
        ort_script = open(script_path + ".ort", "a")
        click.echo(message="#!/bin/sh", file=ort_script)
        click.echo(message=script, file=ort_script)
        ort_script.close()

        main_script_content = "$GIT_DIR/hooks/{}.userscript {} && $GIT_DIR/hooks/{}.ort {}".format(filename, params, filename, params)
        main_script = open(script_path, "a")
        click.echo(message="#!/bin/sh", file=main_script)
        click.echo(message=main_script_content, file=main_script)
        main_script.close()

        make_file_executable(script_path)
        make_file_executable(script_path + ".ort")
        make_file_executable(script_path + ".userscript")

    elif script_exists and os.path.isfile(script_path + ".ort"):
        raise click.UsageError("Ort scripts already exist, post_commit, post_merge, post_rebase, and post_checkout")
    else:
        ort_script = open(script_path + ".ort", "a")
        click.echo(message="#!/bin/sh", file=ort_script)
        click.echo(message=script, file=ort_script)
        ort_script.close()

        main_script = "$GIT_DIR/hooks/{}.ort {}".format(filename, params)
        file = open(script_path, "a")
        click.echo(message="#!/bin/sh", file=file)
        click.echo(message=main_script, file=file)
        file.close()

        make_file_executable(script_path)
        make_file_executable(script_path + ".ort")


def make_file_executable(file_path):
    st = os.stat(file_path)
    os.chmod(file_path, st.st_mode | stat.S_IEXEC)
    
@main.command()
def reset():
    """Removes the current ort configuration files, AS WELL AS SNAPSHOTS and then runs the initiation again."""
    if os.path.isdir('.ort') and os.path.isdir('.git'):
        shutil.rmtree('.ort')
    else:
        raise click.UsageError("There is no ort configuration to reset here.")

    init_impl()


def print_help_msg(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))
