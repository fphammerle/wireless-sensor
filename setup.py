import pathlib

import setuptools

_REPO_URL = "https://github.com/fphammerle/wireless-sensor"

setuptools.setup(
    name="wireless-sensor",
    use_scm_version=True,
    packages=setuptools.find_packages(),
    description="Decode signals sent by FT017TH thermo/hygrometer",
    # long_description=pathlib.Path(__file__).parent.joinpath("README.md").read_text(), TODO
    # long_description_content_type="text/markdown",
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
        "hygrometer",
        "sensor",
        "thermometer",
        "wireless",
    ],
    classifiers=[
        # https://pypi.org/classifiers/
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        # .github/workflows/python.yml TODO
        # "Programming Language :: Python :: 3.5",
        # "Programming Language :: Python :: 3.6",
        # "Programming Language :: Python :: 3.7",
        # "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
    ],
    # entry_points={"console_scripts": ["wireless-sensor = wireless-sensor:_main"]},
    install_requires=[
        # >=1.17.0 for numpy.packbits's bitorder arg
        # https://docs.scipy.org/doc/numpy-1.16.0/reference/generated/numpy.packbits.html?highlight=packbits#numpy.packbits
        "numpy>=1.17.0,<2",
        # pinning exact version due to use of unstable receive api
        # https://github.com/fphammerle/python-cc1101/compare/v2.1.0...v2.2.0a0#diff-319c0dd5b99765f9ec51a25fd100c899d6ce5009b654bd0763090f157a791a67R70
        "cc1101==2.2.0a0",
    ],
    setup_requires=["setuptools_scm"],
    tests_require=["pytest"],
)
