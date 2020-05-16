Title: Polymorphic Functions in ABL
Date: 2015-10-27
Category: blog
Tags: abl, OO, experiments

If you've ever looked at books on refactoring code, there's one common
theme among them: every piece of refactoring advice that has ever been
given assumes the existence of an object system in your language[^1].

At work, we use this crummy business-oriented language called ABL. It
actually has objects, despite their
[many shortcomings](https://blog.abevoelker.com/progress_openedge_abl_considered_harmful/)[^2],
but they come at a prohibitive cost for us: they require manual
memory management, and there are a number of subtle compiler bugs that
affects code compiled one one version and run on another.

[^1]: Michael Feathers'
    [book](http://www.amazon.com/Working-Effectively-Legacy-Michael-Feathers/dp/0131177052)
    actually includes a tiny little section at the end about working
    with C. It consists mainly of the author throwing up his hands and
    suggesting you use a real language.

[^2]: See the "OOABL" sections toward the end. Bear in mind that most
    of the "fixed" issues don't apply to the versions we have in the field.

So what's a down-and-out developer to do? If you squint hard enough,
you'll notice that objects are useful for refactoring mostly because
they provide polymorphic methods. Encapsulation is largely handled by
forward-declaring functions (and ABL doesn't even have the notion of a
struct, so no need to worry about those), and while inheritance is
nice, it's mostly a convenience. Polymorphism allows you to substitute
implementations without changing the code that uses them, which allows
hard code dependencies to be broken.

# Requirements

I wanted to see if I could provide polymorphism in ABL without the
drawbacks of objects. There were a few requirements:

1. Implementations must be able to be stored in variables and passed
   to functions.
2. Implementations shouldn't require explicit create/release calls.
3. The system should allow basic mistakes like typos to be caught at
compile time.
4. It would be nice if it wasn't completely impossible to read.

# The Experiment

I spent some time this afternoon to attempt an implementation, and
wound up with the following scheme: I'd focus just on dispatching
function (method) calls, and use interface and implementation keys to
look up the concrete procedure in question. ABL does allow procedures
to be dynamically invoked, so by returning a procedure, we can also
punt parameter passing to the caller.

Here's what it looks like:

    /* Top-level include for the runtime and type definition. */
    {interfaces.i &NEW="NEW"}

    /* Declare an interface method (mostly just for compiler support). */
    {define-interface.i "igreeter.sayhello"}

    /* You can now use {&igreeter.sayhello} to refer to this
    interface. */
    DEFINE VAR greeter AS {&INTERFACE} NO-UNDO.
    greeter = {&igreeter.sayhello}.

To supply an implementation of a method, you create a normal procedure
and register it with an implementation class:

    {implements.i {&igreeter.sayhello} greeter.english hello.p}
    {implements.i {&igreeter.sayhello} greeter.spanish hola.p}

    /* The methods can be invoked directly....*/
    {invoke.i {&igreeter.sayhello} {&greeter.english}} ("Jimmy").
    {invoke.i {&igreeter.sayhello} {&greeter.spanish}} ("Jimmy").

    /* ...or by passing implementation classes around. */
    PROCEDURE SayHi:
        DEFINE INPUT PARAM klass AS {&INTERFACE} NO-UNDO.
        DEFINE INPUT PARAM name AS CHARACTER NO-UNDO.
        {invoke.i {&igreeter.sayhello} klass} (name).
    END.

    RUN SayHi({&greeter.english}, "Jimmy").
    RUN SayHi({&greeter.spanish}, "Jimmy").

# Results

The interfaces (and implementation classes) in this system can be
stored in variables and passed to procedures, require no memory
management, and will even show up nicely in logs. Since they're
referred to with preprocessor macros, typos in interface or class
names will be caught at compile time (procedure names and parameter
lists are not normally checked). It's debatable whether this counts as
"not impossible to read", but it's at least vaguely decipherable, and
it's pretty easy to wrap.

The current incarnation is pretty basic, and has a number of
limitations:

1. It only supports procedures (not functions or methods).
2. It only support _local_ procedures (can't call a procedure in another
persistent procedure).
3. Procedure parameters aren't checked against the interface for consistency.

# Implementation

The implementation of this scheme is rather strange, mostly because of
preprocessor contortions, though it's also rather small at about 60
lines of code.

The core is a small runtime that is responsible for registering and
looking up concrete procedures for interface implementations:

    CLASS MethodRuntime:
        DEFINE PROTECTED TEMP-TABLE tt_method NO-UNDO
                FIELD klass AS CHARACTER
                FIELD methodName AS CHARACTER
                FIELD procName AS CHARACTER
                FIELD procHdl AS HANDLE
                INDEX method_index IS PRIMARY
                        klass
                        methodName.

        METHOD PUBLIC VOID RegisterMethod(klass AS CHARACTER, methodName AS CHARACTER):
                FIND FIRST tt_method WHERE tt_method.klass = klass
                                AND tt_method.methodName = methodName
                                NO-LOCK NO-ERROR.
                IF AVAILABLE tt_method THEN DO:
                        ASSIGN tt_method.procName = procName
                                tt_method.procHdl = procHdl.
                        RETURN.
                END.

                CREATE tt_method.
                ASSIGN tt_method.klass = klass
                        tt_method.methodName = methodName
                        tt_method.procName = procName
                        tt_method.procHdl = procHdl.
        END.

        METHOD PUBLIC CHARACTER MethodProc(methodName AS CHARACTER,
                       klass AS CHARACTER):
                FIND FIRST tt_method WHERE tt_method.klass = klass
                                AND tt_method.methodName = methodName
                                NO-LOCK NO-ERROR.
                IF NOT AVAILABLE tt_method THEN DO:
                       FIND FIRST tt_method WHERE tt_method.klass = klass
                                       NO-LOCK NO-ERROR.
                       IF NOT AVAILABLE tt_method THEN
                              RETURN ERROR SUBSITUTE("No such class'&1'", klass).
                       ELSE
                              RETURN ERROR SUBSTITUTE("Class '&1' has no method '&2'",
                                            klass, methodName).
                END.
                RETURN tt_method.procName.
        END.
    END.

Internally, classes and interfaces are strings: this allow them to be
created without memory management issues, and means they'll print
nicely in logfiles. They're stored in a temp-table with an index,
since we expect method registration to happen less than method calls,
and we'd like those to be fast if possible.

The toplevel `interfaces.i` include defines a shared instance of the
runtime class, and establishes the opaque `{&INTERFACE}` type synonym
for interfaces and implementation classes.

    &IF DEFINED(INTERFACES_I_)=0 &THEN
    &GLOBAL-DEFINE INTERFACES_I_

    &GLOBAL-DEFINE INTERFACE CHARACTER
    DEFINE {&NEW} SHARED VAR MethodRuntime AS CLASS MethodRuntime NO-UNDO.

    &IF '{&NEW}'<>'' &THEN
    MethodRuntime = NEW MethodRuntime().
    &ENDIF

    &ENDIF

The `define-interface.i` include-macro does very little: it simply
defines a preprocessor name for the string constant that is the
interface name.

    &GLOBAL-DEFINE {1} '{1}'

The `implements.i` include-macro does the same for the implementation
class, and expands to a call to `MethodRuntime:RegisterMethod()`. The
parent-procedure handle parameter of `RegisterMethod` is unused for
now.

    &GLOBAL-DEFINE {2} '{2}'
    MethodRuntime:RegisterMethod({1}, {&{2}}, "{3}", ?).

`invoke.i` is a simple expansion to all but the parameter list of a
dynamic procedure call, using the procedure name returned by the
runtime:

    RUN VALUE(MethodRuntime:MethodProc({1}, {2}))

# Conclusion

It is clearly possible to provide polymorphic functions in ABL, with a
few nice properties, as long as you're willing to accept a slightly
cumbersome syntax and some modest restrictions on the implementations
of methods. Basic compile-time support is doable, and there is no risk
of memory leaks without garbage collector support.
