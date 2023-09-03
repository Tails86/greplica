import setuptools
import subprocess

# This project is only packaged as sdist so that this setup.py script runs at the target

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

def _is_grep_found():
    try:
        try:
            cmd = ['grep', '--version']
            grep_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            # This happens if grep is not installed
            return False

        try:
            out, _ = grep_proc.communicate(timeout=10.0)
        except subprocess.TimeoutExpired:
            # Something went wrong with this execution - assume invalid grep installation
            return False

        # Ensure this actually returned a grep version string and isn't just a past installation of greplica
        return (b'grep' in out and b'greplica' not in out)
    except Exception:
        # Covering all bases - assume invalid grep installation
        return False

# Always have greplica as script
console_scripts = ['greplica=greplica.__main__:main']

# This isn't perfect, but it's better than nothing
# Install grep alias script only if grep is not already found on the system
if not _is_grep_found():
    print('Installing grep script because grep not found on system')
    console_scripts.append('grep=greplica.__main__:main')
else:
    print('Not installing grep; grep already found on system')

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