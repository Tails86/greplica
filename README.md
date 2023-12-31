# greplica

A grep clone in Python with both CLI and library interfaces, supporting ANSI color coding and more.

## Shameless Promotion

Check out my other Python clone tools:
- [refind](https://pypi.org/project/refind/)
- [sedeuce](https://pypi.org/project/sedeuce/)

## Known Differences with grep

- The -D, --devices option is not supported and no support is planned. All inputs are handled as
file streams only.
- Context cannot be given as raw number -NUM.
- The Python module `re` is internally used for all regular expressions. The inputted regular
expression is modified only when basic regular expressions are used. See --help for more
information.

## Contribution

Feel free to open a bug report or make a merge request on [github](https://github.com/Tails86/greplica/issues).

## Installation
This project is uploaded to PyPI at https://pypi.org/project/greplica/

To install, ensure you are connected to the internet and execute: `python3 -m pip install greplica --upgrade`

Once installed, there will be a script called `greplica` under Python's script directory. If `grep`
is not found on the system, then a script called `grep` will also be installed. Ensure Python's
scripts directory is under the environment variable `PATH` in order to be able to execute the script
properly from command line.

## CLI Help
```
usage: greplica [-E | -F | -G] [-P] [-e EXPRESSIONS] [-f FILE [FILE ...]] [-i]
                [--no-ignore-case] [-w] [-x] [--end END] [-z] [-s] [-v] [-V] [--help]
                [-m NUM] [-b] [-n] [--line-buffered] [-H] [-h] [--label LABEL] [-o] [-q]
                [--binary-files TYPE] [-a] [-I] [-d ACTION] [-r] [-R]
                [--include GLOB [GLOB ...]] [--exclude GLOB [GLOB ...]]
                [--exclude-from FILE [FILE ...]] [--exclude-dir GLOB [GLOB ...]] [-L] [-l]
                [-c] [-T] [-Z] [--result-sep SEP] [--name-num-sep SEP] [--name-byte-sep SEP]
                [--context-group-sep SEP] [--context-result-sep SEP]
                [--context-name-num-sep SEP] [--context-name-byte-sep SEP] [-B NUM] [-A NUM]
                [-C NUM] [--color [WHEN]] [-U]
                [EXPRESSIONS] [FILE [FILE ...]]

Reimplementation of grep command entirely in Python.

positional arguments:
  EXPRESSIONS           Expressions to search for, separated by newline character (\n). This
                        is required if --regexp or --file are not specified.
  FILE                  Files or directories to search. Stdin will be searched if not
                        specified, unless -r is specified. Then current directory will be
                        recursively searched.How directories are handled is controlled by -d
                        and -r options.

Expression Interpretation:
  -E, --extended-regexp
                        EXPRESSIONS are "extended" regular expressions. In this mode,
                        greplica passes regular expressions directly to Python re without
                        modification. This for the most part matches original "extended"
                        syntax, but be aware that there will be differences.
  -F, --fixed-strings   EXPRESSIONS are strings
  -G, --basic-regexp    EXPRESSIONS are "basic" regular expressions. In this mode, greplica
                        modifies escaping sequences for characters ?+{}|() before passing to
                        Python re. This for the most part matches original "basic" syntax,
                        but be aware that there will be differences.
  -P, --perl-regexp     EXPRESSIONS are "perl" regular expressions. In this mode, greplica
                        passes regular expressions directly to Python re without
                        modification. This for the most part matches original "perl" syntax,
                        but be aware that there will be differences.
  -e EXPRESSIONS, --regexp EXPRESSIONS
                        use EXPRESSIONS for matching
  -f FILE [FILE ...], --file FILE [FILE ...]
                        take EXPRESSIONS from FILE
  -i, --ignore-case     ignore case in expressions
  --no-ignore-case      do not ignore case (default)
  -w, --word-regexp     match whole words only
  -x, --line-regexp     match whole lines only
  --end END             end-of-line character for parsing search files (default: \n); this
                        does not affect file parsing for -f or --exclude-from
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
  --binary-files TYPE   sets how binary file is parsed; TYPE is 'binary', 'text', or
                        'without-match'
  -a, --text            same as --binary-files=text
  -I                    same as --binary-files=without-match
  -d ACTION, --directories ACTION
                        controls how directory input is handled in FILE; ACTION is 'read',
                        'recurse', or 'skip'
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
  --name-num-sep SEP    String to place between file name and line number when both are
                        enabled
  --name-byte-sep SEP   String to place between file name and byte number when both are
                        enabled
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
                        use ANSI escape codes to highlight the matching strings; WHEN is
                        'always', 'never', or 'auto'
  -U, --binary          do not strip CR characters at EOL (MSDOS/Windows)
  ```

## Library Help

greplica can be used as a library from another module. The following is a simple example.
```py
from greplica.grep import Grep

grep_obj = Grep()
grep_obj.add_expressions('hello .*ld')
grep_obj.add_files('file1.txt', 'path/to/file2.txt', 'path/to/directory/')
grep_obj.directory_handling_type = Grep.Directory.RECURSE
data = grep_obj.execute()

# Prints a list of Grep.FileDat objects which contain filename, start_index,
# stop_index, and num_matches. The values of start_index and stop_index are the start
# and stop indices into data.lines that matching in this file. start_index and
# stop_index will be None only when certain options prevent output to data.lines.
# num_matches may be less than (stop_index - start_index) if data.lines contain
# context separator lines when either *_context_count value is greater than 0 and
# context_sep is not ''.
# ex:
# file1.txt, 0, 1, 1
# path/to/file2.txt, 1, 2, 1
for f in data.files:
  print('{}, {}, {}, {}'.format(f.filename, f.start_index, f.stop_index, f.num_matches))

# Prints a list of Grep.LineDat objects which contain filename, line_num, byte_offset,
# and line. Context separator will be its own element in this list when either
# *_context_count value is greater than 0 and context_sep is not ''. In those cases,
# line_num and byte_offset will be None.
# ex:
# file1.txt, 3, 117, hello world!
# path/to/file2.txt, 8, 393, hello household
for l in data.lines:
  print('{}, {}, {}, {}'.format(l.filename, l.line_num, l.byte_offset, l.line))

# Prints a list of Grep.InfoDat objects which contain filename and info.
# ex:
# path/to/directory/file.bin, path/to/directory/file.bin: binary file matches
for i in data.info
  print('{}, {}'.format(i.filename, i.info))

# Prints a list of Grep.ErrorDat objects which contain filename and err_str.
# ex:
# path/to/directory/restricted/file.bin, greplica: [Errno 13] Permission denied:
# 'path/to/directory/restricted/file.bin'
for e in data.errors:
  print('{}, {}'.format(e.filename, e.err_str))
```

The following describes initialization arguments to Grep.
```py
__init__(self, out_file:io.IOBase=None, err_file:io.IOBase=None, default_in_file:io.IOBase=None)
  '''
  Initializes Grep
  Inputs: out_file - a file object to pass to print() as 'file' for regular messages.
                      This should be set to sys.stdout if writing to terminal is desired.
                      Writing to file is skipped when this is set to None. (default: None)
          err_file - a file object to pass to print() as 'file' for error messages.
                      This should be set to sys.stderr if writing to terminal is desired.
                      Writing to file is skipped when this is set to None. (default: None)
          default_in_file - default input file stream used when no files added.
                      This should be set to sys.stdin if reading from terminal is desired by default.
                      An exception will be caused on execute() if this is None and no files added.
                      (default: None)
  '''
```

The following methods may be called to add expressions, file paths, and globs.
```py
add_dir_exclude_globs(self, *args:Union[str, List[str]])
  '''
  Skip directories that match given globs.
  '''

add_expressions(self, *args:Union[str, List[str]])
  '''
  Adds a single expression or list of expressions that Grep will search for in selected files.
  Inputs: all arguments must be list of strings or string - each string is an expression
  '''

add_file_exclude_globs(self, *args:Union[str, List[str]])
  '''
  Skip files that match given globs.
  '''

add_file_include_globs(self, *args:Union[str, List[str]])
  '''
  Limit files to those matching given globs.
  '''

add_files(self, *args:Union[str, List[str]])
  '''
  Adds a single file or list of files that Grep will crawl through. Each entry must be a path
  to a file or directory. Directories are handled based on value of directory_handling_type.
  Inputs: all arguments must be list of strings or string - each string is a file path
  '''

clear_dir_exclude_globs(self)
  '''
  Clear all directory exclude globs previously added by add_dir_exclude_globs().
  '''

clear_expressions(self)
  '''
  Clears all expressions that were previously set by add_expressions().
  '''

clear_file_exclude_globs(self)
  '''
  Clear all file exclude globs previously added by add_file_exclude_globs().
  '''

clear_file_include_globs(self)
  '''
  Clear all file include globs previously added by add_file_include_globs().
  '''

clear_files(self)
  '''
  Clear all files that were previously set by add_files().
  '''
```

The following Grep options may be adjusted.
```py
# Determines how expressions are parsed
search_type:Grep.SearchType = Grep.SearchType.BASIC_REGEXP

# When true, expression's case is ignored during search
ignore_case:bool = False

# When true, regex search is performed using pattern \\b{expr}\\b
word_regexp:bool = False

# When true, line regex search is used
line_regexp:bool = False

# When true, no error messages are printed
no_messages:bool = False

# When true, matching lines are those that don't match expression
invert_match:bool = False

# When set, this is the maximum number of matching lines printed for each file
max_count:int = None

# When true, line number of match is printed before result
output_line_numbers:bool = False

# When true, file name is printed before result
output_file_name:bool = False

# When true, byte offset is printed before result
output_byte_offset:bool = False

# When true, each printed line is flushed before proceeding
line_buffered:bool = False

# (property) The sequence of bytes expected at the end of each line
# Returns bytes, can be set as str or bytes
end = b'\n'

# The string printed after header information and before line contents
results_sep:str = ':'

# The string printed before line number if both file name and line number are printed
name_num_sep:str = ':'

# The string printed before byte offset value if byte offset as well as either file
# name or line number is printed.
name_byte_sep:str = ':'

# The string printed between each context group
context_sep:str = '--\n'

# The string printed after header information and before context line contents
context_results_sep:str = '-'

# The string printed before context line number if both file name and line number are printed
context_name_num_sep:str = '-'

# The string printed before context byte offset value if byte offset as well as either
# file name or line number is printed.
context_name_byte_sep:str = '-'

# Grep.ColorMode: sets the color mode
self.color_mode:Grep.ColorMode = Grep.ColorMode.AUTO

# Grep.Directory: sets how directories are handled when they are included in file list
directory_handling_type:Grep.Directory = Grep.Directory.READ

# The label to print when output_file_name is true and stdin is parsed
label:str = '(standard input)'

# When true, normal output is not printed
quiet:bool = False

# When true, only the matching contents are printed for each line
only_matching:bool = False

# Grep.BinaryParseFunction: sets how binary files are handled
binary_parse_function:Grep.BinaryParseFunction = Grep.BinaryParseFunction.PRINT_ERROR

# When true, CR are stripped from the end of every line when found
strip_cr:bool = True

# Number of lines of context to print before a match
before_context_count:int = 0

# Number of lines of context to print after a match
after_context_count:int = 0

# When true, only the file name of matching files are printed
print_matching_files_only:bool = False

# When true, only the file name of non-matching files are printed
print_non_matching_files_only:bool = False

# When true, only count of number of matches for each file is printed
print_count_only:bool = False

# When true, add spaces to the left of numbers based on file size
space_numbers_by_size:bool = False

# Dictionary: Contains grep color information
# grep_color_dict gets initialized from environment variable GREP_COLORS; the default is:
# {
#     'mt':None,
#     'ms':'01;31',
#     'mc':'01;31',
#     'sl':'',
#     'cx':'',
#     'rv':False,
#     'fn':'35',
#     'ln':'32',
#     'bn':'32',
#     'se':'36',
#     'ne':False
# }
grep_color_dict:dict
```

At any point, reset() may be called to reset all settings.
```py
reset(self)
  '''
  Resets all Grep state values except for out_file, err_file, and default_in_file.
  '''
```

The following method executes using all data set above.
```py
execute(self, return_matches:bool=True) -> GrepResult
  '''
  Executes Grep with all the assigned attributes.
  Inputs: return_matches - set to True to fill in lines, info, and errors in the result
                         - set to False if outputting to terminal is the only thing that is
                           desired, saving memory
  Returns: a GrepResult object
  Raises: ValueError if no expressions added
          ValueError if no files added and no default input file set during init
  '''
```