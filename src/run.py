import click
import json

from calculate_routes import calculate_routes
from calculate_emissions import calculate_emissions
from rasterize_points import rasterize_points
from preprocess import reduce, merge


@click.group()
@click.option('-p', '--preprocess', type=bool, default=False, help='If raw data needs to be preprocessed first')
@click.pass_context
def cli(ctx, preprocess):
    ctx.ensure_object(dict)
    ctx.obj['PREPROCESS'] = preprocess

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
    rasterize_points(
        config=config,
        emission_types={
        "SOx [kg]": "SO2",
        "PM [kg]": "PM",
        "NOx [kg]": "NOx",
        "CO2 [kg]": "CO2",
        "BC [kg]": "BC",
        "ASH [kg]": "ASH",
        "POA [kg]": "POA",
        "CO [kg]": "CO",
        "NMVOC [kg]": "NMVOC",
    })

@cli.command()
@click.pass_context
def all(ctx):
    """
    """
    with open("config.json") as file:
        config = json.load(file)

    if ctx.obj['PREPROCESS']:
        datasets = ["vesselfinder", "helcom"]
        for d in datasets:
            reduce(d, config)

        merge(config)

    calculate_routes(config)

    calculate_emissions(config)

    rasterize_points(config=config)

if __name__ == "__main__":
    from logger import logger
    cli(obj={})
