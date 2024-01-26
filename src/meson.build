pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'kaar'
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
   'blp/ui.blp',
   'blp/task.blp',
   'blp/preferences.blp',
   'blp/tab.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('kaar',
  'kaar.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'kaar.in',
  output: 'kaar',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

kaar_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'preferences_window.py',
  'model.py',
  'filtering.py',
  'sorting.py',
  'tab.py',
  'pseudo_async.py'
]

install_data(kaar_sources, install_dir: moduledir)
