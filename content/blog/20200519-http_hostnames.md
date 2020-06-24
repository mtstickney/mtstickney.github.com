Title: HTTP Request Hostnames
Date: 2020-06-24
Modified: 2020-06-24 18:03
Category: blog
Tags: http, web, servers, nginx

How many hostnames can a single HTTP request be associated with? Two,
or three if you're using SSL.

The usual place to specify a virtualhost name is the `Host` header;
this is mandatory in HTTP 1.1 requests, so it's almost always set
these days.

The second place a virtualhost name might be specified in the URL
argument to the HTTP verb: `GET http://foobar.com/blog/` is a valid
form for a `GET` request (true for other verbs, too).

If you're serving an HTTPS connection, the SSL protocol can also
specify a virtualhost name in the Server Name Indicator part of the
connection handshake (this is necessary in order to allow the server
to serve the appropriate certificate for the virtualhost). This
happens prior to, and separately from, any HTTP request made over that
connection.

Any or all of these hostnames can be used in a single request, and
there is no requirement (other than common sense) that they match. For
plain HTTP, nginx will select server blocks using the hostname from
the verb URL if present, then from the `Host` header, then by the
usual [matching algorithm][nginx_request_processing].

[nginx_request_processing]: http://nginx.org/en/docs/http/request_processing.html

The situation with HTTPS connections is surprising: the SNI hostname
is used to select the certificate that nginx uses, but it is _not_
used to select the server block to handle the request; that takes the
hostname from the request as usual. Alarmingly, this means an
exotically-formed request can return site contents for virtual host A
with host B's certificate.

## Test Setup

To test, I've added the following blocks to nginx:

```
    # Test setup for virtualhost priority checking.
    # Non-SSL servers
    server {
        listen 127.0.0.1:8888 default_server;
        return 200 'This is the default server.\n';
    }

    server {
        listen 127.0.0.1:8888;
        server_name foo;

        return 200 'This is foo.\n';
    }

    server {
        listen 127.0.0.1:8888;
        server_name bar;
        return 200 'This is bar.\n';
    }

    # Self-signed SSL servers.
    server {
        listen 127.0.0.1:8889 ssl;
        server_name palladium;
        ssl_certificate palladium.cert;
        ssl_certificate_key palladium.key;
        ssl_protocols TLSv1.2;
        return 200 'This is palladium.\n';
    }

    server {
        listen 127.0.0.1:8889 ssl;
        server_name foobar;
        ssl_certificate foobar.cert;
        ssl_certificate_key foobar.key;
        ssl_protocols TLSv1.2;
        return 200 'This is foobar.\n';
    }
```

You can see the priority of hostnames with some carefully-crafted
requests (response headers have been trimmed for brevity).

Baseline request with `Host` header for unknown and known virtualhosts:
```
$ nc localhost 8888 <<EOF
> GET / HTTP/1.1
> Host: quux
> Connection: close
> 
> EOF
This is the default server.

$ nc localhost 8888 <<EOF
> GET / HTTP/1.1
> Host: foo
> Connection: close
> 
> EOF
This is foo.
```

The URL hostname takes priority over the `Host` header:
```
$ nc localhost 8888 <<EOF
> GET http://bar/ HTTP/1.1
> Host: foo
> Connection: close
> 
> EOF
This is bar.
```

SNI hostname selects the cert, but uses the HTTP hostnames to select a
server block for the actual request:

```
$ openssl s_client -connect localhost:8889 -servername palladium -quiet <<EOF
> GET https://foobar/ HTTP/1.1
> Host: palladium
> Connection: close
> 
> EOF
depth=0 CN = palladium
[...]
This is foobar.
```

## Lessons

Since a request can have several different hostnames associated with
it, you need to be careful about reconstructing request URLs; this
usually bites when setting up reverse-proxy headers like
`X-Forwarded-Host` or `Forwarded`.

For a non-default server block (and remember, in nginx there's
_always_ a default server block, even if it's just the first matching
one), `$http_host` and `$ssl_server_name` are _not_ going to give you
the right hostname in the face of exotic requests. `$host` should (it
resolves to the hostname in priority order), but given that the proxy
config is probably static, it might be smarter to use `$server_name`
so you know what you're getting.

For a default server block, you should expect to get requests for
hosts other than `server_name` as a matter of course. If you really
need to process the request hostname, `$host` is probably your best
bet.
