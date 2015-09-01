Title: IV-less Encryption
Date: 2015-09-01
Category: Blog
Tags: cryptography, encryption, AES, programming
Status: draft

To the surprise of many a prorammer new to encryption, several
algorithms require a third parameter when encrypting, in addition to
the key and the data. This parameter (the Initialization Vector) needs
to be stored and re-supplied in order to properly decrypt the data
later. There are plenty of ways to store the IV, and really you can
use whatever is convenient; what follows is an interesting trick that
allows you to do encryption in AES CBC-mode without ever explicitly
storing or transmitting IVs, and without sacrificing security.

## Who Needs IVs, Anyway?

First, a brief note on IVs: Initialization Vectors are actually a
critical piece of strong encryption in CBC mode. Without it, or with a
poorly chosen IV, the encrypted data is subject to known-ciphertext
attacks (i.e. it's not
[semantically secure](https://en.wikipedia.org/wiki/Semantic_security)). In
order to function properly, the IV used to encrypt and decrypt data
needs to be cryptographically random. If your library makes the mistake
of having one, it can be tempting to use the "don't use an IV" option
just for convenience. This is a Bad Idea(tm); Just Say No.

## Quirks of CBC Mode

In CBC mode, each block is encrypted and then `XOR`ed with the
preceding output block. That is, `out[n] = encrypt(key, (input[n] XOR
out[n-1]))`. The first block, which has no preceding output block, is
`XOR`ed with the IV instead: `out[0] = encrypt(key, (input[0] XOR
iv))`.

Decryption works the same way, but in reverse: `out[n] = decrypt(key,
input[n]) XOR input[n-1]`, and `out[0] = decrypt(key, input[0]) XOR
iv`. Note that the decrypted block `n` doesn't require the _decrypted_
block `n-1`, just the _encrypted_ block `n-1` that you were handed to
decrypt.

Now lets supposed you have a message with two blocks, `p[0]` and
`p[1]`, which were encrypted with a key `k` and an IV `iv1` into a
ciphertext (call the ciphertext blocks `c[0]` and `c[1]`). Now lets
see what happens if we try to decrypt that with a completely different
IV, `iv2`: for the first block, we first decrypt the ciphertext block
to get `p[0] XOR iv1` and then `XOR` it with out IV, `iv2`. Whoops!
Unless `iv1` and `iv2` happen to be the same, `p[0] XOR iv1 XOR iv2`
is going to be garbage. So much for the first block.

But wait! What about the second block? First we decrypt the ciphertext
block to get `p[1] XOR c[0]`, and then we `XOR` with the preceding
ciphertext block `c[0]` to get `p[1] XOR c[0] XOR c[0]`, which most
certainly _does_ equal our original plaintext block `p[0]`. We've
successfully decrypted the data and the IV hasn't even come into the
picture, and this will also be true for any subsequent ciphertext
blocks for the same reason. In other words, if we encrypt and decrypt
with two different IVs, we only lose the first block of data.

## Spooky IV Action at a Distance

The obvious way to exploit this behavior is to have the encrypting
party and the decrypting party generate independent cryptographically
random IVs, and treat the first block of data as sacrificial
garbage. Since the encrypting side and decrypting side aren't using
the same IV, they don't need to store or transmit it. The encrypted
data will be a block larger (the same as if you were to concatenate
the IV and the ciphertext), and there is one extra encrypt and decrypt
operation.

This is a rather cute trick for doing encryption without synchronizing
IVs (and without resorting to an all-zero IV and sacrificing data
security), but it's only applicable to CBC-mode, which you probably
shouldn't be using. CBC-mode doesn't do authentication, which is
Bad[^1]; you should use an authenticating mode like
[GCM](https://en.wikipedia.org/wiki/Galois/Counter_Mode) or
[EAX](https://en.wikipedia.org/wiki/EAX_mode) instead (or at least use
a Message Authentication Code). Better still, make your life easier
and use a library that avoids insecure modes altogether, like the
excellent [libsodium](https://libsodium.org). In short: cryptography
is hard, lets go shopping!

[^1]: This is surprising to many people, but without a special
provision for message authentication, encryption ciphers have no way
to tell the difference between a legitimately encrypted message and
random garbage (and this is a good thing). It is surprisingly easy to
produce certain kinds of outputs by modifying the ciphertext, and a
non-authenticating mode like CBC will happily decrypt it without any
idea that it's been tampered with.

## Addendum: Credit Where Credit is Due

I came up with this scheme while I was exploring the AES encryption in
our system at work, which features an option where "no initialization
vector value is used", after a Stack Overflow answer pointed out that
losing the IV only means losing the first block. However, it's not the
first time someone's come up with the idea:
[this answer](http://crypto.stackexchange.com/a/7937) refers to the
same scheme.
