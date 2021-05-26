import click
import json

from calculate_routes import calculate_routes
from calculate_emissions import calculate_emissions
from preprocess import reduce, merge


@click.group()
def cli():
    pass

@cli.command()
def preprocess():
    with open("config.json") as file:
        config = json.load(file)

    datasets = ["vesselfinder", "helcom"]
    for d in datasets:
        reduce(d, config)

    merge(config)

@cli.command()
def routes():
    with open("config.json") as file:
        config = json.load(file)
    calculate_routes(config)

@cli.command()
def emissions():
    with open("config.json") as file:
        config = json.load(file)
    calculate_emissions(config)

@cli.command()
def rasterize():
    with open("config.json") as file:
        config = json.load(file)
    pass

@cli.command()
@click.option(
    '--preprocess',
    default=False, help='If raw data needs to be preprocessed first')
def all(preprocess):
    """
    """
    with open("config.json") as file:
        config = json.load(file)

    if preprocess:
        datasets = ["vesselfinder", "helcom"]
        for d in datasets:
            reduce(d, config)

        merge(config)

    calculate_routes(config)

    calculate_emissions(config)


if __name__ == "__main__":
    from logger import logger
    cli()
