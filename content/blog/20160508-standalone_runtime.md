Title: Work Challenge #3: Standalone Runtime
Date: 2016-05-08
Category: blog
Status: draft
Tags: blog, programming, abl, windows, work challenge

_The third in a [series](/tag/work-challenge.html) of technical
challenges encountered in the course of trying to get work done._

In the [previous part](/blog/work-challenge-2-installer-madness.html)
of the series, I mentioned there would be more detail here about the
standalone client installer I covered. As it turns out, one of the
other weak points of our vendor's system is its inability to
encapsulate the runtime used for programs. Since it doesn't do much
good to install a runtime you can't use, I'm going to cover those
aspects of it here.

## Encapsulated Programs

As has been mentioned here before, the language we use at work is
interpreted, and runs code in the form of source or bytecode
files. The traditional challenge for that sort of language is
deployment: at some point or other, you'll want to deploy an
application either as a single binary, or at least without requiring
the user to install the interpreter separately. Python, for example,
has this issue, and there are a number of
[solutions](https://wiki.python.org/moin/DistributionUtilities) to
deal with packaging up all the various pieces into one unit.

Our vendor, on the other hand, has no such utilities, and unlike
Python their system is unusually resistant to being
encapsulated. Gilles Querret (author of one of the only build systems
for ABL, [PCT](http://jakejustus.github.io/pct/)) has covered a
similar
[process](http://blog.riverside-software.fr/2010/01/openedge-client-deployment-using.html)
for deploying client applications, but I wanted to document my work
here, as it includes some details and caveats that his method doesn't.

## Parts and Pieces

In addition to the files required for the client to run, and
supplementary information for them (e.g. registry entries for ActiveX
components that must be registered), there are a number of
configuration and environment issues that must be handled. The
Progress client requires supplementary files and environment variables
for a default startup parameters file (`startup.pf`, set in
`PROSTARTUP`), a character-encoding conversion map (`convmap.cp`, set
in `PROCONV`), a license file (`progress.cfg`, set in `PROCFG`), a
file with printable error messages (`promsgs`, set in `PROMSGS`), and
a top-level environment variable for the installation (`DLC`). There
are also a variety of platform setting that are set by default in the
registry, but that can be overridden with a local configuration file
(typically `progress.ini`).

Most of these files will never need to be altered by programs, but for
those that do, it should still be possible. Progress uses hardcoded
fallback paths for them, so we need to set the environment
variables to avoid using erroneous paths. The solution to both problems is to use
a small wrapper program that examines the environment and sets unset
variables to appropriate wrapper-relative paths. Copies of the default
installed files are included with the package, but applications can
use their own local copies by setting the environment variables
appropriately.

Progress also stores defaults for platform settings in the registry
under various keys. There is a provision for using configuration files
instead; rather than implement an automatic solution, programs should
expect to use a config file with the encapsulated runtime package.

- environment variables/supplementary files
- global registry settings (progress.ini)
