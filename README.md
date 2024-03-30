# Pixelframe: Multiplayer canvas

#### Pixelframe is a rewrite of the [Pixelflut Project](https://github.com/defnull/pixelflut), compatible with Python 3.

I created this on one afternoon, so most of the code is very sketchy and copied from the [original repository](https://github.com/defnull/pixelflut) and [custom modifications](https://git.leon.wtf/leon/pixelflut). I haven't checked everything, so don't mind to open a pull request if you have some improvements :)

## Usage: The Pixelflut Protocol

Pixelflut defines four main commands that are always supported to get you started:

* `HELP`: Returns a short introductional help text.
* `SIZE`: Returns the size of the visible canvas in pixel as `SIZE <w> <h>`.
* `PX <x> <y>` Return the current color of a pixel as `PX <x> <y> <rrggbb>`.
* `PX <x> <y> <rrggbb(aa)>`: Draw a single pixel at position (x, y) with the specified hex color code.
  If the color code contains an alpha channel value, it is blended with the current color of the pixel.

You can send multiple commands over the same connection by terminating each command with a single newline character (`\n`).

Example:

    $ echo "SIZE" | nc pixelflut.example.com 1234
    SIZE 800 600
    $ echo "PX 23 42 ff8000" | nc pixelflut.example.com 1234
    $ echo "PX 32 42" | nc pixelflut.example.com 1234
    PX 23 42 ff8000

Implementations MAY support additional commands or have less strict parsing rules (e.g. allow `\r\n` or any whitespace between parameters) but they MUST support the commands above.


## Server
### Installation

```shell
cd pixelframe
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Starting

```shell
python3 pixelframe.py
```