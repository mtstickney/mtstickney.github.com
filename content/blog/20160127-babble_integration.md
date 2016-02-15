Title: Work Challenge #1: Down the Rabbit Hole
Date: 2016-01-27
Category: blog
Status: draft
Tags: blog, programming, language interop, abl, windows, work challenge

>  In the desert  
>  I saw a creature, naked, bestial,  
>  Who, squatting upon the ground,  
>  Held his heart in his hands,  
>  And ate of it.  
>  I said, "Is it good, friend?"  
>  "It is bitter--bitter," he answered;  
>  
>  "But I like it  
>  "Because it is bitter,  
>  "And because is is my heart."  
> -- Stephen Crane, "In the Desert"

## Note on the series

_This is the first in a series of interesting challenges I've
encountered at work. Most of them are issues with the environment, and
are obstacles to the main work at hand, and not the work itself._

## The Wasteland

Our primary language at work is, to put it politely, underpowered. It
has no real data structures, synchronous and asynchronous networking
but without streams or promises (or lambdas), is strictly
single-threaded, and has a non-existent standard library. Basic tasks
like making an HTTP request or sending mail via SMTP are untenably
difficult, but still necessary for our application. Later versions of
the language have a bridge to .NET code, but we can't rely on it being
available on our customer's systems.

This came to a head with our previous mail client, which had been
copied off a community wiki some time in the murky past. It couldn't
talk to any server that used encryption, which is most of them these
days, and it had some protocol issues that caused certain severs --
like GMail -- to reject the communication as invalid. The existing
code was nearly impossible to modify: all the networking was
asynchronous, and without data structure all the state was kept in a
pile of global variables. We needed to roll out new email features,
which meant replacing this client with something more robust.

