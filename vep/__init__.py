import krux.cli
import sh
import os
from ConfigParser import RawConfigParser
import re
import sys

class Application(krux.cli.Application):

    def __init__(self, name, **kwargs):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name, **kwargs)
        self.build_dir = os.path.join(self.args.directory, ".build")
        self.package_dir = self.args.package_name
        self.target = "%s/%s" % (self.build_dir, self.args.package_name)
        self._find_vetools()

    def _find_vetools(self):
        self.virtualenvtools = "%s/virtualenv-tools" % os.path.dirname(sys.executable)

    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)
        pycmd = sh.Command('python')

        group.add_argument(
            '--package-prefix',
            default = '/usr/local',
            help = "Path to prefix the entire package with"
        )

        group.add_argument(
            '--package-name',
            default = pycmd('setup.py', '--name').strip(),
            help = "The package name, as seen in apt"
        )

        group.add_argument(
            '--package-version',
            default = pycmd('setup.py', '--version').strip(),
            help = "The package version."
        )

        group.add_argument(
            '--build-number',
            default = False,
            help = "A build number, ie from your CI, if you want it in the version number."
        )

        group.add_argument(
            '--pip-requirements',
            default = 'requirements.pip',
        )

        group.add_argument(
            '--directory',
            default = os.getcwd(),
            help = "Path to look in for the code you want to virtualenv-packageify. default to current directory."
        )

    def update_paths(self):
        vetools = sh.Command(self.virtualenvtools)
        new_path = "%s/%s" % (self.args.package_prefix, self.args.package_name)
        print "updating paths in %s to %s" % (self.target, new_path)
        vetools('--update-path', new_path, _cwd=self.target)

    def clean_target(self):
        find = sh.Command("find")
        # delete *.pyc and *.pyo files
        print "removing .pyc and .pyo files in %s" % self.target
        find(self.target, '-iname', '*.pyo', '-o', '-iname', '*.pyc' '-delete')

    def symlink_entry_points(self):
        print "symlinking entry points"
        # make a directory at .build/bin, which will show up in self.package_prefix/bin, ie defauslt to /usr/local/bin by def
        mkdir = sh.Command('mkdir')
        mkdir('-p', "%s/bin" % self.build_dir)
        rcp = RawConfigParser()
        # someone could be foolish enough to use a hypen in ther package name, needs to be a _.
        egg = "%s.egg-info" % re.sub('-', '_', self.args.package_name)
        entry_points = os.path.join(egg, 'entry_points.txt')
        if not os.path.exists(egg) or not os.path.exists(entry_points):
            print "no entry points, so no symlinks to create"
            return
        rcp.read(entry_points)
        if 'console_scripts' not in rcp.sections():
            return
        os.chdir("%s/bin" % self.build_dir)
        for item in rcp.items('console_scripts'):
            src = "../%s/bin/%s" % (self.package_dir, item[0])
            dest = item[0]
            print 'symlinking ' + src + ' to ' + dest
            if os.path.exists(dest):
                os.remove(dest)
            os.symlink(src, dest)
        os.chdir(self.args.directory)

    def package(self):
        fpm = sh.Command("fpm")
        fpm('--verbose', '-s', 'dir', '-t', 'deb', '-n', self.args.package_name, '--prefix', self.args.package_prefix,
            '-v', self.args.package_version, '-C', os.path.join(self.args.directory, self.build_dir), self.args.directory)

    def run(self):
        print("building %s version %s" % (self.args.package_name, self.args.package_version))
        # destroy & create a virtualenv for the build
        rm = sh.Command('rm')
        print "deleting previous virtual environment"
        rm('-f', '-r', self.target)
        print "creating new virtual environment"
        virtualenv = sh.Command('virtualenv')
        virtualenv('--no-site-packages', self.target)
        # the sh module does not provide a way to create a shell with a virtualenv
        # activated, the next best thing is to set up a shortcut for pip and python
        # in the target virtualenv
        target_pip = sh.Command("%s/bin/pip" % self.target)
        # now install pip 1.4.1 ugh
        print "installing pip 1.4.1"
        target_pip('install', 'pip==1.4.1')
        # if there is a requirements.pip, go ahead and install all the things
        if os.path.isfile(self.args.pip_requirements):
            print "installing requirements"
            target_pip('install', '-r', self.args.pip_requirements, '-I')
        target_python = sh.Command("%s/bin/python" % self.target)
        target_python('setup.py', 'install')
        self.update_paths()
        self.clean_target()
        self.symlink_entry_points()
        self.package()


def main():
    app = Application(name='ve-packager')
    app.run()

if __name__ == '__main__':
    main()
