# Kamm

A [todo.txt](http://todotxt.org) based to-do app

This app is currently in development; so for the love of yourself, please don't use it with your regular todo.txt file which you use primarily, as you never know when something bad happens with it.

# Build

Best way to build this is by Flatpak by cloning this repo in GNOME builder, or by using Flatpak extension in VS Code, and running it by flatpak; as you would not have to worry about dependencies or packages.

You may also build it by meson, without Flatpak by the commands:

```
meson build
cd build
sudo ninja install
```

The dependencies required for building by meson are:

- blueprint-compiler (Meson will automatically clone it if it is not present)
- python3
- gtk4
- libadwaita
- python-gobject
- gobject-introspection
- `pytodotxt` module from pip

(Note that these packages may be named alternately in some Linux/freedesktop distributions)

# Supported extensions on todo.txt

- Hidden Tasks (`h:1` hides the task)

# Inspiration

Features and UI of this app are derived from [Mindstream](https://github.com/xuhcc/mindstream) and [qtodotxt2](https://github.com/QTodoTxt/QTodoTxt2)

> Made with Python, GTK4, cosy Libadwaita 🥰 in India 🇮🇳