#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2023 James Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import argparse
from enum import Enum
import enum
import re
import fnmatch
import glob

__version__ = '1.0.0'
PACKAGE_NAME = 'greplica'

class BinaryDetectedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class FileIterable:
    ''' Base class for a custom file iterable '''
    # Limit each line to 128 kB which isn't human parsable at that size anyway
    LINE_BYTE_LIMIT = 128 * 1024

    def __iter__(self):
        return None

    def __next__(self):
        return None

    @property
    def name(self):
        return None

    @property
    def eof(self):
        return False

class AutoInputFileIterable(FileIterable):
    '''
    Automatically opens file on iteration and returns lines as bytes or strings.
    '''
    def __init__(self, file_path, file_mode='rb', newline_str='\n'):
        self._file_path = file_path
        self._file_mode = file_mode
        self._newline_str = newline_str
        self._as_bytes = 'b' in file_mode
        if isinstance(self._newline_str, str):
            self._newline_str = self._newline_str.encode()
        self._fp = None
        if not self._as_bytes:
            # Force reading as bytes
            self._file_mode += 'b'

    def __del__(self):
        if self._fp:
            self._fp.close()
            self._fp = None

    def __iter__(self):
        # Custom iteration
        if self._fp:
            self._fp.close()
        self._fp = open(self._file_path, self._file_mode)
        return self

    def __next__(self):
        # Custom iteration
        if self._fp:
            b = b''
            last_b = b' '
            end = b''
            newline_len = len(self._newline_str)
            while end != self._newline_str:
                last_b = self._fp.read(1)
                if last_b:
                    if len(b) < __class__.LINE_BYTE_LIMIT:
                        b += last_b
                    # else: overflow - can be detected by checking that the line ends with newline_str
                    end += last_b
                    end = end[-newline_len:]
                else:
                    # End of file
                    self._fp.close()
                    self._fp = None
                    break
            if b:
                if self._as_bytes:
                    return b
                else:
                    try:
                        return b.decode()
                    except UnicodeDecodeError:
                        return b
            else:
                self._fp = None
                raise StopIteration
        else:
            raise StopIteration

    @property
    def name(self):
        return self._file_path

    @property
    def eof(self):
        return (self._fp is None)

class StdinIterable(FileIterable):
    '''
    Reads from stdin and returns lines as bytes or strings.
    '''
    def __init__(self, as_bytes=True, end='\n', label='(standard input)'):
        self._as_bytes = as_bytes
        self._end = end
        self._label = label
        if isinstance(self._end, str):
            self._end = self._end.encode()
        self._eof_detected = False

    def __iter__(self):
        # Custom iteration
        self._eof_detected = False
        return self

    def __next__(self):
        # Custom iteration
        if self._eof_detected:
            raise StopIteration
        b = b''
        end = b''
        end_len = len(self._end)
        while end != self._end:
            last_b = sys.stdin.buffer.read(1)
            if last_b:
                if len(b) < __class__.LINE_BYTE_LIMIT:
                    b += last_b
                # else: overflow - can be detected by checking that the line ends with end
                end += last_b
                end = end[-end_len:]
            else:
                self._eof_detected = True
                break
        if self._as_bytes:
            return b
        else:
            try:
                return b.decode()
            except UnicodeDecodeError:
                return b

    @property
    def name(self):
        return self._label

    @property
    def eof(self):
        return self._eof_detected

class AnsiFormat(Enum):
    '''
    Formatting which may be supplied to AnsiString.
    '''
    RESET='0'
    BOLD='1'
    FAINT='2'
    ITALIC='3'
    ITALICS=ITALIC # Alias
    UNDERLINE='4'
    SLOW_BLINK='5'
    RAPID_BLINK='6'
    SWAP_BG_FG='7'
    HIDE='8'
    CROSSED_OUT='9'
    DEFAULT_FONT='10'
    ALT_FONT_1='11'
    ALT_FONT_2='12'
    ALT_FONT_3='13'
    ALT_FONT_4='14'
    ALT_FONT_5='15'
    ALT_FONT_6='16'
    ALT_FONT_7='17'
    ALT_FONT_8='18'
    ALT_FONT_9='19'
    GOTHIC_FONT='20'
    DOUBLE_UNDERLINE='21'
    NO_BOLD_FAINT='22'
    NO_ITALIC='23'
    NO_UNDERLINE='24'
    NO_BLINK='25'
    PROPORTIONAL_SPACING='26'
    NO_SWAP_BG_FG='27'
    NO_HIDE='28'
    NO_CROSSED_OUT='29'
    NO_PROPORTIONAL_SPACING='50'
    FRAMED='51'
    ENCIRCLED='52'
    OVERLINED='53'
    NO_FRAMED_ENCIRCLED='54'
    NO_OVERLINED='55'
    SET_UNDERLINE_COLOR='58' # Must be proceeded by rgb values
    DEFAULT_UNDERLINE_COLOR='59'

    FG_BLACK='30'
    FG_RED='31'
    FG_GREEN='32'
    FG_YELLOW='33'
    FG_BLUE='34'
    FG_MAGENTA='35'
    FG_CYAN='36'
    FG_WHITE='37'
    FG_SET='38' # Must be proceeded by rgb values
    FG_DEFAULT='39'
    FG_ORANGE=FG_SET+';5;202'
    FG_PURPLE=FG_SET+';5;129'

    BG_BLACK='40'
    BG_RED='41'
    BG_GREEN='42'
    BG_YELLOW='43'
    BG_BLUE='44'
    BG_MAGENTA='45'
    BG_CYAN='46'
    BG_WHITE='47'
    BG_SET='48' # Must be proceeded by rgb values
    BG_DEFAULT='49'
    BG_ORANGE=BG_SET+';5;202'
    BG_PURPLE=BG_SET+';5;129'

