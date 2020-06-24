Title: Linux Local Traffic Delivery
Tags: linux, networking, iptables
Date: 2020-06-24
Modified: 2020-06-24 17:13

I've recently been setting up a homebrew router, with a small fanless
linux box and Jim Salter's [homebrew router guide][homebrew-guide] as
a starting point. In the section where he sets up iptables rules, he
restricts traffic delivered over the loopback interfacee to traffic
from the `127.0.0.1/8` network; I hadn't seen that before, and it
seemed like sensible thing to do (defense in depth and all that).

[homebrew-guide]: https://arstechnica.com/gadgets/2016/04/the-ars-guide-to-building-a-linux-router-from-scratch/

When I got to later stages of the router build, I found that I
couldn't hit any ports open on the router's inferfaces while `ssh`-ed
into the box. They were accessible from other machines, but not from
the router itself. Clearly the service was running, and the firewall
was allowing traffic on that port.... but only to external hosts.

I had firewall rules like this:
```
iptables -i lo -s 127.0.0.1/8 -j ACCEPT
iptables -i wan1 -p tcp -m tcp --dport 22 -j ACCEPT
iptables -j DROP
```

and on the box, `ssh <wan1 IP>` was timing out. Nmap showed the port
as filtered as well, but other machines were able to `ssh <wan1 IP>`
with no trouble.

Turns out the problem has to do with how linux delivers network
traffic to the addresses assigned to the current device. **All traffic
destined for the current machine get delivered over the loopback
interface, regardless of the destination address**. Traffic going to
an address assigned to an external ethernet NIC are still going to be
received on `lo`.

## Tracking it down

I discovered that allowing _all_ traffic from `lo` fixed the problem,
but why was traffic destined for an address assigned to `wan1` being
received on `lo`?

It sounded like a routing thing, but `ip route` didn't show any routes
that would send `<wan IP>` to `lo`. Still, `ip route get <wan IP>`
showed `local <wan IP> dev lo src <wan IP> uid 1000`, so it was
clearly being routed to `lo`. I noticed there were no routes for the
`lo` at all in `ip route`, and discovered that there are actually
several routing tables (`ip route` only lists entries in the `default`
table). `ip route list table local` shows routes for local addresses,
but the `<wan IP>` entry specified the `wan1` interface.

I eventually came across [this answer][so_route_answer] on the
Unix/Linux Stackexchange, which states that part of linux' routing
algorithm is to look for the desination address in the `local` routing
table, and to use that route entry, but with the interface replaced by
`lo`. I haven't been able to find documentation elsewhere to
corroborate this, although it appears to be accurate.

[so_route_answer]: https://unix.stackexchange.com/questions/408300/how-does-linux-handle-routing-a-request-to-its-own-ip/408332#408332

## Fool me once...

I just got bitten by the same problem again, when working on
port-forwards: forwarded ports worked fine from other devices on the
network, but from the router itself they showed as filtered. I had set
up all of the forwarding rules to allow traffic from the WAN
interface, since the address is dynamic... except that for traffic
originating on the router, the source interface is `lo`, not the
external NIC. D'oh.
