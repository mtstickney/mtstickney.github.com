Title: Infrastructure Notes: Pelican Setup
Date: 2015-04-26
Category: Blog
Tags: infrastructure note, blog, meta, pelican, github-pages

>  I have slipped the surly bonds of Octopress  
>  pulled the trigger  
>  and converted this sucker to Pelican.  
>  -- definitely not John Gillespie Magee, Jr.[^1]

[^1]:
  This is a shameless ripoff of John Gillespie Magee Jr.'s fabulous
  poem
  [High Flight](http://www.woodiescciclub.com/high-flight.htm). You
  should go read it.

This blog used to be powered by [Octopress](http://octopress.org), but
I've just finished converting the whole thing to
[Pelican](http://blog.getpelican.com), and wanted to make a few notes
about the switch and the current setup.

## Updates

- _2020-05-16_: Fix broken links, update new-machine setup to use
  fixed theme, and add some extra details about deploying and
  committing that aren't obvious.
- _2015-09-01_: Deploy script was updated to remove the output files
  before regenerating the site.

## Why Switch?

First though, a comment about my reasons for switching: Octopress is a
solid piece of software, with good out-of-the-box settings for the
sort of blogging I want to do (and probably for most blogs in
general). So why the switch? In my case, the two killer issues were
Ruby and the deployment scenario.

Getting Ruby to run on Windows is an absolute nightmare (mainly a
problem with gems). I generally prefer Linux systems, but some of my
machines are Windows-based and the harder it is to update the site the
less likely I am to actually do it. I'm also not as familiar with
Ruby, so the barrier for hacking on Octopress is higher, although I
doubt I'd have needed to do so.

Octopress is designed to run on the github-pages platform, and has
Rake tasks to support updating and deploying the site. Unfortunately
it's not completely clear what these are actually doing -- they commit
the contents of a folder to the `master` or `gh-pages` branch of a
repo, which is an unusual operation in git -- which makes it easy to
make mistakes. I use git every day, and I still managed to commit the
generated site but not my article source. On top of that, you get
octopress by forking the author's repo, which makes it tricky to
update octopress itself.

Octopress' author has [noted][octopress-3.0] the issues with the
deployment process, and has plans to fix them in a future version, but
that still leaves me with the Ruby issues. "Figure out Octopress" has
been on my To-Do list for so long that I'm not actually writing (last
post was more than a year ago), which in the end is the whole point,
so after much procrastinating I'm pulling the trigger and switching to
Pelican.

[octopress-3.0]: http://octopress.org/2015/01/15/octopress-3.0-is-coming/

## The Setup

First, create a virtualenv for the site in question:

    $ mkdir my_site/ && cd my_site/
    $ virtualenv .
    $ source Scripts/activate

Next, install the pelican components and create the project skeleton:

    $ pip install pelican markdown typogrify
    $ pelican-quickstart

It's not a great idea to add the virtualenv components to the git
repo, but we do want to track the installed components so setup on a
new machine is easy. The best way I've found to do that is to save the
requirements list from pip:

    $ pip -l freeze > requirements.txt

You'll want to add Pelican's files, the requirements file, and any
existing content (but not the `output/` folder just yet):

    $ git add pelicanconf.py \
              publishconf.py \
              Makefile \
              fabfiile.py \
              develop_server.sh \
              requirements.txt \
              content/
    $ git commit -m 'Add Pelican files.'

I like Octopress' default theme, so I'm using the
[pelican-octopress][pelican-octopress] theme. There is a small
issue with the github scripts it uses for the sidebar, but I'm hoping
to submit a patch for that shortly. This is also the one and only part
of the site that I haven't figured out how to store in the main repo
yet (a submodule would probably do it). Installation:

[pelican-octopress]: https://github.com/duilio/pelican-octopress-theme

    $ git clone https://github.com/duilio/pelican-octopress-theme.git ../pelican-octopress
    $ pelican-theme -i ../pelican-octopress

## Github Pages

Getting Pelican's output into the right branch for Github Pages can be
a little tricky to wrangle (this was the most confusing part of
Octopress for me), but there are several ways to approach the
problem. I chose to stick with Octopress' `source` and `master` (or
`gh-pages`) branch scheme, where the code for generating the site
resides in the `source` branch of the same repo as the site. Using an
external repo could also work, but I didn't want the clutter.

Instead of using an existing script like `ghp-import` and trying to
convince it to use `master` instead of `gh-pages`, I was able to roll
my own deployment script quite easily using `git subtree`.

The first thing to do is to add the `output/` directory as a subtree
from the master branch:

    $ git subtree add --prefix output/ origin master

Then we can use a deployment script to generate the site, commit the
changes, and push the generated content to the master branch:

    #!/bin/sh
    
    OUTPUT_DIR=output
    # Generate fresh production output
    rm -rf "$OUTPUT_DIR"
    pelican -s publishconf.py
    
    # Just to be safe, make sure we don't commit already-staged changes
    git reset HEAD
    
    # Add and commit the new output
    git add --all "$OUTPUT_DIR"
    DATE=$(date -u "+%Y-%m-%d %H:%M:%S %Z")
    git commit -m "Site updated at $DATE"
    
    # Push it to the remote
    git subtree push --prefix "$OUTPUT_DIR" origin master

Works like a charm, and I (now) know exactly what it's doing. The only
thing missing is `git pull`ing the new `master`, but you generally
won't even have it checked out locally.

## New Machine Setup

With all that in place, setup on a new machine is pretty
straightforward, assuming Python is already installed:

    $ git clone https://github.com/mtstickney/mtstickney.github.com site
    $ # There is a bug with script loading in the upstream theme, so pull a fixed version.
    $ # git clone https://github.com/duilio/pelican-octopress-theme.git pelican-octopress
    $ git clone -b script_fixes https://github.com/mtstickney/pelican-octopress-theme.git pelican-octopress
    $ cd site
    $ virtualenv .
    $ source Scripts/activate
    $ pip install -r requirements.txt
    $ pelican-themes -i ../pelican-octopress
    $ <write write write>
    $ <optionally commit source>
    $ ./deploy.sh
    $ <commit source> (for deployed site update)
