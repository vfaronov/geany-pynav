Geany Python Navigation plugin
==============================

This is a plugin for `Geany`__ to make it easier to navigate a Python codebase.

__ http://geany.org/

Currently, its only feature is "jump to Python module". It tries to
open the source file corresponding to a given Python module (dotted path).


Installation
------------

#. Install Geany 1.27+.

#. Install `GeanyPy`__.
   On Debian/Ubuntu, install ``geany-plugin-py``
   `as well as`__ ``python-gtk2``.

#. Put ``pynav.py`` on your `Geany plugin path`__,
   e.g. in ``~/.config/geany/plugins/``.

#. Open Geany's plugin manager (Tools → Plugin Manager)
   and enable GeanyPy and Python Navigation.

#. Click Keybindings to set your preferred key for "Jump to Python module".
   (This is optional: you can also invoke it from the Tools menu.)

__ http://plugins.geany.org/geanypy.html
__ https://bugs.launchpad.net/ubuntu/+source/geany-plugins/+bug/1592928
__ http://www.geany.org/manual/current/index.html#plugins


Usage
-----

When you press the chosen keybinding (or invoke Tools → Jump to Python module),
the plugin first tries to figure out which Python module name (dotted path)
you wish to look up:

#. if there is some selected text in the current document, then it is used;
#. otherwise, if the cursor is on a line beginning with ``import X``
   or ``from X``, then ``X`` is used;
#. otherwise, you are prompted to enter the dotted path manually.

Then the plugin tries to find the file corresponding to that module name.
For example, if the dotted path is ``foo.bar``, the plugin looks for
``foo/bar.py`` or ``foo/bar/__init__.py`` in a few places around the current
document.

You can also configure the search path on a per-project basis. To do so,
open your Geany project file (the one whose name ends in ``.geany``)
and add a section like this::

    [pynav]
    path=/home/user/project/src:/home/user/project/lib

then restart Geany (reopen the project).
The format is similar to that for ``PYTHONPATH``.
