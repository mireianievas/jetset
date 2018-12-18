#!/usr/bin/env python


from __future__ import division, absolute_import, print_function

__author__ = 'andrea tramacere'




from setuptools import setup, find_packages,Extension
from distutils.extension import Extension
import glob


from distutils.command.build import build
from setuptools.command.install import install

class CustomBuild(build):
    def run(self):
        self.run_command('build_ext')
        build.run(self)

class CustomInstall(install):
    def run(self):
        self.run_command('build_ext')
        self.do_egg_install()

class CustomClean(install):
    def run(self):
        import shutil, glob
        shutil.rmtree('dist')
        shutil.rmtree('build')
        shutil.rmtree(glob.glob('*.egg-info')[0])


custom_cmdclass = {'build': CustomBuild, 'install': CustomInstall,'clean':CustomClean}





version='1.2.0'





f = open("./requirements.txt",'r')
install_req=f.readlines()
f.close()

src_files=['jetset/jetkernel/jetkernel.i']
src_files.extend(glob.glob ('jetkernel_src/src/*.c'))
_module=Extension('_jetkernel',
                  sources=src_files,
                  extra_compile_options='-fPIC  -v  -c -m64 -I',
                  extra_link_options='-suppress',
                  swig_opts=['-v',],
                  include_dirs=['jetkernel_src/include'])

setup(name='jetset',
      version=version,
      author='Andrea Tramacere',
      author_email='andrea.tramacere@gmail.com',
      packages=['jetset', 'leastsqbound', 'jetset.jetkernel'],
      package_data={'jetset':['Spectral_Templates_Repo/*.dat','test_data/SEDs_data/*dat','jetkernel/mathkernel/*dat']},
      scripts=['bin/test_interactive.py'],
      cmdclass=custom_cmdclass,
      requires=install_req,
      ext_modules = [_module],
      py_modules=['jetkernel'], )
