"""Serve only a chosen artifact directory on loopback, with MP4 range seeking."""
import argparse
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
import uvicorn


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    if not (directory / 'manifest.json').is_file() or not (directory / 'index.html').is_file():
        parser.error('Choose the prepared demo artifact directory, not a workspace root.')
    app = Starlette(routes=[Mount('/', app=StaticFiles(directory=directory, html=True))])
    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='warning')
