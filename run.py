"""
Usage:
    python run.py -s
    python run.py -a [sub_id]

Optional arguments:
    -h, --help  show help doc
    -a, --add   add subscription
    -s, --start start task
"""

import getopt
import sys


if __name__ == '__main__':
    try:
        options, args = getopt.getopt(sys.argv[1:], 'ha:s', ['help', 'add=', 'start'])
    except getopt.GetoptError:
        print(__doc__)
        sys.exit()
    if not options:
        print(__doc__)
        sys.exit()
    for name, value in options:
        if name in ['-h', '--help']:
            print(__doc__)
            sys.exit()
        elif name in ['-a', '--add']:
            import asyncio
            from util import new_live_sub
            asyncio.get_event_loop().run_until_complete(asyncio.gather(new_live_sub(sub_id=value)))
        elif name in ['-s', '--start']:
            from sched import start_scheduler
            start_scheduler()
