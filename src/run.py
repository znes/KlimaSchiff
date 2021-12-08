import click
import json
import os

from multiprocessing import Pool
from itertools import repeat

from calculate_routes import calculate_routes
from calculate_emissions import calculate_emissions
from rasterize_points import rasterize_points
import preprocess as preprocess


@click.group()
@click.option(
    "-p",
    "--preprocess",
    type=bool,
    default=False,
    help="If raw data needs to be preprocessed first",
)
@click.option(
    "--parallel",
    "-l",
    type=int,
    help="Number of processes (int) when using multiprocessing parallel computing",
)
@click.pass_context
def cli(ctx, preprocess, parallel):
    ctx.ensure_object(dict)
    ctx.obj["PREPROCESS"] = preprocess
    ctx.obj["PARALLEL"] = parallel


@cli.command()
def reduce_ais():
    with open("config.json") as file:
        config = json.load(file)

    datasets = ["vesselfinder", "helcom"]
    for d in datasets:
        preprocess.reduce_ais_data(d, config)


@cli.command()
def merge_ais():
    with open("config.json") as file:
        config = json.load(file)

    preprocess.merge_ais_data(config)


# helper to be used in different commands...
def _build_emission_model(config):

    model_data_path = os.path.join(
        os.path.expanduser("~"),
        config["model_data"])

    if not os.path.exists(model_data_path):
        os.path.makedirs(model_data_path)

    preprocess.merge_lcpa_models(
        config=config)

    preprocess.append_additional_emissions_to_lcpa(
        scenario=config["scenario"],
        output_dir=os.path.join(os.path.expanduser("~"), config["model_data"]),
        config=config
    )

    preprocess.build_imo_lists(config)


@cli.command()
def build_emission_model():
    with open("config.json") as file:
        config = json.load(file)

    _build_emission_model(config)


@cli.command()
def calc_routes():
    with open("config.json") as file:
        config = json.load(file)
    calculate_routes(config)


@cli.command()
@click.pass_context
def calc_emissions(ctx):
    with open("config.json") as file:
        config = json.load(file)

    # create up-to-date model file
    _build_emission_model(config)

    calculate_emissions(config, columns="all")


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
            zip(
                repeat(config),
                [
                    {"SOx [kg]": "SO2"},
                    {"PM [kg]": "PM"},
                    {"NOx [kg]": "NOx"},
                    {"CO2 [kg]": "CO2"},
                    {"BC [kg]": "EC"},
                    {"ASH [kg]": "Ash"},
                    {"POA [kg]": "POA"},
                    {"CO [kg]": "CO"},
                    {"NMVOC [kg]": "NMVOC"},
                ],
            ),
        )

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
            },
        )


@cli.command()
@click.pass_context
def all(ctx):
    """
    """
    with open("config.json") as file:
        config = json.load(file)

    if ctx.obj["PREPROCESS"]:
        datasets = ["vesselfinder", "helcom"]
        for d in datasets:
            reduce_ais(d, config)

        merge_ais(config)

    calculate_routes(config)

    calculate_emissions(config)

    rasterize_points(config=config)


if __name__ == "__main__":
    from logger import logger
    cli(obj={})
