import io
import os

from setuptools import setup, find_packages

dir = os.path.dirname(__file__)

with io.open(os.path.join(dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pytrendex',
    version='0.0.1',
    description='Tool To Create Google Trends Index From Keywords',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lucashusted/pytrendex',
    author='Lucas Husted',
    author_email='lfh2119@columbia.edu',
    license='GNU',
    install_requires=['pytrends','requests', 'pandas>=0.25', 'lxml','matplotlib'],
    python_requires='>=3',
    packages=find_packages()
)
