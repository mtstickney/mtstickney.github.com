Title: Work Challenge #2: Installer Madness
Date: 2016-01-30
Category: blog
Tags: blog, programming, abl, windows, work challenge

_The second in a [series](/tag/work-challenge.html) of technical
challenges encountered in the course of trying to get work done._

As I mentioned in the previous
[piece](/blog/work-challenge-1-down-the-rabbit-hole.html) in the
series, the primary language we use at work is often rather
frustrating to work with. In addition to the language itself, the
platform infrastructure is also poorly designed, particularly for
cases like ours where we're maintaining a large number of remote
systems in various environments without the benefit of local
personnel. Broken or troublesome installers have been an issue for us
in two areas, where we've had to replace the ones supplied by our
vendor.

## The Sub-Par Standard

Before we get into the specific cases where we've had to route around
the damage, I want to briefly describe the _status quo_ for our
vendor's system. The system we use is divided into components, each of
which requires a license from the vendor. Lets say you're going to
install the mid-range database component and a client access
component. You'd grab the great big installer for your version, run
it, type in your license keys for both components, and wait for them
to be installed. Typically you'd then run an additional service pack
installer, because the vendor doesn't supply service packs as a
roll-up. The service pack installer will detect the installed
components and install the service-pack version of those components
over the top.

If you want to add a component later, you'd be tempted to use the
installer that was installed along with the components (nope, not
making that up) and which is labeled "Add Components" in the Start
menu group. You'd be mistaken if you did, because that's got a bug
where it detects itself as a process using a critical file, and won't
proceed. To do that, you need to carefully stop any process using
files from the vendor an re-run the external installer (you did keep
that around, right?), after which you'll need to run the service pack
installer again. There's no provision for removing components, so if
you wanted to do that you'd have to uninstall and reinstall.

## The Megalith

An obvious downside to this kind of installer is that it has to
contain the data for every component that a user might install (same
goes for the service pack). This makes the installers pretty huge --
about 2Gb for the main installer, and another 1Gb for the service
pack. Having to download 3Gb of installer onto a machine that may be
behind the cheapest DSL line the business owner could find is pretty
painful, and moving files around the internal network is no picnic
either. They have multiple stores? Now you get to attend that party
_twice_. For large installations, we often mail the customer a flash
drive that someone on-site can take around to each station and plug
in.

Curiously, it's not just the installer itself that's bloated. When you
install the client access component, the install is about 500Mb, and
contains database-management tools, source code, and binaries for
completely unrelated components. After some system tracing and
trial-and-error-by-deleting, I determined that the bits used to
actually run programs written for this system are only about 14Mb
(40Mb if you include some optional widget libraries).

After I'd figured out what we really needed, I whipped up an installer
for just those parts. Final size: 6Mb. It runs in a couple of seconds,
is trivial to distribute, and it can be quickly removed and
reinstalled if the install gets corrupted.

Me: 1, vendor: 0.

## The Installer that Didn't

Our vendor provides a component that includes ODBC drivers so that
other systems can access their proprietary database. At some point,
someone decided that it was irritating to drag around several
gigabytes worth of installers to a bunch of different client machines,
so they decided to include a separate installer for the drivers with
the client component.

I stumbled across this when I was poking around the system folder one
day. "Wow!" I thought, "My troubles are over! Easy street, here I
come!" I tracked down a knowledgebase article about how to use it,
which instructed me to map a network drive to the machine with the
installer, and run it from there. H-uh. "Ok," I thought, "they're just
trying to avoid telling people how to find and copy the installer
file. Fair enough."  Then I hit the second paragraph:

> All the files for the ODBC drivers will be on the centrally located
> file server. If at any time the file server changes, the relevant
> setup executable above will need to be run from each machine to
> update the location of the ODBC driver files.
>
> Existing DataSources will have outdated definitions of the location
> of the DLL file used by ODBC and will need to be recreated.

Just to paraphrase: they have a 50Mb installer, which, when run,
_doesn't actually install anything_. If you poke around enough it
becomes clear that this is part of some Machiavellian scheme to
prevent people from talking to their database without a client
license, but come on. Having your ODBC drivers go out every time your
network hiccups or your share names change or your permissions go
screwy? This is why we can't have nice things.

As with the main installer, I whipped up a 5Mb jobby to install the
ODBC drivers in the normal, sane fashion. It's smaller than the
vendor's, it actually installs something, and unlike the vendor's you
can install more than one version at a time, in case you need to talk
to more than one database from a client. You can even install them
alongside the vendor's version without conflict, if you like.

Me: 2, vendor: 0.
