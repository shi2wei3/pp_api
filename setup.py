import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(name='pp_api',
      version='0.1',
      description='Product Pages API',
      long_description='Product Pages API',
      classifiers=[
        "Programming Language :: Python",
        ],
      author='Wei Shi',
      author_email='wshi@redhat.com',
      url='',
      keywords='pp api',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [console_scripts]
      pp = pp_api.pp:main
      """,
      )
