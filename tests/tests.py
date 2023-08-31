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
No betrayed pleasure possible jointure we in throwing.
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
Preference imprudence contrasted to remarkably in on.
Taken now you him trees tears any.
Her object giving end sister except oppose.'''

class FakeStdIn:
    def __init__(self, loaded_str):
        if isinstance(loaded_str, str):
            loaded_str = loaded_str.encode()
        self.buffer = BytesIO(loaded_str)

class CliTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        with open(os.path.join(cls.tmpdir.name, "file1.txt"), "w") as fd:
            fd.write(test_file1)
        with open(os.path.join(cls.tmpdir.name, "file2.txt"), "w") as fd:
            fd.write(test_file2)
        with open(os.path.join(cls.tmpdir.name, "patterns.txt"), "w") as fd:
            fd.write('glue\nkelp\ntrash\ntree\nneglect')

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



if __name__ == '__main__':
    unittest.main()