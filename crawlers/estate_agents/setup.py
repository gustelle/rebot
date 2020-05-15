# Automatically created by: scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name='Catalog Crawlers',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests', 'ujson', 'bs4', 'jsonschema'],
    entry_points={'scrapy': ['settings = estate_agents.settings']}
)
