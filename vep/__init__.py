import krux.cli
import sh


class Application(krux.cli.Application):

    def __init__(self, name, **kwargs):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name, **kwargs)

    # def _read_package_defaults(self):
    #     # can't import setup.py, or variables from it, so call a shell to call python ...
    #     self.package_version = sh.python('setup.py', '--version').strip()
    #     self.package_name = sh.python('setup.py', '--name').strip()
    #
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
            '--directory',
            default = False,
            help = "Path to look in for a git repo & commit changes"
        )

    def run(self):
        print("building %s version %s" % (self.args.package_name, self.args.package_version))


def main():
    app = Application(name='ve-packager')
    app.run()

if __name__ == '__main__':
    main()
