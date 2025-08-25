import click


@click.group(help="commands to help find and manipulate hosts")
def cli():
    pass


@click.command(help="find a specific host")
def find():
    click.echo("find a host")


cli.add_command(find)
