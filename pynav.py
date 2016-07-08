import ConfigParser
import os

import geany        # pylint: disable=import-error
import gtk


class PyNav(geany.Plugin):

    __plugin_name__ = 'Python Navigation'
    __plugin_version__ = '0.1.0'
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
            if cfg.has_option('python_env', 'path'):
                self.python_path = cfg.get('python_env', 'path').split(':')

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
    if dotted_path.startswith('.'):
        return find_module_relative(dotted_path, base_filename)
    names = dotted_path.split('.')
    if base_filename:
        python_path = python_path + [os.path.dirname(base_filename)]
    return find_names_under(names, python_path)


def find_module_relative(dotted_path, base_filename):
    if not base_filename:
        return None
    names = dotted_path.split('.')
    location = base_filename
    while names and names[0] == '':
        names.pop(0)
        location = os.path.dirname(location)
    return find_names_under(names, [location])


def find_names_under(names, base_dirs):
    for base_dir in base_dirs:
        for rel_fn in ['/'.join(names) + '.py',
                       '/'.join(names) + '/__init__.py']:
            candidate = os.path.join(base_dir, rel_fn)
            if os.path.isfile(candidate):
                return candidate
    return None


def jump_to_file(filename):
    old_document = geany.document.get_current()
    new_document = geany.document.open_file(filename)
    if new_document:
        geany.navqueue.goto_line(old_document, new_document, 1)
