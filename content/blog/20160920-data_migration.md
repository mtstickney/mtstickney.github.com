Title: Seed Data in Database Migrations
Date: 2016-09-20
Category: Blog
Status: draft
Tags: database, essay

Managing database schema changes in a consistent way is important for
any application that relies on a database, and doubly so for
on-premise software. Schema migrations are a common way of solving
this problem, but the issue of seed and static data is often given
short shrift. This is my attempt to work out a sensible policy for
data handling in schema migrations.

## Context

Rails and Django are by far the most commonly discussed uses of schema
migrations, and most of the advice you can find is related to one of
those two systems. However, our project differs from their models of
migrations in important ways, so it's important to set some context
here.

The classic way of managing our database changes has been individual
change scripts[^1] run by support technicians when updating a customer to
a new version. The scripts can only alter the schema, not data, have
no specified order, and have to be applied individually through a gui
dialog in our vendor's db management tool. To save technician time and
reduce errors, we want to replace this with a formal schema-migrations
process -- a similar facility to make data changes has been quite
popular with the technicians.

[^1]: These scripts are a proprietary format for describing schema
changes, not standard SQL change scripts. In addition to limitations
in the format's capabilities, it is undocumented and can only be
created by creating two databases and "diffing" them.

Our application is procedural, and doesn't have any sort of
application model like ActiveRecord (the main application isn't even
SQL-based). That means we don't have the auto-magical
migration-generation facilities that Rails or Django has, but we also
don't have to worry about issues with the model code not matching the
generated migration. We'll be writing and executing SQL statements
directly.

Our database changes will sometimes require non-SQL code to run. Due
to restrictions in our primary language and limitations in the SQL
support in the database, we need to maintain a few tables of
schema-related metadata to be enforced by non-SQL procedures after the
main migrations are complete. This is much easier and less error-prone
if db changes like table creation can be wrapped in convenience
functions. These convenience functions also make it easier to handle
existing schema that needs to be left in place when a migration is
applied, like tables created before migrations were in use. Some data
changes would also require non-SQL code to execute, assuming
migrations are the appropriate place for them.

Our database design is also in pretty rough shape these days, and is
going to need lots of incremental changes made to it. That makes
incremental-only migrations an appropriate fit -- they're also
considerably simpler to implement than a system that compares
snapshots and can accept hints to correct mistakes in the naive
generated migrations[^2].

[^2]: The other major disadvantage of snapshot-comparison migrations
is that without an application model, the snapshots have to be taken
from the database, which means you need two copies of it. Our current
tool works this way, and it's a royal pain to keep everything
straight. On top of that, we're still working on our ability to
recreate databases from scratch, which makes the process very ad-hoc.

## Technical Goals

We want to use migrations both to create new production databases
during a fresh install, and to update an existing database to the
state needed to support a new feature or product version. Rollbacks in
production are generally a bad idea, but they're very convenient in a
development environment. Accurate schema rollbacks are actually a hard
requirement because of the way our primary language depends on schema
details. We have a few requirements of migrations:

1. After running migrations on a fresh database, the application
should be able to run without error. Any other data that needs to be
supplied for normal operation has to be entered by a normal user.
2. The same is true for new features: after running migrations for
that feature, it must be usable with only user-entered additional
data.
3. Migrations must not overwrite existing user-entered data in
the database unless it's part of a planned format change.

## DB Changes

Based on the existing change scripts and data-population procedures we
have, there are a few broad categories of database changes, each of
which has different needs to fulfill the goals above.

### Static Data

Static data, if it's truly static, should probably be kept in code or
static files instead of database. However, we have legacy tables that
hold static data, and they need to be populated correctly. Since users
never modify the data in the tables, we can migrate the schema and
data freely, the same way we would if the data were embedded in
code. Static data is required for correct operation, and isn't
user-enterable, so it needs to be populated in a migration.

## Initial System Data

Some records in the database are necessary for the program to run, but
are meant to be altered by the user: for example, a system settings
record. Since these records are required for normal operation, they
have to be created in a migration, but since we can't overwrite
modified data, we can't delete them on revert. For the same reason, we
have to check whether the record already exists when applying a
migration that creates them.

Records in this category can either use well-known primary keys (not
always an option), or the migration will have to be tailored to
identify the particular record in whatever way the application
looks it up.

## Sample Data

Our system ships with some builtin sample data in a fresh install for
training purposes and for the customer's convenience. This sample data
is usually altered by the user, but it's not required for the
application to run correctly, and the user could create it themselves
if needed. It's not really appropriate for a migration, and should be
populated with a separate script. Since the sample data won't be
altered when migrations are applied (at least not in a freshly-built
database), it's important for the sample data's population script to
be kept up-to-date with the current application format[^3].

[^3] This is actually a considerable drawback of this policy:
maintaining a change script with a lot of data is cumbersome, because
you have to effectively simulate database changes on the static data
in the script.

## Format Changes

This category consists of changes that affect the "physical" storage
of a single logical entity in the database. For example, converting a
stringly-typed column to an appropriate non-string type, or renaming a
column. Since the code depends on these changes to function, they must
go in a migration. The values involved are user-edited, but the
logical values are preserved over the migration, so these migrations
may be applied and reverted freely.

## Data Fixups

Data fixups are like format changes, except that they're meant to
clean up problems that may or may not exist. We've occasionally had
early testing code that has created records with typoed names or
duplicate records that cause inconsistent behavior. Obviously these
issues shouldn't make it into production, but it's useful to fix them
in cases where they do, and developer systems will frequently benefit
from those fixes. Because the issue may not be present in any given
database, and because these are mistaken records, the migration should
be prepared to work in a clean environment, and a revert should be a
no-op. It is very important to emphasize that this does _not_ apply to
malformed records _that are used by the application_. In that case the
value may be fixed in a migration, but it must be reverted to the
original form to prevent the application from erroring.

The handling of data in database migrations isn't discussed much. The
documentation for systems like Rails or Django usually point out that
it's possible and provide a trivial example, and developer discussion
usually starts and ends with "don't do that, ever," but without
explaining _why_.
