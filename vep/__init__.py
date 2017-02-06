# call print() as a function, not statement
from __future__ import print_function

import krux.cli
import sh
import os
from ConfigParser import RawConfigParser
import re
import shutil
import sys

__version__ = '0.0.14'


DEFAULT_PACKAGE_FORMAT = 'deb'


# pass-through function to enable line-wise output from commands called via sh.
# you would think you could just pass "print" as the callback function, but that
# does not produce meaningful output. So we have this wrapper.
def print_line(line):
    print(line.rstrip())


class VEPackagerError(StandardError):
    pass


class ConfigurationError(StandardError):
    pass


class Application(krux.cli.Application):

    setup_option_names = {
        'name': 'package_name',
        'url': 'repo_url',
        'version': 'package_version',
    }

    def __init__(self, name, **kwargs):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name, **kwargs)

        self.build_dir = os.path.join(self.args.directory, ".build")
        self.dependencies = self.args.dependency
        self.pip_cache = self.args.pip_cache
        self.package_dir = self.args.package_name
        self.target = os.path.join(self.build_dir, 'virtualenv')
        self._find_vetools()
        self.python = self.args.python
        self._power_on_self_test()
        self.setup_options = {
            'name': None,
            'url': None,
            'version': None,
        }

    def _find_vetools(self):
        self.vetools = "%s/virtualenv-tools" % os.path.dirname(sys.executable)

    def _power_on_self_test(self):
        """
        double-check that required parts are in place.
        :return: bool
        """
        # path to python has to be a link/real file, not a symlink; if it is a
        # symlink, follow it and use that.
        python_real_path = os.path.realpath(self.python)
        if python_real_path == self.python:
            pass
        else:
            self.logger.info("you asked to use{0}, which is a link to {1}, so we are using that.".format(
                    self.python, python_real_path
                )
            )
            self.python = python_real_path

    def get_setup_option(self, option):
        pycmd = sh.Command(os.path.join(self.target, 'bin', 'python'))
        if self.setup_options[option] is None:
            if getattr(self.args, self.setup_option_names[option]) is not None:
                self.setup_options[option] = self.args.getattr[self.setup_option_names[option]]
            else:
                self.setup_options[option] = pycmd('setup.py', "--%s" % option).strip()
        return self.setup_options[option]

    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)

        group.add_argument(
            '--package-prefix',
            default='/usr/local',
            help="Path to prefix the entire package with"
        )

        group.add_argument(
            '--repo-url',
            default=None,
            help="Repo URL to pass through to fpm"
        )

        group.add_argument(
            '--package-format',
            default=DEFAULT_PACKAGE_FORMAT,
            help="The package format, if not deb"
        )

        group.add_argument(
            '--package-name',
            default=None,
            help="The package name, as seen in apt"
        )

        group.add_argument(
            '--package-version',
            default=None,
            help="The package version."
        )

        group.add_argument(
            '--python',
            default='/usr/bin/python',
            help="The path to python to use. Must be a real file, not a symlink."
        )

        group.add_argument(
            '--skip-scripts',
            default=False,
            action='store_true',
            help="Skip installing all the scripts in all the setup.py files in all the requirements"
        )

        group.add_argument(
            '--shim-script',
            default=None,
            help="An extra script to run between the build and package steps. "
                 "If you need to do unnatural things to make your package work, this is the place to do them. "
                 "The script will be called via the sh module and therefore needs a shebang line."
        )

        group.add_argument(
            '--build-number',
            default=False,
            help="A build number, ie from your CI, if you want it to be appended the version number."
        )

        group.add_argument(
            '--pip-requirements',
            default='requirements.pip',
        )

        group.add_argument(
            '--pip-version',
            default='latest',
            help='Version of pip to install in the virtualenv where your application is built.',
        )

        group.add_argument(
            '--directory',
            default=os.getcwd(),
            help="Path to look in for the code you want to virtualenv-packageify. default to current directory."
        )

        group.add_argument(
            '--dependency',
            default=[],
            action='append',
            help="a package on which your package should depend. Passed through to fpm as -d. Pass multiple " \
                 "times for additional dependencies."
        )

        group.add_argument(
            '--pip-cache',
            default=os.environ.get('PIP_CACHE', None),
            help="directory to use as the pip cache; passed to pip as --cache-dir, which may not be available on " \
                 "older versions of pip."
        )

    def update_paths(self):
        vetools = sh.Command(self.vetools)
        package_name = self.get_setup_option('name')
        # this path is where the package will be installed on a target host
        new_path = os.path.join(self.args.package_prefix, package_name)

        # this path is the updated target in the build environment
        new_target = os.path.join(os.path.dirname(self.target), package_name)
        # rename target from 'virtualenv' to the package name; update self.target
        shutil.move(self.target, new_target)
        self.target = new_target
        print("updating paths in %s to %s" % (self.target, new_path))
        vetools('--update-path', new_path, _cwd=self.target)

    def clean_target(self):
        find = sh.Command("find")
        # delete *.pyc and *.pyo files
        print("removing .pyc and .pyo files in %s" % self.target)
        find(self.target, '-iname', '*.pyo', '-o', '-iname', '*.pyc' '-delete')

    def symlink_entry_points(self):
        print("sym-linking entry points")
        # make a directory at .build/bin, which will show up in self.package_prefix/bin, ie defaults to /usr/local/bin
        mkdir = sh.Command('mkdir')
        mkdir('-p', "%s/bin" % self.build_dir)
        rcp = RawConfigParser()
        # someone could be foolish enough to use a hypen in their package name, needs to be a _.
        egg = "%s.egg-info" % re.sub('-', '_', self.get_setup_option('name'))
        entry_points = os.path.join(egg, 'entry_points.txt')
        if not os.path.exists(egg) or not os.path.exists(entry_points):
            print("no entry points, so no symlinks to create")
            return
        rcp.read(entry_points)
        if 'console_scripts' not in rcp.sections():
            return
        os.chdir("%s/bin" % self.build_dir)
        for item in rcp.items('console_scripts'):
            print('linking {0}'.format(item[0]))
            # src = "../%s/bin/%s" % (self.package_dir, item[0])
            src = os.path.join(self.get_setup_option('name'), 'bin', item[0])
            dest = item[0]
            print('sym-linking ' + src + ' to ' + dest)
            if os.path.exists(dest):
                os.remove(dest)
            os.symlink(src, dest)
        os.chdir(self.args.directory)

    def package(self):
        os.chdir(self.args.directory)
        fpm = sh.Command("fpm")
        # if present, append the build number to the version number
        version_string = self.get_setup_option('version')
        if self.args.build_number:
            version_string = "{0}~{1}".format(self.args.package_version, self.args.build_number)
        # -s dir means "make the package from a directory"
        # -t deb means "make a Debian package"
        # -n sets the name of the package
        # --prefix sets the file root under which all included files will be installed
        # -v sets the package version
        # --url over-rides fpm's default of "example.com"
        # -C changes to the provided directory for the root of the package
        # add a -d for each package dependency
        # . is the directory to start out in, before the -C directory and is where the package file is created
        fpm_args = [
            '--verbose', '-s', 'dir', '-t', self.args.package_format, '-n', self.get_setup_option('name'), '--prefix',
            self.args.package_prefix, '-v', version_string, '--url', self.get_setup_option('url'),
            '-C', os.path.join(self.args.directory, self.build_dir),
        ]
        for dependency in self.dependencies:
            fpm_args += ['-d', dependency]
        fpm_args += ['.']
        fpm( _out=print_line, *fpm_args )

    def install_pip(self, pip):
        """
        :param pip: a sh Command pointing to your ve's pip
        :return:
        """
        if self.args.pip_version == 'latest':
            pip('install', 'pip', '--upgrade', _out=print_line)
        else:
            pip('install', "pip==%s" % self.args.pip_version, _out=print_line)

    def install_pip_requirements(self, pip):
        # if there is a requirements.pip, go ahead and install all the things
        if os.path.isfile(self.args.pip_requirements):
            print("installing requirements")
            # installing requirements can take a spell, print output line-wise
            pip_args = ['install', '-r', self.args.pip_requirements, '-I', ]
            if self.pip_cache is not None:
                pip_args += ['--cache-dir', self.pip_cache]
            pip(_out=print_line, *pip_args)

    def create_virtualenv(self):
        rm = sh.Command('rm')
        print("deleting previous virtual environment")
        rm('-f', '-r', self.target)
        print("creating new virtual environment")
        # we've got to use the virtualenv that is in ve-packager, not the system virtualenv,
        # which might use a different version of python.
        virtualenv = sh.Command('%s/virtualenv' % os.path.dirname(sys.executable))
        virtualenv('--no-site-packages', '-p', self.python, self.target, _out=print_line)
        # the sh module does not provide a way to create a shell with a virtualenv
        # activated, the next best thing is to set up a shortcut for pip and python
        # in the target virtualenv
        target_pip = sh.Command(os.path.join(self.target, 'bin', 'pip'))
        target_python = sh.Command(os.path.join(self.target, 'bin', 'python'))
        # now install the pip version from args.pip_version
        print("installing pip==%s" % self.args.pip_version)
        self.install_pip(target_pip)
        print("installing requirements")
        self.install_pip_requirements(target_pip)
        print("running setup.py for %s" % self.args.package_name)
        target_python('setup.py', 'install', _out=print_line)

    def run(self):
        os.chdir(self.args.directory)
        if not os.path.isfile("setup.py"):
            raise VEPackagerError("no setup.py in %s; can't proceed; try --help" % self.args.directory)
        print("building %s version %s" % (self.args.package_name, self.args.package_version))
        # destroy & create a virtualenv for the build; we can't do much before the virtualenv is
        # created, as we need to have a python environment that can run setup.py, which sometimes requires
        # loading __init__.py, which might load other non-stdlib modules.
        self.create_virtualenv()
        for name in self.setup_option_names:
            self.get_setup_option(name)
        print(self.setup_options)
        self.update_paths()
        self.clean_target()
        if not self.args.skip_scripts:
            self.symlink_entry_points()
        if self.args.shim_script is not None:
            # copy the existing environment variables
            env_vars = os.environ.copy()
            # set some environment variables the script might need
            env_vars['PACKAGE_PREFIX'] = self.args.package_prefix
            env_vars['PACKAGE_NAME'] = self.get_setup_option('name')
            env_vars['PACKAGE_DIR'] = self.package_dir
            env_vars['TARGET'] = self.target
            env_vars['BUILD_DIR'] = self.build_dir
            print("running shim script: %s" % self.args.shim_script)
            shim = sh.Command("%s" % self.args.shim_script)
            shim(_env=env_vars, _out=print_line)
        self.package()


def main():
    app = Application(name='ve-packager')
    app.run()

if __name__ == '__main__':
    main()