class AnsiString:
    '''
    Represents an ANSI colorized/formatted string. All or part of the string may contain style and
    color formatting which may be used to print out to an ANSI-supported terminal such as those
    on Linux, Mac, and Windows 10+.

    Example 1:
    s = AnsiString('This string is red and bold string', [AnsiFormat.BOLD, AnsiFormat.FG_RED])
    print(s)

    Example 2:
    s = AnsiString('This string contains custom formatting', '38;2;175;95;95')
    print(s)

    Example 3:
    s = AnsiString('This string contains multiple color settings across different ranges')
    s.apply_formatting(AnsiFormat.BOLD, 5, 6)
    s.apply_formatting(AnsiFormat.BG_BLUE, 21, 8)
    s.apply_formatting([AnsiFormat.FG_ORANGE, AnsiFormat.ITALIC], 21, 14)
    print(s)

    Example 4:
    s = AnsiString('This string will be formatted bold and red')
    print('{:01;31}'.format(s))

    Example 5:
    s = AnsiString('This string will be formatted bold and red')
    # Use any name within AnsiFormat (can be lower or upper case representation of the name)
    print('{:bold;fg_red}'.format(s))

    Example 6:
    s = AnsiString('This string will be formatted bold and red')
    # The character '[' tells the format method to do no parsing/checking and use verbatim as codes
    print('{:[01;31}'.format(s))
    '''

    # The escape sequence that needs to be formatted with command str
    ANSI_ESCAPE_FORMAT = '\x1b[{}m'
    # The escape sequence which will clear all previous formatting (empty command is same as 0)
    ANSI_ESCAPE_CLEAR = ANSI_ESCAPE_FORMAT.format('')

    # Number of elements in each value of _color_settings dict
    SETTINGS_ITEM_LIST_LEN = 2
    # Index of _color_settings value list which contains settings to apply
    SETTINGS_APPLY_IDX = 0
    # Index of _color_settings value list which contains settings to remove
    SETTINGS_REMOVE_IDX = 1

    class Settings:
        '''
        Internal use only - mainly used to create a unique objects which may contain same strings
        '''
        def __init__(self, setting_or_settings):
            if not isinstance(setting_or_settings, list):
                settings = [setting_or_settings]
            else:
                settings = setting_or_settings

            for i, item in enumerate(settings):
                if isinstance(item, str):
                    # Use string verbatim
                    pass
                elif hasattr(item, 'value') and isinstance(item.value, str):
                    # Likely an enumeration - use the value
                    settings[i] = item.value
                else:
                    raise TypeError('Unsupported type for setting_or_settings: {}'.format(type(setting_or_settings)))

            self._str = ';'.join(settings)

        def __str__(self):
            return self._str

    def __init__(self, s='', setting_or_settings=None):
        self._s = s
        # Key is the string index to make a color change at
        # Each value element is a list of 2 lists
        #   index 0: the settings to apply at this string index
        #   index 1: the settings to remove at this string index
        self._color_settings = {}
        if setting_or_settings:
            self.apply_formatting(setting_or_settings)

    def assign_str(self, s):
        '''
        Assigns the base string.
        '''
        self._s = s

    @property
    def base_str(self):
        '''
        Returns the base string without any formatting set.
        '''
        return self._s

    @staticmethod
    def _insert_settings_to_dict(settings_dict, idx, apply, settings, topmost=True):
        if idx not in settings_dict:
            settings_dict[idx] = [[] for _ in range(__class__.SETTINGS_ITEM_LIST_LEN)]
        list_idx = __class__.SETTINGS_APPLY_IDX if apply else __class__.SETTINGS_REMOVE_IDX
        if topmost:
            settings_dict[idx][list_idx].append(settings)
        else:
            settings_dict[idx][list_idx].insert(0, settings)

    def _insert_settings(self, idx, apply, settings, topmost=True):
        __class__._insert_settings_to_dict(self._color_settings, idx, apply, settings, topmost)

    def apply_formatting(self, setting_or_settings, start_idx=0, length=None, topmost=True):
        '''
        Sets the formatting for a given range of characters.
        Inputs: setting_or_settings - Can either be a single item or list of items;
                                      each item can either be a string or AnsiFormat type
                start_idx - The string start index where setting(s) are to be applied
                length - Number of characters to apply settings or None to apply until end of string
                topmost - When true, this setting is placed at the end of the set for the given
                        start_index meaning it is applied last; when false, setting is applied first

        Note: The desired effect may not be achieved if the same setting is applied over an
              overlapping range of characters.
        '''
        if not setting_or_settings:
            # Ignore - nothing to apply
            return
        elif length is not None and length <= 0:
            # Ignore - nothing to apply
            return

        settings = __class__.Settings(setting_or_settings)

        # Apply settings
        self._insert_settings(start_idx, True, settings, topmost)

        if length is not None:
            # Remove settings
            self._insert_settings(start_idx + length, False, settings, topmost)

    def apply_formatting_for_match(self, setting_or_settings, match_object, group=0):
        '''
        Apply formatting using a match object generated from re
        '''
        s = match_object.start(group)
        e = match_object.end(group)
        self.apply_formatting(setting_or_settings, s, e - s)

    def clear_formatting(self):
        '''
        Clears all internal formatting.
        '''
        self._color_settings = {}

    class SettingsIterator:
        def __init__(self, settings_dict):
            self.settings_dict = settings_dict
            self.current_settings = []
            self.dict_iter = iter(sorted(self.settings_dict))

        def __iter__(self):
            return self

        def __next__(self):
            # Will raise StopIteration when complete
            idx = next(self.dict_iter)
            settings = self.settings_dict[idx]
            # Remove settings that it is time to remove
            for setting in settings[AnsiString.SETTINGS_REMOVE_IDX]:
                # setting object will only be matched and removed if it is the same reference to one
                # previously added - will raise exception otherwise which should not happen if the
                # settings dictionary and this method were setup correctly.
                self.current_settings.remove(setting)
            # Apply settings that it is time to add
            self.current_settings += settings[AnsiString.SETTINGS_APPLY_IDX]
            return (idx, settings, self.current_settings)

    def _slice_val_to_idx(self, val, default):
        if val is None:
            return default
        elif val < 0:
            ret_val = len(self._s) + val
            if ret_val < 0:
                ret_val = 0
            return ret_val
        else:
            return val

    def __getitem__(self, val):
        ''' Returns a AnsiString object which represents a substring of self '''
        if isinstance(val, int):
            st = val
            en = val + 1
        elif isinstance(val, slice):
            if val.step is not None and val.step != 1:
                raise ValueError('Step other than 1 not supported')
            st = self._slice_val_to_idx(val.start, 0)
            en = self._slice_val_to_idx(val.stop, len(self._s))
        else:
            raise TypeError('Invalid type for __getitem__')

        if st == 0 and en == len(self._s):
            # No need to make substring
            return self

        new_s = AnsiString(self._s[val])
        last_settings = []
        settings_initialized = False
        for idx, settings, current_settings in __class__.SettingsIterator(self._color_settings):
            if idx >= len(self._s) or idx >= en:
                # Complete
                break
            if idx == st:
                new_s._color_settings[0] = [list(current_settings), []]
                settings_initialized = True
            elif idx > st:
                if not settings_initialized:
                    new_s._color_settings[0] = [last_settings, []]
                    settings_initialized = True
                new_s._color_settings[idx - st] = [list(settings[0]), list(settings[1])]
            last_settings = list(current_settings)
        return new_s

    def __str__(self):
        '''
        Returns an ANSI format string with only internal formatting set.
        '''
        return self.__format__(None)

    def __format__(self, __format_spec):
        '''
        Returns an ANSI format string with both internal and given formatting spec set.
        '''
        if not __format_spec and not self._color_settings:
            # No formatting
            return self._s

        out_str = ''
        last_idx = 0

        settings_dict = self._color_settings
        if __format_spec:
            # Make a local copy and add this temporary format spec
            settings_dict = dict(self._color_settings)

            if __format_spec.startswith("["):
                # Use the rest of the string as-is for settings
                format_settings = __class__.Settings(__format_spec[1:])
            else:
                # The format string contains names within AnsiFormat or integers, separated by semicolon
                formats = __format_spec.split(';')
                format_settings_strs = []
                for format in formats:
                    try:
                        ansi_format = AnsiFormat[format.upper()]
                    except KeyError:
                        try:
                            _ = int(format)
                        except ValueError:
                            raise ValueError(
                                'AnsiString.__format__ failed to parse format ({}); invalid name: {}'
                                .format(__format_spec, format)
                            )
                        else:
                            # Value is an integer - use the format verbatim
                            format_settings_strs.append(format)
                    else:
                        format_settings_strs.append(ansi_format.value)
                format_settings = __class__.Settings(';'.join(format_settings_strs))

            __class__._insert_settings_to_dict(settings_dict, 0, True, format_settings, True)

        clear_needed = False
        for idx, settings, current_settings in __class__.SettingsIterator(settings_dict):
            if idx >= len(self._s):
                # Invalid
                break
            # Catch up output to current index
            out_str += self._s[last_idx:idx]
            last_idx = idx

            settings_to_apply = [str(s) for s in current_settings]
            if settings[__class__.SETTINGS_REMOVE_IDX] and settings_to_apply:
                # Settings were removed and there are settings to be applied -
                # need to reset before applying current settings
                settings_to_apply = [AnsiFormat.RESET.value] + settings_to_apply
            # Apply these settings
            out_str += __class__.ANSI_ESCAPE_FORMAT.format(';'.join(settings_to_apply))
            # Save this flag in case this is the last loop
            clear_needed = bool(current_settings)

        # Final catch up
        out_str += self._s[last_idx:]
        if clear_needed:
            # Clear settings
            out_str += __class__.ANSI_ESCAPE_CLEAR

        return out_str

# Contains default color definitions when GREP_COLORS environment variable not defined
DEFAULT_GREP_ANSI_COLORS = {
    'mt':None,
    'ms':'01;31',
    'mc':'01;31',
    'sl':'',
    'cx':'',
    'rv':False,
    'fn':'35',
    'ln':'32',
    'bn':'32',
    'se':'36',
    'ne':False
}

def _expression_escape_invert(expression, chars):
    '''
    Inverts regex expression escape characters. This is helpful to transform format string from basic
    to extended regex format (and vice-versa).
    ex: \( -> ( and ( -> \(
    '''
    for char in chars:
        escaped_char = '\\' + char
        expression_split = expression.split(escaped_char)
        new_expression_split = []
        for piece in expression_split:
            new_expression_split.append(piece.replace(char, escaped_char))
        expression = char.join(new_expression_split)
    return expression

