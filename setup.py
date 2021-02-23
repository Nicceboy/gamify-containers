from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='lutris-docker',
    version="0.1.0", 
    author="Niklas Saari",
    author_email="niklas.saari@tutanota.com",
    description='Play Windows games on Linux containers with Lutris',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nicceboy/gamify-containers",
    py_modules=['play'],
    install_requires=['docker>=4.3.3'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['playlutris=play:main'],
    },
    python_requires='>=3.6',
)

