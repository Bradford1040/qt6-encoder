# This is a KDE wrapper for ffmpeg

![screenshot](qt6-encoder-ss.png)

---

Open a terminal

```bash
git clone https://github.com/Bradford1040/qt6-encoder ~/qt6-encoder
```

Open your terminal and run this command to create the file:

```bash
nano ~/.local/share/applications/ffmpeg-encoder.desktop
```

- Paste the following block into Nano. Make sure to change the `/path/to/` directory on the `Exec=` line to wherever you actually have the main.py file saved (e.g., /home/<user-name>/qt6-encoder/main.py).

```bash
Ini, TOML
[Desktop Entry]
Type=Application
Name=FFmpeg Encoder
GenericName=Video Compressor
Comment=Custom GUI Wrapper for FFmpeg HEVC Encoding
Exec=python /path/to/your/main.py
Icon=video-x-generic
Terminal=false
Categories=AudioVideo;AudioVideoEditing;
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

Because Plasma dynamically monitors that folder, it should instantly appear in your KDE Application Menu under the Multimedia category. If you type "FFmpeg Encoder" into your KRunner or application search bar, it will pop right up, completely detached from the terminal.
