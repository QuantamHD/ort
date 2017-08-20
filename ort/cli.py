import click
import os
import shutil
import json


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
    init_impl()


def init_impl():
    """Initializes ort in the root of a git project."""
    if not os.path.isdir('.git'):
        raise click.UsageError("You must initiate ort in the root folder of a git project.")
    
    if not os.path.isdir('.ort'):
        os.makedirs('.ort')
    else:
        raise click.UsageError("ort is alread initialized, if this command ended in an error please remove the .ort folder. and run the command again.")
    click.echo("Created .ort configuration folder.")

    database_host     = click.prompt(text="Database Host", default="127.0.0.1", show_default=True)
    database_port     = click.prompt(text="Database Port", default="3306", show_default=True)
    database_user     = click.prompt(text="Database Username", default="root", show_default=True)
    database_password = click.prompt(text="Database Password", hide_input=True)
    database_schema   = click.prompt(text="Database Schema")


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

    filename = os.path.join(os.getcwd(),'.ort/config')
    config_file = open(filename, "a")
    config_json = json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '))
    click.echo(message=config_json ,nl=False ,file=config_file)
    config_file.close()







    
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
