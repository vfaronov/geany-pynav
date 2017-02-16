import ConfigParser
import itertools
import os

import geany        # pylint: disable=import-error
import gtk


class PyNav(geany.Plugin):

    __plugin_name__ = 'Python Navigation'
    __plugin_version__ = '0.2.0'
    __plugin_description__ = 'Navigate a Python codebase quicker'
    __plugin_author__ = 'Vasiliy Faronov <vfaronov@gmail.com>'

    def __init__(self):
        super(PyNav, self).__init__()
        # pylint: disable=no-member
        self.menu_item = gtk.MenuItem('Jump to P_ython module')
        self.menu_item.connect('activate', self.on_activate)
        geany.main_widgets.tools_menu.append(self.menu_item)
        self.menu_item.show()

        self.key_group = self.set_key_group('pynav', 1)
        self.key_group.add_key_item('jump_to_module', 'Jump to Python module',
                                    self.on_activate)

        self.python_path = []
        geany.signals.connect('project-open', self.on_project_open)
        geany.signals.connect('project-close', self.on_project_close)
        self.load_project_config()

    def cleanup(self):
        self.menu_item.destroy()

    def on_project_open(self, *_args):
        self.load_project_config()

    def on_project_close(self, *_args):
        self.unload_project_config()

    def load_project_config(self):
        if geany.app.project is not None:
            cfg = ConfigParser.ConfigParser()
            cfg.read([geany.app.project.file_name])
            if cfg.has_option('pynav', 'path'):
                # `os.pathsep` is used as for ``PYTHONPATH``; see
                # https://docs.python.org/2/using/cmdline.html
                self.python_path = cfg.get('pynav', 'path').split(os.pathsep)
                # Remove blanks
                self.python_path = [p for p in self.python_path if p]

    def unload_project_config(self):
        self.python_path = []

    def on_activate(self, *_args):
        cur_doc = geany.document.get_current()
        dotted_path = guess_dotted_path(cur_doc) or prompt_dotted_path()
        if not dotted_path:
            return
        new_filename = find_module(dotted_path,
                                   cur_doc.file_name if cur_doc else None,
                                   self.python_path)
        if new_filename:
            jump_to_file(new_filename)


def guess_dotted_path(document):
    if document is None:
        return None
    scintilla = document.editor.scintilla
    selection = scintilla.get_selection_contents()
    if selection:
        return selection
    line = scintilla.get_line(scintilla.get_current_line()).lstrip()
    # TODO: handle multiline imports.
    if line.startswith('from ') or line.startswith('import '):
        words = line.split()
        if len(words) > 1:
            return words[1]
    return None


def prompt_dotted_path():
    return geany.dialogs.show_input('Jump to Python module',
                                    geany.main_widgets.window,
                                    'Dotted path:')


def find_module(dotted_path, base_filename, python_path):
    names = dotted_path.split('.')
    if names[0] == '':
        return find_names_relative(names, base_filename)
    if base_filename:
        # Augment the explicitly provided `python_path` with some guesses,
        # but avoid doing the actual guesswork until we've tried the explicit.
        python_path = itertools.chain(python_path,
                                      guess_python_path(base_filename))
    return find_names_under(names, python_path)


def find_names_relative(names, base_filename):
    if not base_filename:
        return None
    location = base_filename
    while names and names[0] == '':
        names.pop(0)
        location = os.path.dirname(location)
    return find_names_under(names, [location])


def guess_python_path(filename):
    # Try the current directory, for implicit relative imports.
    pos = start = os.path.dirname(filename)
    yield pos

    # Walk up the tree to find the first directory that has no ``__init__.py``.
    # That directory is the most likely Python path.
    while os.path.exists(os.path.join(pos, '__init__.py')):
        new_pos = os.path.dirname(pos)
        if new_pos == pos or not new_pos:        # Somehow we're at the root?..
            break
        pos = new_pos
    if pos != start:
        yield pos


def find_names_under(names, base_dirs):
    relative_filenames = [
        os.path.join(*names) + '.py',
        os.path.join(*(names + ['__init__.py'])),
    ]
    for base_dir in base_dirs:
        for rel_fn in relative_filenames:
            candidate = os.path.join(base_dir, rel_fn)
            if os.path.isfile(candidate):
                return candidate
    return None


def jump_to_file(filename):
    old_document = geany.document.get_current()
    new_document = geany.document.open_file(filename)
    if new_document:
        geany.navqueue.goto_line(old_document, new_document, 1)
