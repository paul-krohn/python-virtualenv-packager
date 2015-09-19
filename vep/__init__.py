import krux.cli
import sh
import os
from ConfigParser import RawConfigParser

class Application(krux.cli.Application):

    def __init__(self, name, **kwargs):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name, **kwargs)
        self.build_dir = ".build"
        self.package_dir = self.args.package_name
        self.target = "%s/%s" % (self.build_dir, self.args.package_name)

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

    def update_paths(self):
        vetools = sh.Command('virtualenv-tools')
        new_path = "%s/%s" % (self.args.package_prefix, self.args.package_name)
        print "updating paths in %s to %s" % (self.target, new_path)
        vetools('--update-path', new_path, _cwd=self.target)

    def clean_target(self):
        find = sh.Command("find")
        # delete *.pyc and *.pyo files
        print "removing .pyc and .pyo files in %s" % self.target
        find(self.target, '-iname', '*.pyo', '-o', '-iname', '*.pyc' '-delete')

    def symlink_entry_points(self):
        # make a directory at .build/bin, which will show up in self.package_prefix/bin, ie defauslt to /usr/local/bin by def
        mkdir = sh.Command('mkdir')
        mkdir('-p', "%s/bin" % self.build_dir)
        rcp = RawConfigParser()
        egg = "%s.egg-info" % self.args.package_name
        entry_points = os.path.join(egg, 'entry_points.txt')
        if not os.path.exists(egg) or not os.path.exists(entry_points):
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

    def package(self):
        # fpm --verbose -s dir -t deb -n "${PACKAGE_NAME}" --prefix "${DEST_DIR}" -v "${VERSION}" -C "${BUILD_DIR}" .
        fpm = sh.Command("fpm")
        fpm('--verbose', '-s', 'dir', '-t', 'deb', '-n', self.args.package_name, '--prefix', self.args.package_prefix,
            '-v', self.args.package_version, '-C', self.build_dir, '.')

    def run(self):
        print("building %s version %s" % (self.args.package_name, self.args.package_version))
        # destroy & create a virtualenv for the build
        rm = sh.Command('rm')
        rm('-f', '-r', self.target)
        virtualenv = sh.Command('virtualenv')
        virtualenv('--no-site-packages', self.target)
        # the sh module does not provide a way to create a shell with a virtualenv
        # activated, the next best thing is to set up a shortcut for pip and python
        # in the target virtualenv
        target_pip = sh.Command("%s/bin/pip" % self.target)
        # now install pip 1.4.1 ugh
        target_pip('install', 'pip==1.4.1')
        # if there is a requirements.pip, go ahead and install all the things
        if os.path.isfile(self.args.pip_requirements):
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
