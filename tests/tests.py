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

class CliTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        with open(os.path.join(cls.tmpdir.name, "file1.txt"), "wb") as fd:
            fd.write(test_file1.encode())
        with open(os.path.join(cls.tmpdir.name, "file2.txt"), "wb") as fd:
            fd.write(test_file2.encode())
        with open(os.path.join(cls.tmpdir.name, "patterns.txt"), "wb") as fd:
            fd.write(b'glue\nkelp\ntrash\ntree\nneglect')

    def setUp(self):
        self.old_dir = os.getcwd()
        os.chdir(self.tmpdir.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def tearDown(self):
        os.chdir(self.old_dir)

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
            # Should match "man" but not "woman"
            grep.main(['--color=never', '-xE', 'clothes', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '')

    def test_line_regex_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '-xE', '.*clothes calling he no.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'Smiling nothing affixed he carried it clothes calling he no.')
        self.assertEqual(lines[1], '')

    def test_null_data(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '-z', 'trees', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], '')
        self.assertEqual(lines[1], 'Taken now you him trees tears any.')
        self.assertEqual(lines[2], 'Her object giving end sister except oppose.')
        self.assertEqual(lines[3], '')

    def test_invert_match(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '-vF', '.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'No betrayed pleasure possible jointure we in throwing')
        self.assertEqual(lines[1], '')

    def test_max_num(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
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
            # Should match "man" but not "woman"
            grep.main(['--color=never', 'mr', 'file1.txt', 'file2.txt', '-b'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '366:Excellence put unaffected reasonable mrs introduced conviction she.')
        self.assertEqual(lines[1], '0:Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[2], '')

    def test_line_number(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', 'mr', 'file1.txt', 'file2.txt', '-n'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '8:Excellence put unaffected reasonable mrs introduced conviction she.')
        self.assertEqual(lines[1], '1:Ladyship it daughter securing procured or am moreover mr.')
        self.assertEqual(lines[2], '')

    def test_line_buffered(self):
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(True)) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '.', 'file1.txt', 'file2.txt', '--line-buffered'])
            lines = fake_out.getvalue().split('\n')
            flush_count = fake_out.flush_count
        self.assertEqual(len(lines), 19)
        self.assertEqual(flush_count, 18)

    def test_not_line_buffered(self):
        with patch('greplica.grep.sys.stdout', new = FakeStdOut(True)) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', '.', 'file1.txt', 'file2.txt'])
            lines = fake_out.getvalue().split('\n')
            flush_count = fake_out.flush_count
        self.assertEqual(len(lines), 19)
        self.assertEqual(flush_count, 0)

    def test_with_filename(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
            grep.main(['--color=never', 'any', 'file1.txt', 'file2.txt', '-H'])
            lines = fake_out.getvalue().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'file1.txt:And can event rapid any shall woman green.')
        self.assertEqual(lines[1], 'file2.txt:Taken now you him trees tears any.')
        self.assertEqual(lines[2], '')

    def test_with_no_filename(self):
        with patch('greplica.grep.sys.stdout', new = StringIO()) as fake_out:
            # Should match "man" but not "woman"
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



if __name__ == '__main__':
    unittest.main()