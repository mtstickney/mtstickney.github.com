Title: Pipes and Permissions
Date: 2017-05-08
Category: blog
Tags: worklog, systems programming, windows

_The third in a [series](/tag/work-challenge.html) of technical
challenges encountered in the course of trying to get work done._

If you have two components of a system implemented as separate
processes, you need a way for them to communicate. Unless speed is
critical, you're likely to use sockets or pipes for the channel. Named
pipes are an obvious choice for local communication, and offer an API
similar to sockets, but there are some subtle differences to be aware
of.

# The Pipeserver Model

If you plan to have more than one client of your IPC channel, the
named pipe interface is nearly the same as a traditional socket
server. You create a named pipe, wait for a connection to it, and then
you have an open file-like IPC channel between the component and the
client. Easy, right?

Not so fast. Even though there are direct analogues to the socket
system calls (`CreateNamedPipe` <=> `listen`, `ConnectNamedPipe` <=>
`accept`), and even though the documentation throws around terms like
"pipe server" pretty freely, the underlying model of named pipes is
_different_ than the socket model. The crucial difference is that
sockets have a separate object responsible for accepting connections,
and pipes do not.

When you create a socket server by calling `listen`, you get a socket
listening for connections on some port; when you call `accept` on it
and a client connects, you receive a _new_ socket that's a dedicated
connection to the client[^1]. The original socket remains open,
listening for connections.

[^1]: This always reminds me of `fork`, in that it creates something
that's a distinct clone of it's parent in some ways (both sockets
share the same address and port on the server end). It's like a kind
of algae budding off a new cell: if system calls had sound effects,
`fork` and `listen` would both be accompanied by "*blorp*".

Pipes, on the other hand, don't have the concept of a distinguished
server[^2]. Unlike sockets, when a client connects to a named pipe
server, the pipe instance that they connect _to_ is the same one
they'll be talking _over_. You don't get a new pipe instance, and if
all the instances have been used up, there is no pipe for clients to
connect to (more on this in a bit). This is extra misleading, because
you can create several instances of the same pipe, and it acts
_exactly like the backlog queue in a server socket_ (but it isn't).

[^2]: The `FILE_FLAG_FIRST_PIPE_INSTANCE` flag sure makes it seem that
way, but it's only there to avoid a certain privilege-escalating race
condition (see [here](http://www.blakewatts.com/namedpipepaper.html),
section 3.1). The flag only prevents you from creating a pipe if one
with that name already exists; it doesn't change the pipe itself.

# The Pipe Permission Model

Named pipes also have permissions, like any other object in
windows. While sockets will allow any client to connect to them, pipes
allow you specify a range of mandatory and discretionary ACLs (DACLs)
to restrict what clients may connect or perform other
operations. Pipes also have a curious feature that allows the server
program to impersonate the connecting client, so that a server can
drop privileges to the client's level before servicing requests[^3].

Pipes also inherit these permissions, provided that you're creating
new instances of an existing pipe. If you've set a DACL entry for a
pipe, and you create a new instance of it, the new instance will also
have the DACL applied, even though you created the new instance with
the default permissions[^4].

[^3]: This is also subject to a number of race conditions and
privilege-escalation issues. See the rest of [this
article](http://www.blakewatts.com/namedpipepaper.html).

[^4]: I'm not certain if this is always the case, or only if you use
the default security descriptor by passing `NULL` to
`CreateNamedPipe`.

# Interactions in the Field

Named pipe permissions can sometimes interact with the pipe model in
surprising (and generally unpleasant) ways. Before I explain why,
though, a bit of backstory: at one point at work, we had embedded a
scripting runtime into our application. At the last minute we
discovered issues with our main language runtime, and moved it into a
separate process communicating over a pipe, started by the main
application. Later, due to memory constraints on many-user systems, we
converted the component to a thread-per-client pipe server running as
a service.

Initially, there were no permissions issues:The process was created by
the same user that was connecting to it, so there was no need to
modify the ACLs or impersonate the client. When the component was
converted to a service, we hit our first snag: the default permissions
for named pipes allow administrators to connect[^5], but not
non-administrative users, so we had to modify the DACL to allows
connections from other users, and we had to start impersonating
clients to avoid privilege escalation.

[^5]: There was an additional complication to early versions of this
component: before it was converted to a service, our application would
launch the new process on startup, and if the named pipe already
existed, the process would exit and the existing one would service
connections from the application. As a result, the process ran as the
user account that started the application first, which might or might
not prevent future clients from connecting. Moral of the story: don't
forget to do multi-user testing if that's relevant to your
application.

After the service-based component had been deployed for while, we
discovered that on some systems the pipe's permissions would
periodically revert to the defaults, requiring the service to be
restarted before users could connect. This happened several times a
day on some systems, and never occurred on others.

When we finally tracked it down, this is what was happening: the pipe
library we used (Nate Finch's [npipe](http://github.com/nfinch/npipe))
provides a socket-like interface to a pipe server, but doesn't support
setting DACLs or expose the creation of new pipe instances. To make
multi-user connections work, we were starting the server and using a
patched-in method to set a DACL on the underlying pipe instance. When
clients connected, the library would create a new pipe instance
internally -- depending on whether the previous pipe instance had been
closed, the new instance might inherit the (correct) permissions from
its parent, or get the (broken) default permissions, which it would
then pass on to any child instances.

The fix for this is simple: without modifying the library to better
support setting DACLs, we changed the application to leave pipe
instances open until we were sure the library had created the next
one. Because the previous instance was already open, the next instance
would inherit the proper permissions (I refer to this arrangment as
"heirloom permissions"). That sounds pretty dodgy in retrospect, but
it's been quite stable in production.

# The Moral

Named pipes aren't sockets; don't try to pretend that they are. Pipes
use a different server model than sockets do, and have additional
permissions issues to consider. If you're writing a pipe server, you
need to recreate the listening pipe after you accept a connection;
that exposes you to some extra race conditions, and can affect the way
that pipe permissions are inherited.