def _parse_expressions(expressions):
    # Split for both \r\n and \n
    expressions = [y for x in expressions.split('\r\n') for y in x.split('\n')]
    # Ignore last new line, if any
    if expressions and not expressions[-1]:
        expressions = expressions[:-1]
    return expressions

class Grep:
    '''
    Contains all functionality to grep through files to find and print matching lines.
    '''
    class SearchType(Enum):
        FIXED_STRINGS = enum.auto()
        BASIC_REGEXP = enum.auto()
        EXTENDED_REGEXP = enum.auto()

    class ColorOutputMode(Enum):
        AUTO = enum.auto()
        ALWAYS = enum.auto()
        NEVER = enum.auto()

    class Directory(Enum):
        READ = enum.auto()
        RECURSE = enum.auto()
        RECURSE_LINKS = enum.auto()
        SKIP = enum.auto()

    class BinaryParseFunction(Enum):
        PRINT_ERROR = enum.auto()
        IGNORE_DECODE_ERRORS = enum.auto()
        SKIP = enum.auto()

    def __init__(self, print_file=None):
        '''
        Initializes Grep
        Inputs: print_file - a file object to pass to print() as 'file' or None for stdout
        '''
        self.reset()
        self._print_file = print_file

    def reset(self):
        '''
        Resets all Grep state values except for the print file.
        '''
        self._expressions = []
        self._files = []
        self._file_include_globs = []
        self._file_exclude_globs = []
        self._dir_exclude_globs = []
        self._search_type = __class__.SearchType.BASIC_REGEXP
        self._ignore_case = False
        self._word_regexp = False
        self._line_regexp = False
        self._no_messages = False
        self._invert_match = False
        self._max_count = None
        self._output_line_numbers = False
        self._output_file_name = False
        self._output_byte_offset = False
        self._line_buffered = False
        self._end = b'\n'
        self._results_sep = ':'
        self._name_num_sep = ':'
        self._name_byte_sep = ':'
        self._context_sep = '--\n'
        self._context_results_sep = '-'
        self._context_name_num_sep = '-'
        self._context_name_byte_sep = '-'
        self._color_output_mode = __class__.ColorOutputMode.AUTO
        self._directory_handling_type = __class__.Directory.READ
        self._label = '(standard input)'
        self._quiet = False
        self._only_matching = False
        self._binary_parse_function = __class__.BinaryParseFunction.PRINT_ERROR
        self._strip_cr = True
        self._before_context_count = 0
        self._after_context_count = 0
        self._print_matching_files_only = False
        self._print_non_matching_files_only = False
        self._print_count_only = False

    def add_expression(self, expression_or_expressions):
        '''
        Adds a single expression or list of expressions that Grep will search for in selected files.
        Inputs: expression_or_expressions - must be of type list or str
        '''
        if isinstance(expression_or_expressions, list):
            self._expressions.extend(expression_or_expressions)
        elif isinstance(expression_or_expressions, str):
            self._expressions.append(expression_or_expressions)
        else:
            raise TypeError('Invalid type ({}) for expression_or_expressions'
                            .format(type(expression_or_expressions)))

    def add_expressions(self, expression_or_expressions):
        '''
        Adds a single expression or list of expressions that Grep will search for in selected files.
        Inputs: expression_or_expressions - must be of type list or str
        '''
        self.add_expression(expression_or_expressions)

    def clear_expressions(self):
        '''
        Clears all expressions that were previously set by add_expression().
        '''
        self._expressions.clear()

    def add_files(self, file_or_files):
        '''
        Adds a single file or list of files that Grep will crawl through. Each entry must be a path
        to a file or directory. Directories are handled based on value of directory_handling_type.
        Inputs: file_or_files - must be of type list or str
        '''
        if isinstance(file_or_files, list):
            self._files.extend(file_or_files)
        elif isinstance(file_or_files, str):
            self._files.append(file_or_files)
        else:
            raise TypeError('Invalid type ({}) for file_or_files'.format(type(file_or_files)))

    def clear_files(self):
        '''
        Clear all files that were previously set by add_files().
        '''
        self._files = []

    def add_file_include_globs(self, glob_or_globs):
        if isinstance(glob_or_globs, list):
            self._file_include_globs.extend(glob_or_globs)
        elif isinstance(glob_or_globs, str):
            self._file_include_globs.append(glob_or_globs)
        else:
            raise TypeError('Invalid type ({}) for glob_or_globs'.format(type(glob_or_globs)))

    def clear_file_include_globs(self):
        self._file_include_globs = []

    def add_file_exclude_globs(self, glob_or_globs):
        if isinstance(glob_or_globs, list):
            self._file_exclude_globs.extend(glob_or_globs)
        elif isinstance(glob_or_globs, str):
            self._file_exclude_globs.append(glob_or_globs)
        else:
            raise TypeError('Invalid type ({}) for glob_or_globs'.format(type(glob_or_globs)))

    def clear_file_exclude_globs(self):
        self._file_exclude_globs = []

    def add_dir_exclude_globs(self, glob_or_globs):
        if isinstance(glob_or_globs, list):
            self._dir_exclude_globs.extend(glob_or_globs)
        elif isinstance(glob_or_globs, str):
            self._dir_exclude_globs.append(glob_or_globs)
        else:
            raise TypeError('Invalid type ({}) for glob_or_globs'.format(type(glob_or_globs)))

    def clear_dir_exclude_globs(self):
        self._dir_exclude_globs = []

    @property
    def search_type(self):
        '''
        Grep.SearchType: The search type which sets how expressions are parsed.
        '''
        return self._search_type

    @search_type.setter
    def search_type(self, search_type):
        if not isinstance(search_type, __class__.SearchType):
            raise TypeError('Invalid type ({}) for search_type'.format(type(search_type)))
        self._search_type = search_type

    @property
    def ignore_case(self):
        '''
        Boolean: when true, expression's case is ignored during search
        '''
        return self._ignore_case

    @ignore_case.setter
    def ignore_case(self, ignore_case):
        self._ignore_case = ignore_case

    @property
    def word_regexp(self):
        '''
        Boolean: when true, regex search is performed using pattern \\b{expr}\\b
        '''
        return self._word_regexp

    @word_regexp.setter
    def word_regexp(self, word_regexp):
        self._word_regexp = word_regexp

    @property
    def line_regexp(self):
        '''
        Boolean: when true, line regex search is used
        '''
        return self._line_regexp

    @line_regexp.setter
    def line_regexp(self, line_regexp):
        self._line_regexp = line_regexp

    @property
    def no_messages(self):
        '''
        Boolean: when true, no error messages are printed
        '''
        return self._no_messages

    @no_messages.setter
    def no_messages(self, no_messages):
        self._no_messages = no_messages

    @property
    def invert_match(self):
        '''
        Boolean: when true, matching lines are those that don't match expression
        '''
        return self._invert_match

    @invert_match.setter
    def invert_match(self, invert_match):
        self._invert_match = invert_match

    @property
    def max_count(self):
        '''
        None or int: when set, this is the maximum number of matching lines printed for each file
        '''
        return self._max_count

    @max_count.setter
    def max_count(self, max_count):
        self._max_count = max_count

    @property
    def output_line_numbers(self):
        '''
        Boolean: when true, line number of match is printed before result
        '''
        return self._output_line_numbers

    @output_line_numbers.setter
    def output_line_numbers(self, output_line_numbers):
        self._output_line_numbers = output_line_numbers

    @property
    def output_file_name(self):
        '''
        Boolean: when true, file name is printed before result
        '''
        return self._output_file_name

    @output_file_name.setter
    def output_file_name(self, output_file_name):
        self._output_file_name = output_file_name

    @property
    def output_byte_offset(self):
        '''
        Boolean: when true, byte offset is printed before result
        '''
        return self._output_byte_offset

    @output_byte_offset.setter
    def output_byte_offset(self, output_byte_offset):
        self._output_byte_offset = output_byte_offset

    @property
    def line_buffered(self):
        '''
        Boolean: when true, each printed line is flushed before proceeding
        '''
        return self._line_buffered

    @line_buffered.setter
    def line_buffered(self, line_buffered):
        self._line_buffered = line_buffered

    @property
    def label(self):
        '''
        String: the label to print when output_file_name is true and stdin is parsed
        '''
        return self._label

    @label.setter
    def label(self, label):
        self._label = label

    @property
    def quiet(self):
        '''
        Boolean: when true, normal output is not printed
        '''
        return self._quiet

    @quiet.setter
    def quiet(self, quiet):
        self._quiet = quiet

    @property
    def results_sep(self):
        '''
        String: the string printed after header information and before line contents
        '''
        return self._results_sep

    @results_sep.setter
    def results_sep(self, results_sep):
        if not isinstance(results_sep, str):
            raise TypeError('Invalid type ({}) for results_sep'.format(type(results_sep)))
        self._results_sep = results_sep

    @property
    def name_num_sep(self):
        '''
        String: the string printed before line number if both file name and line number are printed
        '''
        return self._name_num_sep

    @name_num_sep.setter
    def name_num_sep(self, name_num_sep):
        if not isinstance(name_num_sep, str):
            raise TypeError('Invalid type ({}) for name_num_sep'.format(type(name_num_sep)))
        self._name_num_sep = name_num_sep

    @property
    def name_byte_sep(self):
        '''
        String: the string printed before byte offset value if byte offset as well as either file
        name or line number is printed.
        '''
        return self._name_byte_sep

    @name_byte_sep.setter
    def name_byte_sep(self, name_byte_sep):
        if not isinstance(name_byte_sep, str):
            raise TypeError('Invalid type ({}) for name_byte_sep'.format(type(name_byte_sep)))
        self._name_byte_sep = name_byte_sep

    @property
    def context_sep(self):
        '''
        String: the string printed between each context group
        '''
        return self._context_sep

    @context_sep.setter
    def context_sep(self, context_sep):
        if not isinstance(context_sep, str):
            raise TypeError('Invalid type ({}) for context_sep'.format(type(context_sep)))
        self._context_sep = context_sep

    @property
    def context_results_sep(self):
        '''
        String: the string printed after header information and before context line contents
        '''
        return self._context_results_sep

    @context_results_sep.setter
    def context_results_sep(self, context_results_sep):
        if not isinstance(context_results_sep, str):
            raise TypeError('Invalid type ({}) for context_results_sep'.format(type(context_results_sep)))
        self._context_results_sep = context_results_sep

    @property
    def context_name_num_sep(self):
        '''
        String: the string printed before context line number if both file name and line number are printed
        '''
        return self._context_name_num_sep

    @context_name_num_sep.setter
    def context_name_num_sep(self, context_name_num_sep):
        if not isinstance(context_name_num_sep, str):
            raise TypeError('Invalid type ({}) for context_name_num_sep'.format(type(context_name_num_sep)))
        self._context_name_num_sep = context_name_num_sep

    @property
    def context_name_byte_sep(self):
        '''
        String: the string printed before context byte offset value if byte offset as well as either
        file name or line number is printed.
        '''
        return self._context_name_byte_sep

    @context_name_byte_sep.setter
    def context_name_byte_sep(self, context_name_byte_sep):
        if not isinstance(context_name_byte_sep, str):
            raise TypeError('Invalid type ({}) for context_name_byte_sep'.format(type(context_name_byte_sep)))
        self._context_name_byte_sep = context_name_byte_sep

    @property
    def color_output_mode(self):
        '''
        Grep.ColorOutputMode: sets when ANSI escape codes are printed
        '''
        return self._color_output_mode

    @color_output_mode.setter
    def color_output_mode(self, color_output_mode):
        if not isinstance(color_output_mode, __class__.ColorOutputMode):
            raise TypeError('Invalid type ({}) for color_output_mode'.format(type(color_output_mode)))
        self._color_output_mode = color_output_mode

    @property
    def end(self):
        '''
        String: the sequence of characters expected at the end of each line ex: \\n
        '''
        return self._end

    @end.setter
    def end(self, end):
        if isinstance(end, str):
            end = end.encode()
        self._end = end

    @property
    def directory_handling_type(self):
        '''
        Grep.Directory: sets how directories are handled when they are included in file list
        '''
        return self._directory_handling_type

    @directory_handling_type.setter
    def directory_handling_type(self, directory_handling_type):
        if not isinstance(directory_handling_type, __class__.Directory):
            raise TypeError('Invalid type ({}) for directory_handling_type'.format(type(directory_handling_type)))
        self._directory_handling_type = directory_handling_type

    @property
    def only_matching(self):
        '''
        Boolean: when true, only the matching contents are printed for each line
        '''
        return self._only_matching

    @only_matching.setter
    def only_matching(self, only_matching):
        self._only_matching = only_matching

    @property
    def binary_parse_function(self):
        '''
        Grep.BinaryParseFunction: sets how binary files are handled
        '''
        return self._binary_parse_function

    @binary_parse_function.setter
    def binary_parse_function(self, binary_parse_function):
        if not isinstance(binary_parse_function, __class__.BinaryParseFunction):
            raise TypeError('Invalid type ({}) for binary_parse_function'.format(type(binary_parse_function)))
        self._binary_parse_function = binary_parse_function

    @property
    def strip_cr(self):
        '''
        Boolean: when true, CR are stripped from the end of every line when found
        '''
        return self._strip_cr

    @strip_cr.setter
    def strip_cr(self, strip_cr):
        self._strip_cr = strip_cr

    @property
    def before_context_count(self):
        '''
        Integer: number of lines of context to print before a match
        '''
        return self._before_context_count

    @before_context_count.setter
    def before_context_count(self, before_context_count):
        self._before_context_count = before_context_count

    @property
    def after_context_count(self):
        '''
        Integer: number of lines of context to print after a match
        '''
        return self._after_context_count

    @after_context_count.setter
    def after_context_count(self, after_context_count):
        self._after_context_count = after_context_count

    @property
    def print_matching_files_only(self):
        '''
        Boolean: when true, only the file name of matching files are printed
        '''
        return self._print_matching_files_only

    @print_matching_files_only.setter
    def print_matching_files_only(self, print_matching_files_only):
        self._print_matching_files_only = print_matching_files_only

    @property
    def print_non_matching_files_only(self):
        '''
        Boolean: when true, only the file name of non-matching files are printed
        '''
        return self._print_non_matching_files_only

    @print_non_matching_files_only.setter
    def print_non_matching_files_only(self, print_non_matching_files_only):
        self._print_non_matching_files_only = print_non_matching_files_only

    @property
    def print_count_only(self):
        '''
        Boolean: when true, only count of number of matches for each file is printed
        '''
        return self._print_count_only

    @print_count_only.setter
    def print_count_only(self, print_count_only):
        self._print_count_only = print_count_only

    @staticmethod
    def _generate_color_dict():
        grep_color_dict = dict(DEFAULT_GREP_ANSI_COLORS)
        if 'GREP_COLORS' in os.environ:
            colors = os.environ['GREP_COLORS'].split(':')
            for color in colors:
                key_val = color.split('=', maxsplit=1)
                if key_val[0] in grep_color_dict:
                    if isinstance(grep_color_dict[key_val[0]], bool):
                        # Set the value to True when specified at all
                        grep_color_dict[key_val[0]] = True
                    elif len(key_val) == 2:
                        # The string must be integers separated by semicolon
                        is_valid = True
                        for item in key_val[1].split(';'):
                            try:
                                _ = int(item)
                            except ValueError:
                                is_valid = False
                                break
                        if is_valid:
                            grep_color_dict[key_val[0]] = key_val[1]
                        # else: value is ignored

        return grep_color_dict

    class LineParsingData:
        '''
        Holds various temporary state data in order to facilitate line parsing.
        '''
        def __init__(self):
            self.files = []
            self.line_format = ''
            self.context_sep = ''
            self.context_line_format = ''
            self.expressions = []
            self.line_ending = b'\n'
            self.ignore_case = False
            self.fixed_string_parse = False
            self.color_enabled = False
            self.matching_color = None
            self.matching_line_color = None
            self.context_line_color = None
            self.file = None
            self.file_iter = None
            self.line_data_dict = {}
            self.line = b''
            self.line_printed = False
            self.line_len = 0
            self.formatted_line = None
            self.line_slices = []
            self.line_num = 0
            self.overflow_detected = False
            self.binary_detected = False
            self.num_matches = 0
            self.something_printed = False
            self.byte_offset = 0
            self.print_fn = None
            self.binary_parse_function = Grep.BinaryParseFunction.PRINT_ERROR
            self.strip_cr = True
            self.before_context_count = 0
            self.current_before_byte_offsets = []
            self.current_before_context = []
            self.after_context_count = 0
            self.current_after_context_counter = 0

        def set_file(self, file):
            '''
            Prints any errors detected of previous file and sets the file currently being parsed
            '''
            self.current_before_byte_offsets = []
            self.current_before_context = []
            self.current_after_context_counter = 0
            self.binary_detected = False
            self.line_num = 0
            self.byte_offset = 0
            self.line_len = 0
            self.num_matches = 0
            self.file = file
            if file:
                self.line_data_dict['filename'] = AnsiString(file.name)
                self.file_iter = iter(file)
            else:
                try:
                    self.line_data_dict.pop('filename')
                except KeyError:
                    pass
                self.file_iter = None

        def next_line(self):
            '''
            Grabs the next line from the file and formats the line as necessary.
            Returns: True if line has been read or False if end of file reached.
            '''
            if self.line_num > 0 and not self.line_printed and self.before_context_count > 0:
                # Save before context
                self.current_before_context += [self.formatted_line]
                self.current_before_byte_offsets += [self.byte_offset]
                self.current_before_context = self.current_before_context[-self.before_context_count:]
                self.current_before_byte_offsets = self.current_before_byte_offsets[-self.before_context_count:]
            self.byte_offset += self.line_len
            self.line_num += 1
            self.line_printed = False
            try:
                self.line = next(self.file_iter)
            except StopIteration:
                # File is complete
                status_msgs = ''
                if (
                    self.binary_detected
                    and self.num_matches > 0
                    and self.binary_parse_function == Grep.BinaryParseFunction.PRINT_ERROR
                ):
                    status_msgs += 'binary file matches'
                if self.overflow_detected:
                    if status_msgs:
                        status_msgs += ' and'
                    status_msgs += ' line overflow detected'
                if status_msgs:
                    self.print_fn('{filename}: {status_msgs}'
                                  .format(status_msgs=status_msgs, **self.line_data_dict))
                return False

            self.line_len = len(self.line)

            # Remove the line ending if it is found
            if self.line.endswith(self.line_ending):
                self.line = self.line[:-len(self.line_ending)]
                self.overflow_detected = False
            else:
                # Only way this is acceptable is if we are done reading from file
                self.overflow_detected = not self.file.eof

            # Remove CR if ending starts with LF
            cr = b'\r'
            lf = b'\n'
            if self.line_ending.startswith(lf) and self.line.endswith(cr) and self.strip_cr:
                self.line = self.line[:-1]

            try:
                if self.binary_parse_function == Grep.BinaryParseFunction.IGNORE_DECODE_ERRORS:
                    errors='ignore'
                else:
                    errors='strict'
                str_line = self.line.decode(errors=errors)
            except UnicodeDecodeError:
                # Can't decode line
                if self.binary_parse_function == Grep.BinaryParseFunction.SKIP:
                    raise BinaryDetectedException()
                else:
                    # Note this is a bit more flexible as \x00 can be decoded by Python without error
                    self.binary_detected = True
                    self.formatted_line = AnsiString(self.line)
            else:
                # Make line lower case if fixed strings are used
                if self.ignore_case and self.fixed_string_parse:
                    str_line = str_line.lower()
                self.formatted_line = AnsiString(str_line)

            self.line_slices = []

            return True

        def _print_line(self, line_format, formatted_line, line_num, byte_offset, line_slices=[]):
            if not line_slices:
                # Default to printing the entire line
                line_slices = [slice(0, None)]
            else:
                line_slices.sort(key=lambda x: x.start)

            for line_slice in line_slices:
                if line_slice.start is not None:
                    slice_byte_offset = line_slice.start
                else:
                    slice_byte_offset = 0
                self.line_data_dict.update({
                    'num': AnsiString(str(line_num)),
                    'byte_offset': AnsiString(str(byte_offset + slice_byte_offset)),
                    'line': formatted_line[line_slice]
                })
                self.print_fn(line_format.format(**self.line_data_dict))

            self.something_printed = True

        def parse_complete(self, is_match):
            '''
            Called when parsing of line is complete.
            Inputs: is_match - True iff the current line is a match
            '''

            if is_match:
                self.num_matches += 1
                self.formatted_line.apply_formatting(self.matching_line_color, topmost=False)
            else:
                self.formatted_line.apply_formatting(self.context_line_color, topmost=False)

            if (
                (is_match or  (self.current_after_context_counter > 0))
                and not self.binary_detected
            ):
                # Print before context
                if self.current_before_context and self.something_printed:
                    self.print_fn(self.context_sep, end='')
                for i, before_line in enumerate(self.current_before_context):
                    line_num = self.line_num - len(self.current_before_context) + i
                    byte_offset = self.current_before_byte_offsets[i]
                    self._print_line(
                        self.context_line_format,
                        before_line,
                        line_num,
                        byte_offset
                    )
                self.current_before_context = []
                self.current_before_byte_offsets = []

                # Print the line
                self._print_line(
                    self.line_format if is_match else self.context_line_format,
                    self.formatted_line,
                    self.line_num,
                    self.byte_offset,
                    self.line_slices
                )

                if is_match:
                    self.current_after_context_counter = self.after_context_count
                else:
                    self.current_after_context_counter -= 1

                self.line_printed = True
            else:
                self.current_after_context_counter = 0

    def _make_file_iterable(self, path):
        return AutoInputFileIterable(path, 'rb', self.end)

    def _generate_line_format(self, grep_color_dict, name_num_sep, name_byte_sep, result_sep):
        if grep_color_dict and 'se' in grep_color_dict:
            se_color = grep_color_dict['se']
            name_num_sep = str(AnsiString(name_num_sep, se_color))
            name_byte_sep = str(AnsiString(name_byte_sep, se_color))
            result_sep = str(AnsiString(result_sep, se_color))

        line_format = ''

        output_file_name_only = (
            self._print_count_only
            or self._print_matching_files_only
            or self._print_non_matching_files_only
        )
        output_file_name = (self._output_file_name or output_file_name_only)
        output_line_numbers = (self._output_line_numbers and not output_file_name_only)
        output_byte_offset = (self._output_byte_offset and not output_file_name_only)
        output_line = (not self._print_matching_files_only and not self._print_non_matching_files_only)

        if output_file_name:
            line_format += '{filename'
            if grep_color_dict and grep_color_dict.get('fn'):
                line_format += ':[' + grep_color_dict['fn']
            line_format += '}'
            if output_line_numbers:
                line_format += name_num_sep
            elif output_byte_offset:
                line_format += name_byte_sep
            elif output_line:
                line_format += result_sep

        if output_line_numbers:
            line_format += '{num'
            if grep_color_dict and grep_color_dict.get('ln'):
                line_format += ':[' + grep_color_dict['ln']
            line_format += '}'
            if output_byte_offset:
                line_format += name_byte_sep
            elif output_line:
                line_format += result_sep

        if output_byte_offset:
            line_format += '{byte_offset'
            if grep_color_dict and grep_color_dict.get('ln'):
                line_format += ':[' + grep_color_dict['ln']
            line_format += '}'
            if output_line:
                line_format += result_sep

        if output_line:
            line_format += '{line}'
        return line_format

    def _init_line_parsing_data(self):
        '''
        Initializes line parsing data which makes up the local running state of Grep.execute().
        '''
        data = __class__.LineParsingData()

        data.ignore_case = self._ignore_case
        data.line_ending = self._end
        data.binary_parse_function = self._binary_parse_function
        data.strip_cr = self._strip_cr

        # Only apply context values if only_matching is not set
        if not self._only_matching:
            data.before_context_count = self._before_context_count
            data.after_context_count = self._after_context_count

        if self._color_output_mode == Grep.ColorOutputMode.ALWAYS:
            data.color_enabled = True
        elif self._color_output_mode == Grep.ColorOutputMode.AUTO:
            if self._print_file is None:
                data.color_enabled = sys.stdout.isatty()
            else:
                data.color_enabled = False
        else:
            data.color_enabled = False

        if not self._files:
            if (
                self.directory_handling_type == __class__.Directory.RECURSE
                or self.directory_handling_type == __class__.Directory.RECURSE_LINKS
            ):
                data.files = [self._make_file_iterable('.')]
            else:
                data.files = [StdinIterable(True, self.end, self._label)]
        else:
            data.files = [self._make_file_iterable(f) for f in self._files]

        data.expressions = self._expressions

        for i in range(len(data.expressions)):
            if self._search_type == __class__.SearchType.FIXED_STRINGS:
                if self._ignore_case:
                    data.expressions[i] = data.expressions[i].lower()
            elif self._search_type == __class__.SearchType.BASIC_REGEXP:
                # Transform basic regex string to extended
                # The only difference with basic is that escaping of some characters is inverted
                data.expressions[i] = _expression_escape_invert(data.expressions[i], '?+{}|()')

            if self._word_regexp:
                if self._search_type == __class__.SearchType.FIXED_STRINGS:
                    # Transform expression into regular expression
                    data.expressions[i] = r"\b" + re.escape(data.expressions[i]) + r"\b"
                else:
                    data.expressions[i] = r"\b" + data.expressions[i] + r"\b"
            elif self._line_regexp:
                if self._search_type == __class__.SearchType.FIXED_STRINGS:
                    # Transform expression into regular expression
                    data.expressions[i] = re.escape(data.expressions[i])
            data.expressions[i] = data.expressions[i].encode()

        if self._word_regexp or self._line_regexp:
            # Force to regex parse
            data.fixed_string_parse = False
        else:
            data.fixed_string_parse = (self._search_type == __class__.SearchType.FIXED_STRINGS)

        if data.color_enabled:
            grep_color_dict = __class__._generate_color_dict()
            data.matching_color = grep_color_dict['mt']
            if data.matching_color is None:
                if self.invert_match:
                    # I don't get this setting because matching line isn't colored in this case
                    data.matching_color = grep_color_dict['mc']
                else:
                    data.matching_color = grep_color_dict['ms']
            if grep_color_dict['rv'] and self._invert_match:
                data.matching_line_color = grep_color_dict['cx']
                data.context_line_color = grep_color_dict['sl']
            else:
                data.matching_line_color = grep_color_dict['sl']
                data.context_line_color = grep_color_dict['cx']
            data.context_sep = str(AnsiString(self._context_sep, grep_color_dict['se']))
        else:
            grep_color_dict = None
            data.matching_color = None
            data.matching_line_color = None
            data.context_line_color = None
            data.context_sep = self._context_sep

        data.line_format = self._generate_line_format(
            grep_color_dict,
            self._name_num_sep,
            self._name_byte_sep,
            self._results_sep
        )

        data.context_line_format = self._generate_line_format(
            grep_color_dict,
            self._context_name_num_sep,
            self._context_name_byte_sep,
            self._context_results_sep
        )

        if (
            not self._quiet
            and not self._print_count_only
            and not self._print_matching_files_only
            and not self._print_non_matching_files_only
        ):
            data.print_fn = lambda line, end=None : print(line, file=self._print_file, flush=self._line_buffered, end=end)
        else:
            # Do nothing on print
            data.print_fn = lambda line, end=None: None

        if self._print_count_only:
            # Force binary mode to ignore decode errors so it continues to count
            self.binary_parse_function = __class__.BinaryParseFunction.IGNORE_DECODE_ERRORS

        return data

    def _parse_line(self, data:LineParsingData):
        '''
        Parses a line from a file, formats line, and prints the line if match is found.
        '''
        match_found = False
        for expression in data.expressions:
            if match_found and not data.color_enabled and not self.only_matching:
                # No need to keep looping through expressions
                break
            elif not expression:
                # Special case: always a match on empty string, and nothing to color
                match_found = True
            elif data.fixed_string_parse:
                loc = data.line.find(expression)
                if loc >= 0:
                    match_found = True
                    if data.color_enabled or self.only_matching:
                        while loc >= 0:
                            if data.color_enabled:
                                data.formatted_line.apply_formatting(
                                    data.matching_color, loc, len(expression))
                            if self.only_matching:
                                data.line_slices.append(slice(loc, loc + len(expression)))
                            loc = data.line.find(expression, loc + len(expression))
            else:
                # Regular expression matching
                flags = 0
                if self._ignore_case:
                    flags = re.IGNORECASE
                if self._line_regexp:
                    m = re.fullmatch(expression, data.line, flags)
                    if m is not None:
                        match_found = True
                        if data.color_enabled:
                            # This is going to just format the whole line
                            data.formatted_line.apply_formatting_for_match(data.matching_color, m)
                        if self.only_matching:
                            data.line_slices.append(slice(m.start(0), m.end(0)))
                else:
                    for m in re.finditer(expression, data.line, flags):
                        match_found = True
                        if data.color_enabled:
                            data.formatted_line.apply_formatting_for_match(data.matching_color, m)
                        if self.only_matching:
                            data.line_slices.append(slice(m.start(0), m.end(0)))
        if self._invert_match:
            match_found = not match_found
        data.parse_complete(match_found)
        return match_found

    def _parse_file(self, file, data):
        file_base_name = os.path.basename(file.name)

        included = False
        for g in self._file_include_globs:
            if fnmatch.fnmatch(file_base_name, g):
                included = True
                break
        if not self._file_include_globs:
            # Default to include all when no globs provided
            included = True

        excluded = False
        for g in self._file_exclude_globs:
            if fnmatch.fnmatch(file_base_name, g):
                excluded = True
                break

        if not included or excluded:
            return False

        match_found = False

        try:
            data.set_file(file)
        except EnvironmentError as ex:
            # This occurs if permission is denied
            if not self._no_messages:
                print('{}: {}'.format(PACKAGE_NAME, str(ex)), file=sys.stderr)
        else:
            try:
                while data.next_line() and (self._max_count is None or data.num_matches < self._max_count):
                    if self._parse_line(data):
                        match_found = True
                if (
                    (self._print_matching_files_only and match_found)
                    or (self._print_non_matching_files_only and not match_found)
                ):
                    print(
                        data.line_format.format(**data.line_data_dict),
                        file=self._print_file,
                        flush=self._line_buffered
                    )
                elif self._print_count_only:
                    data.line_data_dict.update({
                        'num': AnsiString(''),
                        'byte_offset': AnsiString(''),
                        'line': data.num_matches
                    })
                    print(
                        data.line_format.format(**data.line_data_dict),
                        file=self._print_file,
                        flush=self._line_buffered
                    )
            except BinaryDetectedException:
                pass # Skip the rest of the file and continue
        return match_found

    def _is_excluded_dir(self, dir_path):
        exclude = False
        base_name = os.path.basename(os.path.normpath(dir_path))
        for g in self._dir_exclude_globs:
            if fnmatch.fnmatch(base_name, g):
                exclude = True
                break
        return exclude

    def execute(self):
        '''
        Executes Grep with all the assigned attributes.
        Returns: a list of files with matches
        '''
        if not self._expressions:
            print('No expressions provided', file=sys.stderr)
            return None

        data = self._init_line_parsing_data()
        matched_files = []

        for file in data.files:
            if os.path.isdir(file.name):
                if not self._is_excluded_dir(file.name):
                    if self._directory_handling_type == __class__.Directory.READ:
                        print('{}: {}: Is a directory'.format(PACKAGE_NAME, file.name))
                    elif (
                        self._directory_handling_type == __class__.Directory.RECURSE
                        or self._directory_handling_type == __class__.Directory.RECURSE_LINKS
                    ):
                        followlinks = (self._directory_handling_type == __class__.Directory.RECURSE_LINKS)
                        for root, dirs, recurse_files in os.walk(file.name, followlinks=followlinks):
                            if not self._is_excluded_dir(root):
                                for recurse_file in recurse_files:
                                    file_path = os.path.join(root, recurse_file)
                                    if self._parse_file(self._make_file_iterable(file_path), data):
                                        matched_files += [file_path]
                            else:
                                # Do nothing and exclude anything that follows
                                dirs[:] = []
            else:
                if self._parse_file(file, data):
                    matched_files += [file.name]

        return matched_files

