import logging
import click
import click_log

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


@click.command()
@click_log.simple_verbosity_option(logger)
@click.option('--termlist', type=click.Path(exists=True), required=True, help="headerless list of term ids")
@click.option('--sco_table', type=click.Path(exists=True), required=True, help="subclass table from sparql/sco.sparql")
def hident(termlist, sco_file):
    logger.info(termlist)
    logger.info(sco_file)


def set_to_sorted_list(term_set: set[str]) -> list[str]:
    listified = list(term_set)
    listified.sort()
    return listified


if __name__ == "__main__":
    hident()
