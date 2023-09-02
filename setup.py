import setuptools
import os

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

def _which(cmd):
    paths = os.environ.get('PATH', '')
    paths = paths.split(os.path.pathsep)
    dirs = [d for d in paths if os.path.isdir(d)]
    for dir_path in dirs:
        for item in [f for f in os.listdir(dir_path) if f == cmd]:
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                return item_path
    return None

# Always have greplica as script
console_scripts = ['greplica=greplica.__main__:main']

# This isn't perfect, but it's better than nothing
# Install grep alias script only if grep is not already found in path
if _which('grep') is None:
    console_scripts.append('grep=greplica.__main__:main')

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