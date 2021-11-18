import click
import json

from calculate_routes import calculate_routes
from calculate_emissions import calculate_emissions, append_additional_emissions_to_lcpa
from rasterize_points import rasterize_points
import preprocess as preprocess
from multiprocessing import Pool
from itertools import repeat

@click.group()
@click.option('-p', '--preprocess', type=bool, default=False, help='If raw data needs to be preprocessed first')
@click.option('--parallel', '-l', type=int, help="Number of processes (int) when using multiprocessing parallel computing")
@click.pass_context
def cli(ctx, preprocess, parallel):
    ctx.ensure_object(dict)
    ctx.obj['PREPROCESS'] = preprocess
    ctx.obj['PARALLEL'] = parallel

@cli.command()
def reduce():
    with open("config.json") as file:
        config = json.load(file)

    datasets = ["vesselfinder", "helcom"]
    for d in datasets:
        preprocess.reduce(d, config)

@cli.command()
def merge():
    with open("config.json") as file:
        config = json.load(file)

    preprocess.merge(config)

@cli.command()
def routes():
    with open("config.json") as file:
        config = json.load(file)
    calculate_routes(config)

@cli.command()
def emissions():
    with open("config.json") as file:
        config = json.load(file)

    # create up-to-date model file
    append_additional_emissions_to_lcpa()

    calculate_emissions(config)

@cli.command()
@click.pass_context
def rasterize(ctx):
    with open("config.json") as file:
        config = json.load(file)
    # parallel
    if ctx.obj["PARALLEL"] > 0:
        pool = Pool(processes=ctx.obj["PARALLEL"])
        pool.starmap(
            rasterize_points,
            zip(repeat(config), [
                {"SOx [kg]": "SO2"},
                {"PM [kg]": "PM"},
                {"NOx [kg]": "NOx"},
                {"CO2 [kg]": "CO2"},
                {"BC [kg]": "EC"},
                {"ASH [kg]": "Ash"},
                {"POA [kg]": "POA"},
                {"CO [kg]": "CO"},
                {"NMVOC [kg]": "NMVOC"}]))

    else:
        rasterize_points(
            config=config,
            emission_types={
            "SOx [kg]": "SO2",
            "PM [kg]": "PM",
            "NOx [kg]": "NOx",
            "CO2 [kg]": "CO2",
            "BC [kg]": "EC",
            "ASH [kg]": "Ash",
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
