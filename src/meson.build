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

appstream_file = i18n.merge_file(
        input: 'net.hemish.kaar.metainfo.xml.in',
       output: 'net.hemish.kaar.metainfo.xml',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test('Validate appstream file', appstreamcli,
     args: ['validate', '--no-net', '--explain', appstream_file])

gnome.compile_resources('kaar',
  'kaar.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: [blueprints, appstream_file],
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
  'preferences.py',
  'model.py',
  'filtering.py',
  'sorting.py',
  'tab.py',
  'pseudo_async.py',
  'enums.py'
]

install_data(kaar_sources, install_dir: moduledir)
