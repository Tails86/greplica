from . import *

try:
    sys.exit(main(sys.argv[1:]))
except KeyboardInterrupt:
    print('')
    sys.exit(0)
