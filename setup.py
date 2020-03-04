import io
import os

from setuptools import setup

dir = os.path.dirname(__file__)

with io.open(os.path.join(dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='wb_gtrends',
    version='1.0.0',
    description='Tool To Create Google Trends Index From Keywords',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lucashusted/wb_gtrends',
    author='Lucas Husted',
    author_email='dreyco676@gmail.com',
    license='GNU',
    install_requires=['requests', 'pandas>=0.25', 'lxml','matplotlib','seaborn'],
    packages=['modules'],
)
