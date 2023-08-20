# greplica
A grep clone in Python with both CLI and library interfaces, supporting ANSI color coding and more.

## CLI Help
```
usage: grep.py [-E | -F | -G] [-e EXPRESSIONS] [-f FILE] [-i] [--no-ignore-case] [-w] [-x] [--end END] [-z] [-s] [-v] [-V] [--help] [-m NUM] [-b] [-n]
               [--line-buffered] [-H] [-h] [--label LABEL] [-o] [-q] [--binary-files TYPE] [-a] [-I] [-d ACTION] [-r] [-R] [--include GLOB [GLOB ...]]
               [--exclude GLOB [GLOB ...]] [--exclude-from FILE [FILE ...]] [--exclude-dir GLOB [GLOB ...]] [-L] [-l] [-c] [-T] [-Z] [--result-sep SEP]
               [--name-num-sep SEP] [--name-byte-sep SEP] [--context-group-sep SEP] [--context-result-sep SEP] [--context-name-num-sep SEP]
               [--context-name-byte-sep SEP] [-B NUM] [-A NUM] [-C NUM] [--color [WHEN]] [-U]
               [EXPRESSIONS] [FILE [FILE ...]]

Reimplementation of grep command entirely in Python.

positional arguments:
  EXPRESSIONS           Expressions to search for, separated by newline character (\n). This is required if --regexp or --file are not specified.
  FILE                  Files or directories to search. Stdin will be searched if not specified. How directories are handled is controled by -d and -r options.

Expression Interpretation:
  -E, --extended-regexp
                        EXPRESSIONS are extended regular expressions
  -F, --fixed-strings   EXPRESSIONS are strings
  -G, --basic-regexp    EXPRESSIONS are basic regular expressions
  -e EXPRESSIONS, --regexp EXPRESSIONS
                        use EXPRESSIONS for matching
  -f FILE, --file FILE  take EXPRESSIONS from FILE
  -i, --ignore-case     ignore case in expressions
  --no-ignore-case      do not ignore case (default)
  -w, --word-regexp     match whole words only
  -x, --line-regexp     match whole lines only
  --end END             newline character lines will be parsed by (default: \n)
  -z, --null-data       same as --end='\0'

Miscellaneous:
  -s, --no-messages     suppress error messages
  -v, --invert-match    select non-matching lines
  -V, --version         display version information and exit
  --help                display this help text and exit

Output control:
  -m NUM, --max-count NUM
                        stop after NUM lines
  -b, --byte-offset     print line's byte offset with each line
  -n, --line-number     print line number with each line
  --line-buffered       flush output on each line
  -H, --with-filename   print file name with each line
  -h, --no-filename     suppress the file name output
  --label LABEL         use LABEL as the standard input file name
  -o, --only-matching   show only nonempty parts of lines that match
  -q, --quiet, --silent
                        suppress all normal output
  --binary-files TYPE   sets how binary file is parsed; TYPE is 'binary', 'text', or 'without-match'
  -a, --text            same as --binary-files=text
  -I                    same as --binary-files=without-match
  -d ACTION, --directories ACTION
                        controls how directory input is handled in FILE; ACTION is 'read', 'recurse', or 'skip'
  -r, --recursive       same as --directories=recurse
  -R, --dereference-recursive
                        same as --directories=recurse_links
  --include GLOB [GLOB ...]
                        limit files to those matching GLOB
  --exclude GLOB [GLOB ...]
                        skip files that match GLOB
  --exclude-from FILE [FILE ...]
                        read FILE for exclude globs file name globs
  --exclude-dir GLOB [GLOB ...]
                        skip directories that match GLOB
  -L, --files-without-match
                        print only names of FILEs with no selected lines
  -l, --files-with-matches
                        print only names of FILEs with selected lines
  -c, --count           print only a count of selected lines per FILE
  -T, --initial-tab     currently just adds tabs to each sep value (will make better later)
  -Z, --null            adds 0 to the end of result-sep
  --result-sep SEP      String to place between header info and and search output
  --name-num-sep SEP    String to place between file name and line number when both are enabled
  --name-byte-sep SEP   String to place between file name and byte number when both are enabled
  --context-group-sep SEP
                        String to print between context groups
  --context-result-sep SEP
                        String to place between header info and context line
  --context-name-num-sep SEP
                        String to place between file name and line number on context line
  --context-name-byte-sep SEP
                        String to place between file name and byte number on context line

Context Control:
  -B NUM, --before-context NUM
                        print NUM lines of leading context
  -A NUM, --after-context NUM
                        print NUM lines of trailing context
  -C NUM, --context NUM
                        print NUM lines of output context
  --color [WHEN], --colour [WHEN]
                        use ANSI escape codes to highlight the matching strings; WHEN is 'always', 'never', or 'auto'
  -U, --binary          do not strip CR characters at EOL (MSDOS/Windows)
  ```