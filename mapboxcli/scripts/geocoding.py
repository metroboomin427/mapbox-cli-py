import logging

import click
import mapbox

from mapboxcli.compat import map
from .helpers import (MapboxCLIException, iter_query,
                      coords_from_query, echo_headers)


@click.command(short_help="Geocode an address or coordinates.")
@click.argument('query', default='-', required=False)
@click.option(
    '--forward/--reverse',
    default=True,
    help="Perform a forward or reverse geocode. [default: forward]")
@click.option('--include', '-i', 'include_headers',
              is_flag=True, default=False,
              help="Include HTTP headers in the output.")
@click.option(
    '--lat', type=float, default=None,
    help="Bias results toward this latitude (decimal degrees). --lon "
         "is also required.")
@click.option(
    '--lon', type=float, default=None,
    help="Bias results toward this longitude (decimal degrees). --lat "
         "is also required.")
@click.option(
    '--place-type', '-t', multiple=True, metavar='NAME', default=None,
    help="Restrict results to one or more of these place types: {0}.".format(
        sorted(mapbox.Geocoder().place_types.keys())))
@click.option('--output', '-o', default='-', help="Save output to a file.")
@click.pass_context
def geocoding(ctx, query, forward, include_headers, lat, lon, place_type, output):
    """This command returns places matching an address (forward mode) or
    places matching coordinates (reverse mode).

    In forward (the default) mode the query argument shall be an address
    such as '1600 pennsylvania ave nw'.

      $ mapbox geocode '1600 pennsylvania ave nw'

    In reverse mode the query argument shall be a JSON encoded array
    of longitude and latitude (in that order) in decimal degrees.

      $ mapbox geocode --reverse '[-77.4371, 37.5227]'

    An access token is required, see `mapbox --help`.
    """
    verbosity = (ctx.obj and ctx.obj.get('verbosity')) or 2
    logger = logging.getLogger('mapbox')

    access_token = (ctx.obj and ctx.obj.get('access_token')) or None
    stdout = click.open_file(output, 'w')

    geocoder = mapbox.Geocoder(access_token=access_token)

    if forward:
        for q in iter_query(query):
            try:
                resp = geocoder.forward(
                    q, types=place_type, lat=lat, lon=lon)
            except mapbox.validation.MapboxValidationError as exc:
                raise click.BadParameter(str(exc))

            if include_headers:
                echo_headers(resp.headers, file=stdout)
            if resp.status_code == 200:
                click.echo(resp.text, file=stdout)
            else:
                raise MapboxCLIException(resp.text.strip())
    else:
        for lon, lat in map(coords_from_query, iter_query(query)):
            try:
                resp = geocoder.reverse(lon=lon, lat=lat, types=place_type)
            except mapbox.validation.MapboxValidationError as exc:
                raise click.BadParameter(str(exc))

            if include_headers:
                echo_headers(resp.headers, file=stdout)
            if resp.status_code == 200:
                click.echo(resp.text, file=stdout)
            else:
                raise MapboxCLIException(resp.text.strip())
