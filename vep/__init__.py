import krux.cli
import sh
import os


class Application(krux.cli.Application):

    def __init__(self, name, **kwargs):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name, **kwargs)
        self.build_dir = ".build"
        self.package_dir = self.args.package_name
        self.target = "%s/%s" % (self.build_dir, self.args.package_name)

    def add_cli_arguments(self, parser):
        group = krux.cli.get_group(parser, self.name)

        group.add_argument(
            '--package-prefix',
            default = '/usr/local',
            help = "Path to prefix the entire package with"
        )

        group.add_argument(
            '--package-name',
            default = sh.python('setup.py', '--name').strip(),
            help = "The package name, as seen in apt"
        )

        group.add_argument(
            '--package-version',
            default = sh.python('setup.py', '--version').strip(),
            help = "The package version."
        )

        group.add_argument(
            '--pip-requirements',
            default = 'requirements.pip',
        )

    def run(self):
        print("building %s version %s" % (self.args.package_name, self.args.package_version))
        # destroy & create a virtualenv for the build
        sh.rm('-f', '-r', self.target)
        sh.virtualenv('--no-site-packages', self.target)
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


def main():
    app = Application(name='ve-packager')
    app.run()

if __name__ == '__main__':
    main()
