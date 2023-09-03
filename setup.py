import setuptools
import os
import sys
import fnmatch

# This project is only packaged as sdist so that this setup.py script runs at the target

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

def _which(cmd):
    paths = os.environ.get('PATH', '')
    paths = paths.split(os.path.pathsep)
    dirs = [d for d in paths if os.path.isdir(d)]

    if sys.platform.lower().startswith('win'):
        # Windows environment variable PATHEXT specifies executable extensions
        strip_ext = tuple([e.lower() for e in os.environ.get('PATHEXT', '').split(';')])
        case_sensitive = False
        cmd = cmd.lower()
    else:
        strip_ext = None
        case_sensitive = True

    # Only search paths which don't have 'python' in it (in case this is an upgrade)
    for dir_path in [d for d in dirs if 'python' not in d.lower()]:
        for item in os.listdir(dir_path):
            if strip_ext and item.lower().endswith(strip_ext):
                base_item = os.path.splitext(item)[0]
            else:
                base_item = item

            if not case_sensitive:
                base_item = base_item.lower()

            if base_item == cmd:
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                    return item_path

    return None

# Always have greplica as script
console_scripts = ['greplica=greplica.__main__:main']

# This isn't perfect, but it's better than nothing
# Install grep alias script only if grep is not already found in path
grep_path = _which('grep')
if grep_path is None:
    print('Installing grep script because grep not found in PATH')
    console_scripts.append('grep=greplica.__main__:main')
else:
    print('Not installing grep; grep already found at: {}'.format(grep_path))

setuptools.setup(
    name='greplica',
    author='James Smith',
    author_email='jmsmith86@gmail.com',
    description='A grep clone in Python supporting ANSI color coding and more',
    keywords='grep, regex, print',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Tails86/greplica',
    project_urls={
        'Documentation': 'https://github.com/Tails86/greplica',
        'Bug Reports': 'https://github.com/Tails86/greplica/issues',
        'Source Code': 'https://github.com/Tails86/greplica'
    },
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': console_scripts
    }
)