class GrepArgParser:
    '''
    Used to parse command line arguments for Grep.
    '''
    def __init__(self):
        self._parser = argparse.ArgumentParser(
            prog=PACKAGE_NAME,
            description='Reimplementation of grep command entirely in Python.',
            add_help=False)
        self._parser.register('action', 'extend', __class__.ExtendArgparseAction)

        self._parser.add_argument('expressions_positional', type=str, nargs='?', default=None, metavar='EXPRESSIONS',
                            help='Expressions to search for, separated by newline character (\\n). '
                            'This is required if --regexp or --file are not specified.')
        self._parser.add_argument('file', type=str, nargs='*', default=[], metavar='FILE',
                            help='Files or directories to search. Stdin will be searched if not specified, '
                            ' unless -r is specified. Then current directory will be recursively searched.'
                            'How directories are handled is controlled by -d and -r options.')

        regexp_group = self._parser.add_argument_group('Expression Interpretation')
        regexp_type = regexp_group.add_mutually_exclusive_group()
        regexp_type.add_argument('-E', '--extended-regexp', action='store_true',
                                help='EXPRESSIONS are "extended" regular expressions.\n'
                                'In this mode, greplica passes regular expressions directly to Python re '
                                'without modification. This for the most part matches original "extended" '
                                'syntax, but be aware that there may be differences.')
        regexp_type.add_argument('-F', '--fixed-strings', action='store_true',
                                help='EXPRESSIONS are strings')
        regexp_type.add_argument('-G', '--basic-regexp', action='store_true',
                                help='EXPRESSIONS are "basic" regular expressions.\n'
                                'In this mode, greplica modifies escaping sequences for characters ?+{}|() '
                                'before passing to Python re. This for the most part matches original "basic" '
                                'syntax, but be aware that there may be differences.')
        regexp_group.add_argument('-e', '--regexp', dest='expressions_option', metavar='EXPRESSIONS', type=str,
                                default=None,
                                help='use EXPRESSIONS for matching')
        regexp_group.add_argument('-f', '--file', metavar='FILE', dest='expressions_file', nargs='+',
                                  action='extend', default=[], type=str,
                                  help='take EXPRESSIONS from FILE')
        regexp_group.add_argument('-i', '--ignore-case', action='store_true',
                                help='ignore case in expressions')
        regexp_group.add_argument('--no-ignore-case', dest='ignore_case', action='store_false',
                                help='do not ignore case (default)')
        regexp_group.add_argument('-w', '--word-regexp', action='store_true',
                                help='match whole words only')
        regexp_group.add_argument('-x', '--line-regexp', action='store_true',
                                help='match whole lines only')
        regexp_group.add_argument('--end', type=str, default='\n',
                                   help='newline character lines will be parsed by (default: \\n)')
        regexp_group.add_argument('-z', '--null-data', action='store_true',
                                   help='same as --end=\'\\0\'')

        misc_group = self._parser.add_argument_group('Miscellaneous')
        misc_group.add_argument('-s', '--no-messages', action='store_true', help='suppress error messages')
        misc_group.add_argument('-v', '--invert-match', action='store_true', help='select non-matching lines')
        misc_group.add_argument('-V', '--version', action='store_true', help='display version information and exit')
        misc_group.add_argument('--help', action='help', help='display this help text and exit')

        output_ctrl_grp = self._parser.add_argument_group('Output control')
        output_ctrl_grp.add_argument('-m', '--max-count', metavar='NUM', type=int, default=None,
                                     help='stop after NUM lines')
        output_ctrl_grp.add_argument('-b', '--byte-offset', action='store_true',
                                     help='print line\'s byte offset with each line')
        output_ctrl_grp.add_argument('-n', '--line-number', action='store_true', help='print line number with each line')
        output_ctrl_grp.add_argument('--line-buffered', action='store_true', help='flush output on each line')
        output_ctrl_grp.add_argument('-H', '--with-filename', action='store_true', help='print file name with each line')
        output_ctrl_grp.add_argument('-h', '--no-filename', action='store_true', help='suppress the file name output')
        output_ctrl_grp.add_argument('--label', type=str, metavar='LABEL', default='(standard input)',
                                     help='use LABEL as the standard input file name')
        output_ctrl_grp.add_argument('-o', '--only-matching', action='store_true', help='show only nonempty parts of lines that match')
        output_ctrl_grp.add_argument('-q', '--quiet', '--silent', action='store_true', help='suppress all normal output')
        output_ctrl_grp.add_argument('--binary-files', type=str, metavar='TYPE', default='binary',
                                     choices=['binary', 'text', 'without-match'],
                                     help='sets how binary file is parsed;\n'
                                     'TYPE is \'binary\', \'text\', or \'without-match\'')
        output_ctrl_grp.add_argument('-a', '--text', action='store_true', help='same as --binary-files=text')
        output_ctrl_grp.add_argument('-I', dest='binary_without_match', action='store_true',
                                     help='same as --binary-files=without-match')
        output_ctrl_grp.add_argument('-d', '--directories', type=str, metavar='ACTION', default='read',
                                     choices=['read', 'recurse', 'skip', 'recurse_links'],
                                     help='controls how directory input is handled in FILE;\n'
                                     'ACTION is \'read\', \'recurse\', or \'skip\'')
        output_ctrl_grp.add_argument('-r', '--recursive', action='store_true', help='same as --directories=recurse')
        output_ctrl_grp.add_argument('-R', '--dereference-recursive', action='store_true', help='same as --directories=recurse_links')
        output_ctrl_grp.add_argument('--include', type=str, nargs='+', metavar='GLOB', action='extend', default=[],
                                     help='limit files to those matching GLOB')
        output_ctrl_grp.add_argument('--exclude', type=str, nargs='+', metavar='GLOB', action='extend', default=[],
                                     help='skip files that match GLOB')
        output_ctrl_grp.add_argument('--exclude-from', type=str, nargs='+', metavar='FILE', action='extend', default=[],
                                     help='read FILE for exclude globs file name globs')
        output_ctrl_grp.add_argument('--exclude-dir', type=str, nargs='+', metavar='GLOB', action='extend', default=[],
                                     help='skip directories that match GLOB')
        output_ctrl_grp.add_argument('-L', '--files-without-match', action='store_true', help='print only names of FILEs with no selected lines')
        output_ctrl_grp.add_argument('-l', '--files-with-matches', action='store_true', help='print only names of FILEs with selected lines')
        output_ctrl_grp.add_argument('-c', '--count', action='store_true', help='print only a count of selected lines per FILE')
        # TODO: fix the below feature
        output_ctrl_grp.add_argument('-T', '--initial-tab', action='store_true',
                                     help='currently just adds tabs to each sep value (will make better later)')
        output_ctrl_grp.add_argument('-Z', '--null', action='store_true', help='adds 0 to the end of result-sep')
        output_ctrl_grp.add_argument('--result-sep', type=str, metavar='SEP', default=':',
                                    help='String to place between header info and and search output')
        output_ctrl_grp.add_argument('--name-num-sep', type=str, metavar='SEP', default=':',
                                    help='String to place between file name and line number when both are enabled')
        output_ctrl_grp.add_argument('--name-byte-sep', type=str, metavar='SEP', default=':',
                                    help='String to place between file name and byte number when both are enabled')
        output_ctrl_grp.add_argument('--context-group-sep', type=str, metavar='SEP', default='--\n',
                                    help='String to print between context groups')
        output_ctrl_grp.add_argument('--context-result-sep', type=str, metavar='SEP', default='-',
                                    help='String to place between header info and context line')
        output_ctrl_grp.add_argument('--context-name-num-sep', type=str, metavar='SEP', default='-',
                                    help='String to place between file name and line number on context line')
        output_ctrl_grp.add_argument('--context-name-byte-sep', type=str, metavar='SEP', default='-',
                                    help='String to place between file name and byte number on context line')

        context_ctrl_grp = self._parser.add_argument_group('Context Control')
        context_ctrl_grp.add_argument('-B', '--before-context', type=int, default=None, metavar='NUM',
                                      help='print NUM lines of leading context')
        context_ctrl_grp.add_argument('-A', '--after-context', type=int, default=None, metavar='NUM',
                                      help='print NUM lines of trailing context')
        context_ctrl_grp.add_argument('-C', '--context', type=int, default=None, metavar='NUM',
                                      help='print NUM lines of output context')
        context_ctrl_grp.add_argument('--color', '--colour', type=str, metavar='WHEN', nargs='?', default='auto', dest='color',
                                    choices=['always', 'never', 'auto'],
                                    help='use ANSI escape codes to highlight the matching strings;\n'
                                    'WHEN is \'always\', \'never\', or \'auto\'')
        context_ctrl_grp.add_argument('-U', '--binary', action='store_true', help='do not strip CR characters at EOL (MSDOS/Windows)')

        self._args = None

    class ExtendArgparseAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest, [])
            items.extend(values)
            setattr(namespace, self.dest, items)

    @staticmethod
    def _is_windows():
        return sys.platform.lower().startswith('win')

    def _expand_cli_path(self, path):
        if __class__._is_windows() and '*' in path or '?' in path:
            # Need to manually expand this out
            expanded_paths = [f for f in glob.glob(path)]
            if not expanded_paths:
                if not self._args.no_messages:
                    print('No match for: {}'.format(path), file=sys.stderr)
        else:
            # *nix and *nix based systems do this from command line
            expanded_paths = [path]
        return expanded_paths

    def _expand_cli_paths(self, paths):
        return [y for x in paths for y in self._expand_cli_path(x)]

    def parse(self, cliargs, grep_object:Grep):
        '''
        Parses command line arguments into the given Grep object
        '''
        grep_object.reset()
        self._args = self._parser.parse_args(cliargs)

        if not self._args:
            return False

        if self._args.version:
            print('{} {}'.format(PACKAGE_NAME, __version__))
            sys.exit(0)

        # Pars expressions from all of the different options into a single list of expressions
        expressions = []
        if self._args.expressions_option is not None:
            # Set expressions to the option
            expressions.extend(_parse_expressions(self._args.expressions_option))
            # The first positional (expressions_positional) is a file
            if self._args.expressions_positional is not None:
                self._args.file.insert(0, self._args.expressions_positional)
        elif self._args.expressions_file:
            for file in self._args.expressions_file:
                try:
                    with open(file, 'r') as fp:
                        expressions.extend(_parse_expressions(fp.read()))
                except EnvironmentError as ex:
                    if not self._args.no_messages:
                        print('{}: {}'.format(PACKAGE_NAME, str(ex)), file=sys.stderr)
            # The first positional (expressions_positional) is a file
            if self._args.expressions_positional is not None:
                self._args.file.insert(0, self._args.expressions_positional)
        elif self._args.expressions_positional is not None:
            # Set expressions to the positional
            expressions.extend(_parse_expressions(self._args.expressions_positional))

        if not expressions:
            self._parser.print_usage()
            print('Try --help for more information', file=sys.stderr)
            return False

        grep_object.add_expression(expressions)

        if self._args.file:
            grep_object.add_files(self._expand_cli_paths(self._args.file))

        if self._args.extended_regexp:
            grep_object.search_type = Grep.SearchType.EXTENDED_REGEXP
        elif self._args.fixed_strings:
            grep_object.search_type = Grep.SearchType.FIXED_STRINGS
        else:
            # Basic regexp is default if no type specified
            grep_object.search_type = Grep.SearchType.BASIC_REGEXP

        grep_object.ignore_case = self._args.ignore_case
        grep_object.word_regexp = self._args.word_regexp
        grep_object.line_regexp = self._args.line_regexp
        grep_object.no_messages = self._args.no_messages
        grep_object.invert_match = self._args.invert_match
        grep_object.max_count = self._args.max_count
        grep_object.output_line_numbers = self._args.line_number
        grep_object.output_file_name = self._args.with_filename
        grep_object.output_byte_offset = self._args.byte_offset
        grep_object.line_buffered = self._args.line_buffered
        grep_object.label = self._args.label
        grep_object.quiet = self._args.quiet
        grep_object.only_matching = self._args.only_matching
        grep_object.strip_cr = not self._args.binary
        grep_object.print_matching_files_only = self._args.files_with_matches
        grep_object.print_non_matching_files_only = self._args.files_without_match
        grep_object.print_count_only = self._args.count

        if self._args.context is not None:
            grep_object.before_context_count = self._args.context
            grep_object.after_context_count = self._args.context
        else:
            if self._args.before_context is not None:
                grep_object.before_context_count = self._args.before_context
            if self._args.after_context is not None:
                grep_object.after_context_count = self._args.after_context

        if self._args.recursive or self._args.directories == 'recurse':
            grep_object.directory_handling_type = Grep.Directory.RECURSE
            if not self._args.no_filename:
                # Force output of file name
                grep_object.output_file_name = True
        elif self._args.dereference_recursive or self._args.directories == 'recurse_links':
            grep_object.directory_handling_type = Grep.Directory.RECURSE_LINKS
            if not self._args.no_filename:
                # Force output of file name
                grep_object.output_file_name = True
        elif self._args.directories == 'skip':
            grep_object.directory_handling_type = Grep.Directory.SKIP
        else:
            grep_object.directory_handling_type = Grep.Directory.READ

        if self._args.null_data:
            grep_object.end = b'\x00'
        else:
            grep_object.end = bytes(self._args.end, "utf-8").decode("unicode_escape")

        grep_object.results_sep = bytes(self._args.result_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.results_sep += '\t'
        if self._args.null:
            grep_object.results_sep += '\0'
        grep_object.name_num_sep = bytes(self._args.name_num_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.name_num_sep += '\t'
        grep_object.name_byte_sep = bytes(self._args.name_byte_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.name_byte_sep += '\t'

        grep_object.context_sep = bytes(self._args.context_group_sep, "utf-8").decode("unicode_escape")
        grep_object.context_results_sep = bytes(self._args.context_result_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.context_results_sep += '\t'
        if self._args.null:
            grep_object.context_results_sep += '\0'
        grep_object.context_name_num_sep = bytes(self._args.context_name_num_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.context_name_num_sep += '\t'
        grep_object.context_name_byte_sep = bytes(self._args.context_name_byte_sep, "utf-8").decode("unicode_escape")
        if self._args.initial_tab:
            grep_object.context_name_byte_sep += '\t'

        if self._args.color == 'always':
            grep_object.color_output_mode = Grep.ColorOutputMode.ALWAYS
        elif self._args.color == 'never':
            grep_object.color_output_mode = Grep.ColorOutputMode.NEVER
        else:
            grep_object.color_output_mode = Grep.ColorOutputMode.AUTO

        if self._args.binary_files == 'text' or self._args.text:
            grep_object.binary_parse_function = Grep.BinaryParseFunction.IGNORE_DECODE_ERRORS
        elif self._args.binary_files == 'without-match' or self._args.binary_without_match:
            grep_object.binary_parse_function = Grep.BinaryParseFunction.SKIP
        else:
            grep_object.binary_parse_function = Grep.BinaryParseFunction.PRINT_ERROR

        grep_object.add_file_include_globs(self._args.include)
        grep_object.add_file_exclude_globs(self._args.exclude)

        for exclude_file in self._expand_cli_paths(self._args.exclude_from):
            try:
                with open(exclude_file, 'r') as fp:
                    for line in fp.readlines():
                        if line.endswith('\n'):
                            line = line[:-1]
                        if line.endswith('\r'):
                            line = line[:-1]
                        grep_object.add_file_exclude_globs(line)
            except EnvironmentError as ex:
                if not self._args.no_messages:
                    print('{}: {}'.format(PACKAGE_NAME, str(ex)), file=sys.stderr)

        grep_object.add_dir_exclude_globs(self._args.exclude_dir)

        return True

def main(cliargs):
    '''
    Performs Grep with given command line arguments
    Returns: 0 on success, non-zero integer on failure
    '''
    grep = Grep()
    grep_arg_parser = GrepArgParser()
    if not grep_arg_parser.parse(cliargs, grep):
        return 1
    else:
        matched_files = grep.execute()
        if matched_files is not None:
            return 0
        else:
            return 1
