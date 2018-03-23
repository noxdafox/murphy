import logging
import argparse
from pathlib import Path

from murphy.journal import Journal
from murphy.agents import application, installer, internet
from murphy.win_libvirt import state_interpreter, libvirt_cleanup


def main():
    arguments = parse_arguments()
    journal = Journal(Path(arguments.journal))

    setup_logging(arguments.debug and 10 or 20)

    interpreter = state_interpreter(
        arguments.device, scraper_port=arguments.scraper_port)

    if arguments.agent == 'installer':
        agent = installer.ApplicationInstaller(
            interpreter, journal, max_depth=arguments.max_depth,
            frequency=arguments.state_frequency)

        logging.info("Installing the application under focus.")
    if arguments.agent == 'explorer':
        agent = application.ApplicationExplorer(
            interpreter, journal, max_depth=arguments.max_depth,
            frequency=arguments.state_frequency)

        logging.info("Exploring the application under focus.")
    elif arguments.agent == 'internet':
        agent = internet.InternetExplorer(
            interpreter, journal, max_depth=arguments.max_depth,
            frequency=arguments.state_frequency)

        logging.info("Exploring \"The Internet®\".")
    else:
        logging.error("Unknown agent: %s", arguments.agent)

    try:
        agent.explore(arguments.timeout)
    except Exception as error:
        logging.exception(error)
    finally:
        logging.info("Restoring device state to intial one.")
        journal.initial_node.state.restore()
        logging.info("Cleaning up snapshots.")
        libvirt_cleanup(arguments.device)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Example MrMurphy Agent/Crawler implementation.')
    parser.add_argument('device', type=str, help='Libvirt domain UUID')
    parser.add_argument(
        '-j', '--journal', type=str, default='journal',
        help='Path where to store the journal and its rendered form')
    parser.add_argument(
        '-s', '--scraper-port', type=int, default=8000,
        help='GUI scraper service port')
    parser.add_argument(
        '-t', '--timeout', type=int, default=600,
        help='How long to execute the agent')
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, help='debug log')

    subparsers = parser.add_subparsers(
        dest='agent', title='agents', description='agent to use')

    # Internet Explorer
    internet_parser = subparsers.add_parser(
        'internet', help='Explore the content of "The Internet®".')
    internet_parser.add_argument(
        '-m', '--max-depth', type=int, default=internet.MAX_DEPTH,
        help='How many links to follow')
    internet_parser.add_argument(
        '-f', '--state-frequency', type=int, default=internet.FREQUENCY,
        help='How frequently checking the current state')

    # Application Installer
    installer_parser = subparsers.add_parser(
        'installer', help='Install a generic application.')
    installer_parser.add_argument(
        '-m', '--max-depth', type=int, default=internet.MAX_DEPTH,
        help='How many buttons to click')
    installer_parser.add_argument(
        '-f', '--state-frequency', type=int, default=internet.FREQUENCY,
        help='How frequently checking the current state')

    # Application Explorer
    installer_parser = subparsers.add_parser(
        'explorer', help='Explore a generic application.')
    installer_parser.add_argument(
        '-m', '--max-depth', type=int, default=internet.MAX_DEPTH,
        help='How many buttons to click')
    installer_parser.add_argument(
        '-f', '--state-frequency', type=int, default=internet.FREQUENCY,
        help='How frequently checking the current state')

    return parser.parse_args()


def setup_logging(loglevel):
    """Set up logging level and format. Silence few noisy logs."""
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

    logging.basicConfig(level=loglevel, format=log_format)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("twisted").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("vncdotool").setLevel(logging.WARNING)


if __name__ == '__main__':
    main()
