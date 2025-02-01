from setuptools import setup, find_packages

setup(
    name='beacon-app',
    version='1.0',
    description='Application for working with WSPR-beacon based on ESP32 MCU',
    author='Ihar Yatsevich',
    author_email='igor.nikolaevich.96@gmail.com',
    license='GPL-3.0',
    url='https://github.com/IgrikXD/WSPR-beacon',
    packages=find_packages(),
    package_data={
        'beaconapp': [
            'resources/*.png ',
            'resources/*.ico',
        ]
    },
    install_requires=[
        'customtkinter',
        'pillow',
        'pyserial'
    ],
    include_package_data=True,
    entry_points={
        'gui_scripts': [
            'beacon-app = beaconapp.main:main',
        ],
    }
)