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

## Vendor Tentacles

- environment variables
- global registry settings
