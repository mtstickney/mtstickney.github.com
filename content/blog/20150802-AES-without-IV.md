Title: IV-less Encryption
Date: 2015-08-02
Category: Blog
Tags: cryptography, encryption, AES, programming
Status: draft

Programmers new to encryption are often surprised to find that some
algorithms require them to make special arrangements to transmit or
store Initialization Vectors. What follows is a handy trick for doing
AES encryption without an IV in CBC mode, without sacrificing
security.

## Who Needs IVs, Anyway?

Initialization Vectors are actually a critical piece of strong
encryption in CBC mode. Without it, or with a poorly chosen IV, the
encrypted data is subject to known-ciphertext attacks (i.e. it's not
[semantically secure](https://en.wikipedia.org/wiki/Semantic_security)). In
order to function properly, the IV used to encrypt and decrypt data
needs to be cryptographically random.

## Quirks of CBC Mode

In CBC mode, each block is encrypted and then `XOR`ed with the preceding
output block. The first block, which has no preceding output block, is
`XOR`ed with the IV instead. Since blocks are `XOR`ed with the previous
_output_ block, this has a curious property: if you have two blocks,
you can recover the second (and subsequent blocks) even if you have no
way to recover the first.

We can exploit this property pretty easily: if losing the IV means we
can no longer retrieve the first block, then we can treat the first
block as sacrificial and ignore the IV entirely, adding a sacrificial
block when encrypting and discarding it on decryption. You could use
an IV of a block of all-zero bytes (some systems refer to this as
encrypting "without an IV"), or a random value, or even different
values when encrypting and decrypting.

In order to maintain good security properties, we should still use a
cryptographically-random IV (but now we don't need to store or
transmit it). It might be tempting to use an all-zero IV and a
cryptographically-random first block, but the properties will only
hold if the result of encrypting the block is suitably random[^1].

[^1]: It should be, but I'm not a cryptographer and it definitely works
the other way around.

## Credit Where Credit is Due

I came up with this scheme while I was exploring the AES encryption in
our system at work, which features an option where "no initialization
vector value is used", after a Stack Overflow answer pointed out that
losing the IV only means losing the first block. However, it's not the
first time someone's come up with the idea:
[this answer](http://crypto.stackexchange.com/a/7937) refers to the
same scheme.
