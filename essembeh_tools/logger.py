import logging
from argparse import ArgumentParser

from essembeh_tools.utils import parser_group

from . import __name__ as app

logger = logging.getLogger(app)

logging.basicConfig(format="%(message)s", level=logging.DEBUG)


DEBUG = logger.debug
INFO = logger.info
WARNING = logger.warning


def add_verbose_quiet(parser: ArgumentParser):
    with parser_group(parser, exclusive=True) as group:
        group.add_argument(
            "-q", "--quiet", action="store_true", help="print less details"
        )
        group.add_argument(
            "-v", "--verbose", action="store_true", help="print more details"
        )
