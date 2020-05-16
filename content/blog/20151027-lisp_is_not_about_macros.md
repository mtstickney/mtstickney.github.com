Title: Lisp is Not About Macros (or No Really, Why Lisp? part I)
Date: 2015-10-27
Category: blog
Status: draft
Tags: lisp, macros

In circles where Lisp is an acceptable language, someone will show up
periodically and ask "why lisp?". There are plenty of answers, but
invariable someone will stand up and shout "because Macros, that's
why!". Despite this rude interruption, the standard advice is to avoid
macros and use regular functions wherever possible. How can we
reconcile these two views? My claim is that, while important, macros
are not central to Lisp, and that Lisp would be a perfectly fine
language without them.

## Macro What Now?

If the standard advice is to avoid macros, why are they in the
language at all? Macros have a few specific uses, which broadly boil
down to three classes: performance enhancements, control-flow
operators, and syntax adjustments.

Performance enhancements basically mean doin


