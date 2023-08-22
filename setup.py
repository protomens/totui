# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='totui',
    version='1.9.0',
    description='TradeOgre TUI',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='protomens',
    author_email='protomens@eratosthen.es',
    url='https://github.com/protomens/totui',
    license='MIT',
    keywords='crypto tui tradeogre bitcoin monero haven dero arrr',
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    include_package_data=True,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=['requests',  'npyscreen', 'undetected_chromedriver', 'selenium', 'bs4', 'urllib3', 'pillow', 'qrcode'],
    package_data={'totui': ['config.ini','coins.list', 'logo.uni']},
    entry_points = {
        'console_scripts': ['totui = totui.totui:main'],
    }
)

