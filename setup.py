# wireless-sensor - Receive & decode signals of FT017TH wireless thermo/hygrometers
#
# Copyright (C) 2020 Fabian Peter Hammerle <fabian@hammerle.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pathlib

import setuptools

_REPO_URL = "https://github.com/fphammerle/wireless-sensor"

setuptools.setup(
    name="wireless-sensor",
    use_scm_version=True,
    packages=setuptools.find_packages(),
    description="Receive & decode signals of FT017TH thermo/hygrometers",
    long_description=pathlib.Path(__file__).parent.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Fabian Peter Hammerle",
    author_email="fabian@hammerle.me",
    url=_REPO_URL,
    project_urls={"Changelog": _REPO_URL + "/blob/master/CHANGELOG.md"},
    license="GPLv3+",
    keywords=[
        "FT017TH",
        "IoT",
        "cc1101",
        "climate",
        "decode",
        "home-automation",
        "humidity",
        "hygrometer",
        "raspberry-pi",
        "sensor",
        "thermometer",
        "wireless",
    ],
    classifiers=[
        # https://pypi.org/classifiers/
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        # .github/workflows/python.yml
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Home Automation",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": ["wireless-sensor-receive = wireless_sensor._cli:_receive"]
    },
    install_requires=[
        # >=1.17.0 for numpy.packbits's bitorder arg
        # https://docs.scipy.org/doc/numpy-1.16.0/reference/generated/numpy.packbits.html?highlight=packbits#numpy.packbits
        "numpy>=1.17.0,<2",
        # pinning exact version due to use of unstable receive api
        "cc1101==2.7.3",
    ],
    setup_requires=["setuptools_scm"],
    tests_require=["pytest"],
)
