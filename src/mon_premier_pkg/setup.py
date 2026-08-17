

from setuptools import find_packages, setup

package_name = 'mon_premier_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cecilia',
    maintainer_email='ceciliarazakaharisoa@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={

        'console_scripts': [
             'mon_publisher = mon_premier_pkg.mon_publisher:main',
'mon_subscriber = mon_premier_pkg.mon_subscriber:main',
        ],
    },
)
