# ve-packager
A wrapper for fpm to create packages from Python virtual environments.

Based on a shell script by @plathrop. The use case is pretty environment-specific, but I've tried to keep it agnostic.

## Installation
This is a debian package in krux's apt repo. To install you should be able to:

    $ apt-get install ve-packager
    
As `ve-packager` is a wrapper for fpm, which is distributed as a gem, make sure that is installed and working before proceeding.
 
Due to a limitation/design choice in virtualenv-tools, if your python is a symlink, virtualenv-tools will silently fail to update the path to python in your virtual environment. The issue is that virtualenv-tools will only update the path to `python`, not `python27` or similar. If your path to python is a symbolic link (as is the case on distributions that use /etc/alternatives to manage which python you are using), the paths will not get updated, and none of your CLI entry points will work.

For this reason, `ve-packager` checks if your path to python and the real path are the same, and bails if not. You'll need a path to a python that is called `python`, and is in a path that has no symlinks. Pass that in to ve-packager via the `--python` flag.

## Usage

Ideally, cd to the root of your checked-out repo, and run it:

    $ cd my-python-project
    $ ve-packager

## Limitations

The underlying program, fpm, doesn't work on OS X, due to what looks like an issue with a call to utime().

As they include the python binary, the packages created only work on the platform on which they were created.

On ubuntu lucid nodes, you'll need to activate a virtualenv that has a working pip module installed; the version of pip provided in the 'python-pip' package does not work.