Since you can't implement a reasonable SMTP client in the primary
language, and since the .NET bridge wasn't available, I figured it
would be useful to embed a more capable language myself. I initially
planned on the JVM, but after a little research it looked like it
would be much simpler to use
[ECL](https://common-lisp.net/project/ecl/) -- Common Lisp is a
capable language with a model that makes interop easy, and the ECL
implementation was designed to be embedded in other programs.

## If it ain't one thing...

After a fair bit of work, I had a version of ECL that could be loaded
into our main application, and used to call Lisp code that had been
loaded in the image. An SMTP library provided non-broken email
support, threads appeared to work, and life was good. Rumor had it
that our language's VM was unfriendly toward embedded code, but
everything was working well. Then, on the brink of success, the
unthinkable: our tester reported that our application crashed on
_every machine that wasn't my VM_[^1].

[^1]: I suspect this may have had something to do with Windows'
    Dynamic Execution Prevention system. Lisp implementations
    typically set this off because of the dynamic code generation they
    do, but it's only enabled by default on Server editions of
    Windows, so it's easy to miss during development. Sadly I haven't
    had the time to verify the theory.

Not only had my project catastrophically failed, but now all of the
email-based features we were trying to roll out were in jeopardy. In a
desperate attempt to stem the bleeding, I called upon the Unix gods
and did what any gray-bearded programmer would: moved the Lisp
implementation into a separate process. Since I couldn't just pass
pointers around anymore, I had to find an wire-format encoding that
could be used by both the Lisp process and our gimpy language; and
since I couldn't initialize the process with a blocking call, I'd need
a way to know when it had started up (or worse, when it failed
to). Performance would probably also take a hit, so mitigating that
would be important for fine-grained calls[^2].

[^2]: As part of the original system, I had implemented a rather
    cunning, if complex, system that allowed the Lisp image to call
    back into the main process to handle database manipulation (our
    language is a 4gl and can't talk to normal databases -- it's on
    loan to us from the 80s). Unfortunately, with the number of calls
    required, performance was slow even with the directly-embedded
    version.

I settled on a scheme where the two processes would communicate with
[MsgPack](http://msgpack.org/index.html) over a named pipe. The main
process would act as a pipe server, and the Lisp process would connect
to it after receiving the pipe name as an argument. That way the main
process could block waiting for a connection, and would at least be
notified if the Lisp process was killed because the pipe would be
broken. I had to write a wrapper library to allow our main language to
work with pipes, and I had to work around issues on the Lisp side
too[^3], but eventually it seemed to be working reliably, and we were
able to roll out the email features to a few customers without
problems. There were even a few opportunities for performance
improvements, and life was good again.

[^3]: For example, most Lisps check file existence with the `_stat()`
function, which calls `CreateFile()` internally. This counts as a
connection to the pipe, and a subsequent open will fail unless the
server re-creates the instance. Since most Lisps check file existence
before opening in order to signal an error for missing files, a normal
open call can't be used to connect to a named pipe.

## ...it's another.

Another unfortunate feature of our primary language is that it's
extremely chatty when talking to the database, which makes it unusably
slow over a non-local network connection. Some of our customers have
installations at several locations that need to share a database; our
solution in these cases is to run our software on a Terminal Server
machine that's local to the database, and have each location log in
remotely.

One of these customers was recently given the version of our software
with the Lisp co-process to solve some email issues they were having,
and instantly ran out of virtual address space on their server. They
had 60 clients running sessions simultaneously, and like many other
garbage-collected languages, Lisp implementations often allocate their
whole heap space on startup. Linux systems handle this with
overcommit, but on Windows our implementation allocates the memory
with `MEM_COMMIT | MEM_RESERVE`, which consumes the whole chunk of
address space on allocation.

Increasing the system's page file up to 50Gb was sufficient to solve
their immediate problem, but starting 60 large processes is wasteful
for an application that just uses them for networking services and
some text processing. The solution was to share a single co-process
among all the users on the same machine.

The first step was to make the co-process the pipe server, so that
multiple instances of the main application could connect to it, and
have the co-process exit if the pipe already existed. That was simple
enough, but we lost the ability to wait for the co-process to connect,
so initialization had to get timeout parameters and a special wait
function[^4].

[^4]: Windows has a function to wait for a named pipe to become
    available for connection, but it can't be used to wait on a pipe
    that doesn't exist yet. To get a proper timeout, you have to
    `Sleep()` in the case that the pipe doesn't exist, and
    `WaitNamedPipe()` when it does; since `Sleep()` isn't interrupted
    when the pipe becomes available, you need a timeout that retries
    connections a certain number of times.

Now we have to deal with the first real problem in this setup: when
the first instance of our application starts up, it will launch the
co-process which will act as a server for all other instances of our
application. So far so good. However, the co-process is started as the
user who is currently logged in -- which means that as soon as they
end the remote session, the co-process will be killed, leaving other
instances of our application stranded.

To solve this, we need a non-user service to be responsible for
launching instances of the co-process, so that they won't be owned by
logged-in users. On Linux, we'd just start this as a DBus client and
be done with it, but since Windows doesn't have a reasonable DBus
equivalent, it has to listen on a well-known named pipe for launch
requests (we can re-use the MsgPack protocol here). A little bit of
work in [Go](https://golang.org) solved this admirably, except that
named pipes in Windows only grant permissions to their creator by
default -- now _nobody_ could connect to the server.

## And another?

With a little bit of fooling with Go's foreign-function system and a
few patches to the [npipe](https://github.com/natefinch/npipe)
library, I had an implementation that would correctly launch shared
co-process instances for multiple users without getting terminated at
logout. Our application could now do basic things like speaking to
mail servers and processing a config file, all things that should been
available to begin with.

Surely this house of cards won't last. Something, somewhere, is going
to go wrong with one of these moving parts -- my bet is that someone
will manage to kill the shared co-process while other instances are in
the middle of using it. The only real solution is to port our
application to a sane language, just as fast as we possibly can. For
now, though, our Rube-Goldberg-ian creation will have to rumble along
until we hit another hurdle.
