from setuptools import setup, find_packages
from os.path import join, abspath, dirname
from re import search as re_search

PACKAGE_NAME = "ramp-client"
PACKAGE_DIR = "ramp_client"
ROOT_DIR = abspath(dirname(__file__))

with open("requirements.txt") as requirements_txt:
    requirements = requirements_txt.read().splitlines()

EXTRA_REQUIRES = {
    "dev": [
        "black~=20.8b1",
        "pylint~=2.6.0",
    ],
}

with open(join(ROOT_DIR, "README.md"), encoding="utf-8") as readme_file:
    README = readme_file.read()

with open(
    join(ROOT_DIR, PACKAGE_DIR, "__version__.py"), encoding="utf-8"
) as version_file:
    VERSION = re_search(r'__version__\s+?=\s+?"(.+)"', version_file.read()).group(1)

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    long_description=README,
    long_description_content_type="text/markdown",
    description="API wrapper for interacting with https://ramp.com",
    author_email="geoff@cover.build",
    author_name="Geoffrey Doempke",
    url="https://github.com/efnineio/ramp",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    py_modules=[PACKAGE_DIR],
    python_requires=">=3.6",
    install_requires=requirements,
    packages=find_packages(exclude=["tests", "tests.*"]),
    extras_require=EXTRA_REQUIRES,
    keywords="api wrapper",
)
