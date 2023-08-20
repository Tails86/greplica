import sys
from .grep import main as grep_main

def main():
    ''' Grep main using arguments from sys.argv '''
    try:
        return grep_main(sys.argv[1:])
    except KeyboardInterrupt:
        # User quit - no need to print error, just exit gracefully
        print('')
        return 0

# Execute above
sys.exit(main())
