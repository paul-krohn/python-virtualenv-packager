# ve-packager
A wrapper for fpm to create packages from Python virtual environments.

Based on a shell script by @plathrop. The use case is pretty environment-specific, but I've tried to keep it agnostic.

## Usage

Ideally, cd to the root of your checked-out repo, and run it:

    $ cd my-python-project
    $ ve-packager

## Limitations

The underlying program, fpm, doesn't work on OS X, due to what looks like an issue with a call to utime().

As they include the python binary, the packages created only work on the platform on which they were created.

On ubuntu lucid nodes, you'll need to activate a virtualenv that has a working pip module installed; the version of pip provided in the 'python-pip' package does not work.
