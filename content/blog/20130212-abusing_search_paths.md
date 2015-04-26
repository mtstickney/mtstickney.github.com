Title: Abusing Search Paths for Fun and Profit
Date: 2013-02-12
Category: Blog
Tags: worklog, abl

What do you do when you have to use an undocumented function? Reverse
engineer it, naturally. I was recently in the position of having to
automate some functions of an interactive tool provided by my language
environment. The language docs said the procedure I needed could be
extracted from a library distributed with the tool, but neglected to
mention what it's parameters were or what data needed to be passed.

The extracted procedure was a bytecode-compiled file, so I couldn't
examine the code, but I found a handy [script][param-script] that
would extract the parameter information from the bytecode. That wasn't
enough to use the procedure, but it did give me an idea: if I could
replace the standard procedure with my own version, I could have it
report the input it was getting when it was called.

[param-script]: https://gist.github.com/abevoelker/581127

I had traced the tool in Process Monitor earlier, and noticed that it
always searched for raw-source procedure files before bytecode files,
and for bytecode files before looking in a procedure library. I
whipped up a quick version of the procedure I wanted to call with the
right parameters, which would just report its input when run, and
plopped it next to the procedure library I'd extracted the bytecode
file from. I fired up the tool, pointed it at a file, and sure enough
it ran my procedure, reported the data, and promptly crashed.

That gave me enough information to use the real procedure file,
despite the total lack of documentation. The moral of the story here
is that language search paths often be used to hook parts of an
application that would otherwise be hard to reach, whether it's
bytecode files or DLLs (LD_PRELOAD, anyone?).
