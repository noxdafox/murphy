"""Windows UI Automation based GUI Scraping Agent.

HTTP server acting as Scraping Agent within the guest OS.

Execution:

  server.py <host> <port> <path_to_scraper>

Protocol:

  HTTP GET /

  Description:

  Scrape the current window and collect the output.

  Parameters:

    * recursive:
      Type: Boolean
      Default: False
      Description: Recursive scraping might return more information
                   but takes longer.
    * timeout:
      Type: Integer
      Default: 10
      Description: Maximum wait time for scraping results.

   Examples:

   curl -X GET "localhost:8000/?recursive=1&timeout=30"

The response is application/json MIME encoded in the format:

{"type": "scraper type",
 "status": "success|failure"
 "error": "error message"
 "result": "scraper output"}

"""

import json
import logging
import argparse
import subprocess

from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer


DEFAULT_TIMEOUT = 10
SCRAPER_TYPE = 'windows_ui_automation'


def scraper_class_factory(scraper_path):
    class ScraperAgent(BaseHTTPRequestHandler):
        """Serves HTTP requests allowing to execute remote commands."""
        scraper = scraper_path

        def do_GET(self):
            """Run simple command with parameters."""
            response = {'type': SCRAPER_TYPE}

            query = parse_qs(urlparse(self.path).query)
            recursive = bool(int(query.get('recursive', [False])[0]))
            timeout = int(query.get('timeout', [DEFAULT_TIMEOUT])[0])

            command = [self.scraper, 'true'] if recursive else self.scraper

            try:
                response['result'] = run_command(command, timeout=timeout)
                response['status'] = 'success'
                logging.info("Window successfully scraped")
                logging.debug(response['result'])
            except (RuntimeError, TimeoutError) as error:
                logging.exception(error)
                response['error'] = "%r" % error
                response['status'] = 'failure'

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            self.wfile.write(bytes(json.dumps(response), "utf8"))

    return ScraperAgent


def run_command(args: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Executes a command returning its exit code and output."""
    logging.info("Executing %s command %s.")

    process = subprocess.Popen(args,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    try:
        output = process.communicate(timeout=timeout)[0].decode('utf8')
    except subprocess.TimeoutExpired:
        process.terminate()
        raise TimeoutError(timeout)

    if process.returncode == 0:
        try:
            return json.loads(output)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Unable to decode JSON output:\n%s\n%s"
                % (output, error)) from error
    else:
        raise RuntimeError(
            "%s exit code %d, output:\n%s"
            % (' '.join(process.args), process.returncode, output))


def main():
    arguments = parse_arguments()

    logging.basicConfig(level=arguments.debug and 10 or 20)

    logging.info("Serving requests at %s %d.", arguments.host, arguments.port)

    try:
        run_server(arguments)
    except KeyboardInterrupt:
        logging.info("Termination request.")


def run_server(arguments: argparse.ArgumentParser):
    scraper_class = scraper_class_factory(arguments.scraper)
    server = HTTPServer((arguments.host, arguments.port), scraper_class)

    server.serve_forever()


def parse_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Windows UI Automation GUI Scraper Agent.')
    parser.add_argument('host', type=str, help='Server address')
    parser.add_argument('port', type=int, help='Server port')
    parser.add_argument('scraper', type=str, help='Path to scraper binary')
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, help='debug log')

    return parser.parse_args()


if __name__ == '__main__':
    main()
