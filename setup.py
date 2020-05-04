# To create new distro: python setup.py sdist bdist_wheel
# To upload: twine upload dist/*

import io
import os
from setuptools import setup, find_packages

dir = os.path.dirname(__file__)

with io.open(os.path.join(dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pytrendex',
    version='4.0.1',
    description='Tool To Create Google Trends Index From Keywords',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lucashusted/pytrendex',
    author='Lucas Husted',
    author_email='lucas.f.husted@columbia.edu',
    license='GNU',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        ],
    install_requires=['pytrends','requests','numpy','statsmodels','pandas>=0.25', 'lxml','matplotlib'],
    python_requires='>=3',
    packages=find_packages()
)
