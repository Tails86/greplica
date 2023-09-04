#!/usr/bin/env python3

import os
import sys
import unittest
from io import BytesIO, StringIO
from unittest.mock import patch
import tempfile

THIS_FILE_PATH = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
PROJECT_DIR = os.path.abspath(os.path.join(THIS_FILE_PATH, '..'))
SOURCE_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'src'))

sys.path.insert(0, SOURCE_DIR)
from greplica import grep

test_file1 = '''Up am intention on dependent questions oh elsewhere september.
No betrayed pleasure possible jointure we in throwing
And can event rapid any shall woman green.
Hope they dear who .* its bred.
Smiling nothing affixed he carried it clothes calling he no.
Its something disposing departure she favorite tolerably engrossed.
Truth short folly court why she their balls.
Excellence put unaffected reasonable mrs introduced conviction she.
Nay particular delightful but unpleasant for uncommonly who.'''

test_file2 = '''Ladyship it daughter securing procured or am moreover mr.
Put sir she exercise vicinity cheerful wondered.
Continual say suspicion provision he neglected sir curiosity unwilling.
Simplicity end themselves increasing led day sympathize yet.
General windows effects not are drawing man garrets.
Common indeed garden you his ladies out yet.
Preference imprudence contrasted to remarkably in on.\x00
Taken now you him trees tears any.
Her object giving end sister except oppose.'''

test_file3 = '''Looking started he up perhaps against.
How remainder all additions get elsewhere resources.
One missed shy wishes supply design answer formed.
Prevent on present hastily passage an subject in be.
Be happiness arranging so newspaper defective affection ye.
Families blessing he in to no daughter.'''

test_file4 = '''Egestas purus viverra accumsan in nisl nisi.
Amet nisl suscipit adipiscing bibendum est ultricies integer quis auctor.
Dictum non consectetur a erat nam at.
Praesent elementum facilisis leo vel fringilla est ullamcorper.
Mauris augue neque gravida in fermentum.
Mi sit amet mauris commodo quis imperdiet.
Amet volutpat consequat mauris nunc.
Ut diam quam nulla porttitor massa id neque aliquam vestibulum.
Donec enim diam vulputate ut pharetra sit amet aliquam id.
Proin libero nunc consequat interdum varius sit amet mattis.
Facilisis magna etiam tempor orci eu lobortis.
Lobortis scelerisque fermentum dui faucibus in ornare quam.
Ut etiam sit amet nisl purus in mollis nunc sed.'''

class FakeStdIn:
    def __init__(self, loaded_str):
        if isinstance(loaded_str, str):
            loaded_str = loaded_str.encode()
        self.buffer = BytesIO(loaded_str)

class FakeStdOut:
    def __init__(self, isatty=True):
        self._isatty = isatty
        self._real_buffer = StringIO()
        self.flush_count = 0
        self.write = self._real_buffer.write
        self.read = self._real_buffer.read
        self.close = self._real_buffer.close
        self.fileno = self._real_buffer.fileno
        self.getvalue = self._real_buffer.getvalue

    def flush(self):
        self._real_buffer.flush()
        self.flush_count += 1

    def isatty(self):
        return self._isatty

class PermissionErrorMockAutoInputFileIterable(grep.AutoInputFileIterable):
    def __iter__(self):
        raise EnvironmentError(f"[Errno 13] Permission denied: '{self.name}'")

def _is_windows():
    return sys.platform.lower().startswith('win')

class GrepTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        with open(os.path.join(cls.tmpdir.name, "file1.txt"), "wb") as fd:
            fd.write(test_file1.encode())
        with open(os.path.join(cls.tmpdir.name, "file2.txt"), "wb") as fd:
            fd.write(test_file2.encode())
        with open(os.path.join(cls.tmpdir.name, "file3.txt"), "wb") as fd:
            fd.write(test_file3.encode())
        with open(os.path.join(cls.tmpdir.name, "file4.txt"), "wb") as fd:
            fd.write(test_file4.encode())
        with open(os.path.join(cls.tmpdir.name, "patterns.txt"), "wb") as fd:
            fd.write(b'glue\nkelp\ntrash\ntree\nneglect')
        with open(os.path.join(cls.tmpdir.name, "globfile.txt"), "wb") as fd:
            fd.write(b'*1.txt\n\n\n')

    def setUp(self):
        self.old_dir = os.getcwd()
        os.chdir(self.tmpdir.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def tearDown(self):
        os.chdir(self.old_dir)

    def test_match_empty_line(self):
        os.environ['GREP_COLORS'] = ''
        with patch('greplica.grep.sys.stdout', new = StringIO()), \
            patch('greplica.grep.sys.stdin', FakeStdIn('abc\n\ndef')) \
        :
            # This will cause a match of length 0 and try to color it
            # This would previously cause an exception
            grep.main(['--color=always', '-E', '^.*$', 'file1.txt', 'file2.txt'])

    def test_search_no_color(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'any', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'And can event rapid any shall woman green.')
        self.assertEqual(lines[1], 'Taken now you him trees tears any.')
        self.assertEqual(lines[2], '')

    def test_search_color(self):
        os.environ['GREP_COLORS'] = '' # Use default colors
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=always', 'yet', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Simplicity end themselves increasing led day sympathize \x1b[01;31myet\x1b[m.')
        self.assertEqual(lines[1], 'Common indeed garden you his ladies out \x1b[01;31myet\x1b[m.')
        self.assertEqual(lines[2], '')

    def test_search_color_filename_numbers_context(self):
        os.environ['GREP_COLORS'] = '' # Use default colors
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=always', 'yet', 'file1.txt', 'file2.txt', '-Hnb', '-B', '1'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines,[
            '\x1b[35mfile2.txt\x1b[m\x1b[36m-\x1b[m\x1b[32m3\x1b[m\x1b[36m-\x1b[m\x1b[32m107\x1b[m\x1b[36m-\x1b[m'
                'Continual say suspicion provision he neglected sir curiosity unwilling.',
            '\x1b[35mfile2.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m4\x1b[m\x1b[36m:\x1b[m\x1b[32m179\x1b[m\x1b[36m:\x1b[m'
                'Simplicity end themselves increasing led day sympathize \x1b[01;31myet\x1b[m.',
            '\x1b[36m--',
            '\x1b[m\x1b[35mfile2.txt\x1b[m\x1b[36m-\x1b[m\x1b[32m5\x1b[m\x1b[36m-\x1b[m\x1b[32m240\x1b[m\x1b[36m-\x1b[m'
                'General windows effects not are drawing man garrets.',
            '\x1b[35mfile2.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m6\x1b[m\x1b[36m:\x1b[m\x1b[32m293\x1b[m\x1b[36m:\x1b[m'
                'Common indeed garden you his ladies out \x1b[01;31myet\x1b[m.',
            ''
        ])

    def test_search_color_filename_numbers_context_environment(self):
        os.environ['GREP_COLORS'] = 'ms=03;33:mc=04;34:sl=35:cx=41:rv:fn=42:ln=43:bn=44:se=45:ne'
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=always', 'their', 'file1.txt', '-Hnbv', '-C', '3'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines,[
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m1\x1b[m\x1b[45m:\x1b[m\x1b[43m0\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Up am intention on dependent questions oh elsewhere september.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m2\x1b[m\x1b[45m:\x1b[m\x1b[43m63\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'No betrayed pleasure possible jointure we in throwing\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m3\x1b[m\x1b[45m:\x1b[m\x1b[43m117\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'And can event rapid any shall woman green.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m4\x1b[m\x1b[45m:\x1b[m\x1b[43m160\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Hope they dear who .* its bred.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m5\x1b[m\x1b[45m:\x1b[m\x1b[43m192\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Smiling nothing affixed he carried it clothes calling he no.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m6\x1b[m\x1b[45m:\x1b[m\x1b[43m253\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Its something disposing departure she favorite tolerably engrossed.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m-\x1b[m\x1b[43m7\x1b[m\x1b[45m-\x1b[m\x1b[43m321\x1b[m\x1b[45m-\x1b[m\x1b[35m'
                'Truth short folly court why she \x1b[35;04;34mtheir\x1b[0;35m balls.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m8\x1b[m\x1b[45m:\x1b[m\x1b[43m366\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Excellence put unaffected reasonable mrs introduced conviction she.\x1b[m',
            '\x1b[42mfile1.txt\x1b[m\x1b[45m:\x1b[m\x1b[43m9\x1b[m\x1b[45m:\x1b[m\x1b[43m434\x1b[m\x1b[45m:\x1b[m\x1b[41m'
                'Nay particular delightful but unpleasant for uncommonly who.\x1b[m',
            ''
        ])

    def test_search_color_filename_numbers_context_environment_mt(self):
        os.environ['GREP_COLORS'] = 'mt=03;33'
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=always', 'their', 'file1.txt', '-Hnbv', '-C', '3'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines,[
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m1\x1b[m\x1b[36m:\x1b[m\x1b[32m0\x1b[m\x1b[36m:\x1b[m'
                'Up am intention on dependent questions oh elsewhere september.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m2\x1b[m\x1b[36m:\x1b[m\x1b[32m63\x1b[m\x1b[36m:\x1b[m'
                'No betrayed pleasure possible jointure we in throwing',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m3\x1b[m\x1b[36m:\x1b[m\x1b[32m117\x1b[m\x1b[36m:\x1b[m'
                'And can event rapid any shall woman green.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m4\x1b[m\x1b[36m:\x1b[m\x1b[32m160\x1b[m\x1b[36m:\x1b[m'
                'Hope they dear who .* its bred.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m5\x1b[m\x1b[36m:\x1b[m\x1b[32m192\x1b[m\x1b[36m:\x1b[m'
                'Smiling nothing affixed he carried it clothes calling he no.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m6\x1b[m\x1b[36m:\x1b[m\x1b[32m253\x1b[m\x1b[36m:\x1b[m'
                'Its something disposing departure she favorite tolerably engrossed.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m-\x1b[m\x1b[32m7\x1b[m\x1b[36m-\x1b[m\x1b[32m321\x1b[m\x1b[36m-\x1b[m'
                'Truth short folly court why she \x1b[03;33mtheir\x1b[m balls.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m8\x1b[m\x1b[36m:\x1b[m\x1b[32m366\x1b[m\x1b[36m:\x1b[m'
                'Excellence put unaffected reasonable mrs introduced conviction she.',
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m9\x1b[m\x1b[36m:\x1b[m\x1b[32m434\x1b[m\x1b[36m:\x1b[m'
                'Nay particular delightful but unpleasant for uncommonly who.',
            ''
        ])

    def test_search_auto_color_and_isatty(self):
        os.environ['GREP_COLORS'] = '' # Use default colors
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(True)) as fake_out:
            grep.main(['--color=auto', 'yet', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Simplicity end themselves increasing led day sympathize \x1b[01;31myet\x1b[m.')
        self.assertEqual(lines[1], 'Common indeed garden you his ladies out \x1b[01;31myet\x1b[m.')
        self.assertEqual(lines[2], '')

    def test_search_auto_color_and_not_isatty(self):
        os.environ['GREP_COLORS'] = '' # Use default colors
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(False)) as fake_out:
            grep.main(['--color=auto', 'yet', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Simplicity end themselves increasing led day sympathize yet.')
        self.assertEqual(lines[1], 'Common indeed garden you his ladies out yet.')
        self.assertEqual(lines[2], '')

    def test_search_from_stdin(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn(test_file1)) \
        :
            grep.main(['--color=never', 'any'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'And can event rapid any shall woman green.')
        self.assertEqual(lines[1], '')

    def test_extended_regex(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-E', '(is.*she)|(she.*is)', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Its something disposing departure she favorite tolerably engrossed.')
        self.assertEqual(lines[1], 'Put sir she exercise vicinity cheerful wondered.')
        self.assertEqual(lines[2], '')

    def test_perl_regex(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-P', '(is.*she)|(she.*is)', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Its something disposing departure she favorite tolerably engrossed.')
        self.assertEqual(lines[1], 'Put sir she exercise vicinity cheerful wondered.')
        self.assertEqual(lines[2], '')

    def test_fixed_strings(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-F', '.*', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'Hope they dear who .* its bred.')
        self.assertEqual(lines[1], '')

    def test_basic_regex(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-G', '\(sir.*he\)\|\(he.*sir\)', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Put sir she exercise vicinity cheerful wondered.')
        self.assertEqual(lines[1], 'Continual say suspicion provision he neglected sir curiosity unwilling.')
        self.assertEqual(lines[2], '')

    def test_pattern_file_option(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-f', 'patterns.txt', '--', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Continual say suspicion provision he neglected sir curiosity unwilling.')
        self.assertEqual(lines[1], 'Taken now you him trees tears any.')
        self.assertEqual(lines[2], '')

    def test_pattern_file_not_found_error(self):
        with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
            patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
        :
            grep.main(['--color=never', '-f', 'abcd.txt', '--', 'file1.txt', 'file2.txt'])
            err_text = fake_err.getvalue()
        self.assertIn("greplica: [Errno 2] No such file or directory: 'abcd.txt'", err_text)

    def test_pattern_file_not_found_error_suppressed(self):
        with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
            patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
        :
            grep.main(['--color=never', '--no-messages', '-f', 'abcd.txt', '--', 'file1.txt', 'file2.txt'])
            err_text = fake_err.getvalue()
        self.assertNotIn("greplica: [Errno 2] No such file or directory: 'abcd.txt'", err_text)

    def test_ignore_case(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-i', 'Am', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Up am intention on dependent questions oh elsewhere september.')
        self.assertEqual(lines[1], 'Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[2], '')

    def test_no_ignore_case(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '--no-ignore-case', 'Am', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '')

    def test_whole_words(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '-w', 'man', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'General windows effects not are drawing man garrets.')
        self.assertEqual(lines[1], '')

    def test_line_regex_no_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-xE', 'clothes', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '')

    def test_line_regex_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-xE', '.*clothes calling he no.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'Smiling nothing affixed he carried it clothes calling he no.')
        self.assertEqual(lines[1], '')

    def test_null_data(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-z', 'trees', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], '')
        self.assertEqual(lines[1], 'Taken now you him trees tears any.')
        self.assertEqual(lines[2], 'Her object giving end sister except oppose.')
        self.assertEqual(lines[3], '')

    def test_invert_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-vF', '.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'No betrayed pleasure possible jointure we in throwing')
        self.assertEqual(lines[1], '')

    def test_max_num(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-F', '.', 'file1.txt', 'file2.txt', '-m', '5'])
            lines = fake_out.getvalue().split('\n')
        # 5 from each file plus trailing newline
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[0], 'Up am intention on dependent questions oh elsewhere september.')
        self.assertEqual(lines[1], 'And can event rapid any shall woman green.')
        self.assertEqual(lines[2], 'Hope they dear who .* its bred.')
        self.assertEqual(lines[3], 'Smiling nothing affixed he carried it clothes calling he no.')
        self.assertEqual(lines[4], 'Its something disposing departure she favorite tolerably engrossed.')
        self.assertEqual(lines[5], 'Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[6], 'Put sir she exercise vicinity cheerful wondered.')
        self.assertEqual(lines[7], 'Continual say suspicion provision he neglected sir curiosity unwilling.')
        self.assertEqual(lines[8], 'Simplicity end themselves increasing led day sympathize yet.')
        self.assertEqual(lines[9], 'General windows effects not are drawing man garrets.')
        self.assertEqual(lines[10], '')

    def test_byte_offset(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'mr', 'file1.txt', 'file2.txt', '-b'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '366:Excellence put unaffected reasonable mrs introduced conviction she.')
        self.assertEqual(lines[1], '0:Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[2], '')

    def test_line_number(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'mr', 'file1.txt', 'file2.txt', '-n'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '8:Excellence put unaffected reasonable mrs introduced conviction she.')
        self.assertEqual(lines[1], '1:Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[2], '')

    def test_line_buffered(self):
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(True)) as fake_out:
            grep.main(['--color=never', '.', 'file1.txt', 'file2.txt', '--line-buffered'])
            lines = fake_out.getvalue().split('\n')
            flush_count = fake_out.flush_count
        self.assertEqual(len(lines), 19)
        self.assertEqual(flush_count, 18)

    def test_not_line_buffered(self):
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(True)) as fake_out:
            grep.main(['--color=never', '.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
            flush_count = fake_out.flush_count
        self.assertEqual(len(lines), 19)
        self.assertEqual(flush_count, 0)

    def test_with_filename(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'any', 'file1.txt', 'file2.txt', '-H'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'file1.txt:And can event rapid any shall woman green.')
        self.assertEqual(lines[1], 'file2.txt:Taken now you him trees tears any.')
        self.assertEqual(lines[2], '')

    def test_with_no_filename(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'any', '-r', '-h'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'And can event rapid any shall woman green.')
        self.assertEqual(lines[1], 'Taken now you him trees tears any.')
        self.assertEqual(lines[2], '')

    def test_stdin_custom_label(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn(test_file1)) \
        :
            grep.main(['--color=never', '-H', '--label', 'CuStOmLaBeL', 'delightful'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'CuStOmLaBeL:Nay particular delightful but unpleasant for uncommonly who.')
        self.assertEqual(lines[1], '')

    def test_stdin_default_label(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn(test_file1)) \
        :
            grep.main(['--color=never', '-H', 'delightful'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '(standard input):Nay particular delightful but unpleasant for uncommonly who.')
        self.assertEqual(lines[1], '')

    def test_only_matching(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn('hello 1234\n5678 this is some\ntest with 23795 numbers 0000')) \
        :
            grep.main(['--color=never', '[0-9]\+', '-o'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['1234', '5678', '23795', '0000', ''])

    def test_quiet(self):
        with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
            patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
        :
            grep.main(['--color=never', '-F', '.', 'file1.txt', 'file2.txt', 'invalid.txt', '-q'])
            lines = fake_out.getvalue().split('\n')
            err_text = fake_err.getvalue()
        # No output, but error text should still show
        self.assertEqual(lines, [''])
        self.assertIn("No such file or directory: 'invalid.txt'", err_text)

    def test_binary_matches(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, [f'{binary_file_path}: binary file matches', ''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_binary_option_binary_matches(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', '--binary-files', 'binary', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, [f'{binary_file_path}: binary file matches', ''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_binary_option_text(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', '--binary-files', 'text', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, ['eggs eggs eggs bum bumkjdbnfkadfbub', ''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_text_option(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', '--text', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, ['eggs eggs eggs bum bumkjdbnfkadfbub', ''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_binary_option_without_match(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', '--binary-files', 'without-match', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, [''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_without_match_option(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            with patch('greplica.grep.sys.stderr', new = StringIO()) as fake_err, \
                patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out \
            :
                grep.main(['--color=never', '-I', 'eggs', binary_file_path])
                lines = fake_out.getvalue().split('\n')
                err_text = fake_err.getvalue()
            self.assertEqual(lines, [''])
            self.assertEqual(err_text, '')
        finally:
            tmp_dir.cleanup()

    def test_default_directory(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'oppose', '.'])
            out = fake_out.getvalue()
        self.assertEqual(out, 'greplica: .: Is a directory\n')

    def test_read_directory(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-d', 'read', 'oppose', '.'])
            out = fake_out.getvalue()
        self.assertEqual(out, 'greplica: .: Is a directory\n')

    def test_skip_directory(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-d', 'skip', 'oppose', '.'])
            out = fake_out.getvalue()
        self.assertEqual(out, '')

    def test_recurse_directory(self):
        s = os.path.sep
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-d', 'recurse', 'oppose', '.'])
            out = fake_out.getvalue()
        self.assertEqual(out, f'.{s}file2.txt:Her object giving end sister except oppose.\n')

    def test_recurse_directory_option(self):
        s = os.path.sep
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', '-r', 'oppose', '.'])
            out = fake_out.getvalue()
        self.assertEqual(out, f'.{s}file2.txt:Her object giving end sister except oppose.\n')

    @unittest.skipIf(_is_windows(), "symlinks can't easily be created in windows")
    def test_recurse_directory_not_following_symlinks(self):
        tmp_dir = tempfile.TemporaryDirectory()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir.name)
        os.symlink(self.tmpdir.name, os.path.join(tmp_dir.name, 'link'))
        try:
            with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
                grep.main(['--color=never', '-r', 'oppose', '.'])
                out = fake_out.getvalue()
            self.assertEqual(out, '')
        finally:
            os.chdir(old_cwd)
            tmp_dir.cleanup()

    @unittest.skipIf(_is_windows(), "symlinks can't easily be created in windows")
    def test_recurse_directory_following_symlinks(self):
        s = os.path.sep
        tmp_dir = tempfile.TemporaryDirectory()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir.name)
        os.symlink(self.tmpdir.name, os.path.join(tmp_dir.name, 'link'))
        try:
            with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
                grep.main(['--color=never', '-R', 'oppose', '.'])
                out = fake_out.getvalue()
            self.assertEqual(out, f'.{s}link{s}file2.txt:Her object giving end sister except oppose.\n')
        finally:
            os.chdir(old_cwd)
            tmp_dir.cleanup()

    def test_include_glob(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'no', 'file1.txt', 'file2.txt', '--include', '*1.txt'])
            out = fake_out.getvalue()
        self.assertEqual(out, 'Smiling nothing affixed he carried it clothes calling he no.\n')

    def test_exclude_glob(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'no', 'file1.txt', 'file2.txt', '--exclude', '*1.txt'])
            out = fake_out.getvalue()
        self.assertEqual(out, 'General windows effects not are drawing man garrets.\nTaken now you him trees tears any.\n')

    def test_exclude_glob_file(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'no', 'file1.txt', 'file2.txt', '--exclude-from', 'globfile.txt'])
            out = fake_out.getvalue()
        self.assertEqual(out, 'General windows effects not are drawing man garrets.\nTaken now you him trees tears any.\n')

    @unittest.skipIf(_is_windows(), "symlinks can't easily be created in windows")
    def test_exclude_dir(self):
        s = os.path.sep
        tmp_dir = tempfile.TemporaryDirectory()
        old_cwd = os.getcwd()
        os.chdir(tmp_dir.name)
        os.symlink(self.tmpdir.name, os.path.join(tmp_dir.name, 'link'))
        os.symlink(self.tmpdir.name, os.path.join(tmp_dir.name, 'blink'))
        os.symlink(self.tmpdir.name, os.path.join(tmp_dir.name, 'sink'))
        with open('lick', 'wb') as fd:
            fd.write(b'All in favor\nall opposed')
        try:
            with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
                grep.main(['--color=never', '-R', 'oppose', '.', '--exclude-dir', 'l*k', 'sin?'])
                out = fake_out.getvalue()
            self.assertEqual(out, f'.{s}lick:all opposed\n.{s}blink{s}file2.txt:Her object giving end sister except oppose.\n')
        finally:
            os.chdir(old_cwd)
            tmp_dir.cleanup()

    def test_files_without_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'any', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-L'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file3.txt', 'file4.txt', ''])

    def test_files_with_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'any', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-l'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file1.txt', 'file2.txt', ''])

    def test_print_count(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'it', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', 'patterns.txt', '-c'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file1.txt:3', 'file2.txt:4', 'file3.txt:1', 'file4.txt:6', 'patterns.txt:0', ''])

    def test_initial_tab(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'sit', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-THn'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file2.txt:  3:\tContinual say suspicion provision he neglected sir curiosity unwilling.',
            'file4.txt:  6:\tMi sit amet mauris commodo quis imperdiet.',
            'file4.txt:  9:\tDonec enim diam vulputate ut pharetra sit amet aliquam id.',
            'file4.txt: 10:\tProin libero nunc consequat interdum varius sit amet mattis.',
            'file4.txt: 13:\tUt etiam sit amet nisl purus in mollis nunc sed.',
            ''
        ])

    def test_null_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'diam', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-ZHn'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file4.txt:8:\x00Ut diam quam nulla porttitor massa id neque aliquam vestibulum.',
            'file4.txt:9:\x00Donec enim diam vulputate ut pharetra sit amet aliquam id.',
            ''
        ])

    def test_result_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'green', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb', '--result-sep', ' :) '])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file1.txt:3:117 :) And can event rapid any shall woman green.', ''])

    def test_name_num_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'green', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb', '--name-num-sep', ' <> '])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file1.txt <> 3:117:And can event rapid any shall woman green.', ''])

    def test_name_byte_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main(['--color=never', 'green', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb', '--name-byte-sep', ' | '])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, ['file1.txt:3 | 117:And can event rapid any shall woman green.', ''])

    def test_context_group_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'on', 'file1.txt', '--context-group-sep', '\\\\/\\\\/\\n', '-C', '2'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'Up am intention on dependent questions oh elsewhere september.',
            'No betrayed pleasure possible jointure we in throwing',
            'And can event rapid any shall woman green.',
            '\\/\\/',
            'Its something disposing departure she favorite tolerably engrossed.',
            'Truth short folly court why she their balls.',
            'Excellence put unaffected reasonable mrs introduced conviction she.',
            'Nay particular delightful but unpleasant for uncommonly who.', ''
        ])

    def test_context_result_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'design', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb',
                '--context-result-sep', '!', '-C', '2'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file3.txt-1-0!Looking started he up perhaps against.',
            'file3.txt-2-39!How remainder all additions get elsewhere resources.',
            'file3.txt:3:92:One missed shy wishes supply design answer formed.',
            'file3.txt-4-143!Prevent on present hastily passage an subject in be.',
            'file3.txt-5-196!Be happiness arranging so newspaper defective affection ye.',
            ''
        ])

    def test_context_name_num_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'nulla', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb',
                '--context-name-num-sep', ' % ', '-C', '2'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file4.txt % 6-262-Mi sit amet mauris commodo quis imperdiet.',
            'file4.txt % 7-305-Amet volutpat consequat mauris nunc.',
            'file4.txt:8:342:Ut diam quam nulla porttitor massa id neque aliquam vestibulum.',
            'file4.txt % 9-406-Donec enim diam vulputate ut pharetra sit amet aliquam id.',
            'file4.txt % 10-465-Proin libero nunc consequat interdum varius sit amet mattis.',
            ''
        ])

    def test_context_name_byte_sep(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'suspicion', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-Hnb',
                '--context-name-byte-sep', '()', '-C', '1'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file2.txt-2()58-Put sir she exercise vicinity cheerful wondered.',
            'file2.txt:3:107:Continual say suspicion provision he neglected sir curiosity unwilling.',
            'file2.txt-4()179-Simplicity end themselves increasing led day sympathize yet.',
            ''
        ])

    def test_before_context(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'massa', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-H', '-B', '4'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file4.txt-Praesent elementum facilisis leo vel fringilla est ullamcorper.',
            'file4.txt-Mauris augue neque gravida in fermentum.',
            'file4.txt-Mi sit amet mauris commodo quis imperdiet.',
            'file4.txt-Amet volutpat consequat mauris nunc.',
            'file4.txt:Ut diam quam nulla porttitor massa id neque aliquam vestibulum.',
            ''
        ])

    def test_after_context(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            grep.main([
                '--color=never', 'erat', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', '-H', '-A', '4'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(lines, [
            'file4.txt:Dictum non consectetur a erat nam at.',
            'file4.txt-Praesent elementum facilisis leo vel fringilla est ullamcorper.',
            'file4.txt-Mauris augue neque gravida in fermentum.',
            'file4.txt-Mi sit amet mauris commodo quis imperdiet.',
            'file4.txt-Amet volutpat consequat mauris nunc.',
            ''
        ])

    def test_strip_cr(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn('this file\r\nmust have been made\r\nin windows\r\n')) \
        :
            with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
                grep.main(['--color=never', 'file\r'])
                out = fake_out.getvalue()
            self.assertEqual(out, f'')

    def test_no_strip_cr(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out, \
            patch('greplica.grep.sys.stdin', FakeStdIn('this file\r\nmust have been made\r\nin windows\r\n')) \
        :
            with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
                grep.main(['--color=never', '-U', 'file\r'])
                out = fake_out.getvalue()
            self.assertEqual(out, f'this file\r\n')

    #
    # Library Interface Tests
    #

    def test_lib_no_expressions(self):
        grep_obj = grep.Grep()
        grep_obj.add_files('file1.txt')
        self.assertRaises(ValueError, grep_obj.execute)

    def test_lib_no_files(self):
        grep_obj = grep.Grep()
        grep_obj.add_expressions('any')
        self.assertRaises(ValueError, grep_obj.execute)

    def test_lib_string_match_no_color(self):
        grep_obj = grep.Grep()
        grep_obj.add_expressions('any')
        grep_obj.add_files('file1.txt', 'file2.txt', 'file3.txt')
        data = grep_obj.execute()
        self.assertEqual(data['files'], ['file1.txt', 'file2.txt'])
        self.assertEqual(data['lines'], [
            'And can event rapid any shall woman green.',
            'Taken now you him trees tears any.'
        ])
        self.assertEqual(data['info'], [])
        self.assertEqual(data['errors'], [])

    def test_lib_string_match_with_color_name_and_numbers(self):
        grep_obj = grep.Grep()
        grep_obj.grep_color_dict = {} # Use default colors
        grep_obj.add_expressions('any')
        grep_obj.add_files('file1.txt', 'file2.txt', 'file3.txt')
        grep_obj.color_mode = grep.Grep.ColorMode.ALWAYS
        grep_obj.output_file_name = True
        grep_obj.output_line_numbers = True
        grep_obj.output_byte_offset = True
        data = grep_obj.execute()
        self.assertEqual(data['files'], ['file1.txt', 'file2.txt'])
        self.assertEqual(data['lines'], [
            '\x1b[35mfile1.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m3\x1b[m\x1b[36m:\x1b[m\x1b[32m117\x1b[m\x1b[36m:\x1b[m'
                'And can event rapid \x1b[01;31many\x1b[m shall woman green.',
            '\x1b[35mfile2.txt\x1b[m\x1b[36m:\x1b[m\x1b[32m8\x1b[m\x1b[36m:\x1b[m\x1b[32m393\x1b[m\x1b[36m:\x1b[m'
                'Taken now you him trees tears \x1b[01;31many\x1b[m.'
        ])
        self.assertEqual(data['info'], [])
        self.assertEqual(data['errors'], [])

    def test_lib_matching_files_only(self):
        grep_obj = grep.Grep()
        grep_obj.add_expressions('any')
        grep_obj.add_files(['file1.txt', 'file2.txt', 'file3.txt'])
        grep_obj.print_matching_files_only = True
        data = grep_obj.execute()
        self.assertEqual(data['files'], ['file1.txt', 'file2.txt'])
        self.assertEqual(data['lines'], [])
        self.assertEqual(data['info'], ['file1.txt', 'file2.txt'])
        self.assertEqual(data['errors'], [])

    def test_lib_count_only(self):
        grep_obj = grep.Grep()
        grep_obj.add_expressions('any')
        grep_obj.add_files(['file1.txt', 'file2.txt', 'file3.txt'])
        grep_obj.print_count_only = True
        data = grep_obj.execute()
        self.assertEqual(data['files'], ['file1.txt', 'file2.txt'])
        self.assertEqual(data['lines'], [])
        self.assertEqual(data['info'], ['file1.txt:1', 'file2.txt:1', 'file3.txt:0'])
        self.assertEqual(data['errors'], [])

    def test_lib_print_directory(self):
        grep_obj = grep.Grep()
        grep_obj.add_files('.')
        grep_obj.add_expressions('any')
        grep_obj.directory_handling_type = grep.Grep.Directory.READ
        data = grep_obj.execute()
        self.assertEqual(data['files'], [])
        self.assertEqual(data['lines'], [])
        self.assertEqual(data['info'], ['greplica: .: Is a directory'])
        self.assertEqual(data['errors'], [])

    def test_lib_access_error(self):
        with patch('greplica.grep.AutoInputFileIterable', PermissionErrorMockAutoInputFileIterable):
            grep_obj = grep.Grep()
            grep_obj.add_files('file1.txt', 'file2.txt', 'file3.txt')
            grep_obj.add_expressions('any')
            data = grep_obj.execute()
            self.assertEqual(data['files'], [])
            self.assertEqual(data['lines'], [])
            self.assertEqual(data['info'], [])
            self.assertEqual(data['errors'], [
                "greplica: [Errno 13] Permission denied: 'file1.txt'",
                "greplica: [Errno 13] Permission denied: 'file2.txt'",
                "greplica: [Errno 13] Permission denied: 'file3.txt'"
            ])

    def test_lib_binary_matches_print_to_info(self):
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            binary_file_path = os.path.join(tmp_dir.name, 'binary.txt')
            with open(binary_file_path, 'wb') as fd:
                fd.write(b'\xe0eggs eggs eggs bum bum\xf9kjdbnfka\xffdfbub')
            grep_obj = grep.Grep()
            grep_obj.add_files(binary_file_path)
            grep_obj.add_expressions('eggs')
            data = grep_obj.execute()
            self.assertEqual(data['info'], [f'{binary_file_path}: binary file matches'])
        finally:
            tmp_dir.cleanup()


if __name__ == '__main__':
    unittest.main()