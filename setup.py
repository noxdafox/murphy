import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="mrmurphy",
    version="0.0.1",
    author="F-Secure Corporation",
    author_email="matteo.cafasso@f-secure.com",
    url="https://github.com/f-secure/mrmurphy",
    description=("Framework for automating GUI based application testing"),
    long_description=read('README.rst'),
    license="Apache License 2.0",
    keywords="test automation",

    python_requires='>=3.5',
    install_requires=['graphviz',
                      'libvirt-python',
                      'numpy',
                      'Pillow',
                      'pyvbox',
                      'vncdotool'],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'mrmurphy = murphy.main:main',
        ]
    },

    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
