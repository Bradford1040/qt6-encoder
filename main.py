import sys
import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)


class EncodeWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                self.log_signal.emit(line.rstrip())

        return_code = process.wait()
        self.finished_signal.emit(return_code)


class EncoderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg Compression Wrapper")
        self.resize(700, 600)

        # Main Layout
        layout = QVBoxLayout()

        # 1. Video Input with Clear Button
        self.lbl_input = QLabel("Input Video: None")
        input_button_layout = QHBoxLayout()

        self.btn_input = QPushButton("Select Input MKV/MP4")
        self.btn_input.clicked.connect(self.select_input)

        self.btn_clear_input = QPushButton("Clear Input")
        self.btn_clear_input.clicked.connect(self.clear_input)

        input_button_layout.addWidget(self.btn_input)
        input_button_layout.addWidget(self.btn_clear_input)

        # 2. Subtitle Input with Clear Button
        self.lbl_sub = QLabel("Subtitle File: None (Will use built-in if left blank)")
        sub_button_layout = QHBoxLayout()

        self.btn_sub = QPushButton("Select Subtitle .SRT (Optional)")
        self.btn_sub.clicked.connect(self.select_subtitle)

        self.btn_clear_sub = QPushButton("Clear Subtitle")
        self.btn_clear_sub.clicked.connect(self.clear_subtitle)

        sub_button_layout.addWidget(self.btn_sub)
        sub_button_layout.addWidget(self.btn_clear_sub)

        # 3. Output Destination
        self.lbl_output = QLabel("Output File: None")
        self.btn_output = QPushButton("Set Output Destination")
        self.btn_output.clicked.connect(self.select_output)

        # Encoding Options (Radio Buttons for exclusive selection)
        options_layout = QHBoxLayout()

        self.radio_nvenc = QRadioButton("NVIDIA (nvenc)")
        self.radio_amf = QRadioButton("AMD (amf)")
        self.radio_cpu = QRadioButton("CPU (libx265)")
        self.radio_nvenc.setChecked(True)  # Default selection

        self.encoder_group = QButtonGroup()
        self.encoder_group.addButton(self.radio_nvenc)
        self.encoder_group.addButton(self.radio_amf)
        self.encoder_group.addButton(self.radio_cpu)

        self.lbl_bitrate = QLabel("Target Bitrate:")
        self.input_bitrate = QLineEdit("700k")
        self.input_bitrate.setFixedWidth(80)

        options_layout.addWidget(self.radio_nvenc)
        options_layout.addWidget(self.radio_amf)
        options_layout.addWidget(self.radio_cpu)
        options_layout.addStretch()  # Pushes bitrate box to the right
        options_layout.addWidget(self.lbl_bitrate)
        options_layout.addWidget(self.input_bitrate)

        # Live Terminal Output Console
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet(
            "background-color: #1e1e1e; color: #00ff00; font-family: monospace;"
        )

        # Run Button
        self.btn_run = QPushButton("START ENCODE")
        self.btn_run.setStyleSheet(
            "background-color: #2b5b84; color: white; font-weight: bold; padding: 8px;"
        )
        self.btn_run.clicked.connect(self.start_encoding)

        # Assemble UI Layout
        layout.addWidget(self.lbl_input)
        layout.addLayout(input_button_layout)
        layout.addSpacing(5)
        layout.addWidget(self.lbl_sub)
        layout.addLayout(sub_button_layout)
        layout.addSpacing(5)
        layout.addWidget(self.lbl_output)
        layout.addWidget(self.btn_output)
        layout.addSpacing(15)
        layout.addLayout(options_layout)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Live FFmpeg Output Log:"))
        layout.addWidget(self.log_console)
        layout.addWidget(self.btn_run)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.input_file = ""
        self.subtitle_file = ""
        self.output_file = ""
        self.worker = None

    def select_input(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.mkv)"
        )
        if file:
            self.input_file = file
            self.lbl_input.setText(f"Input Video: {file}")

    def clear_input(self):
        self.input_file = ""
        self.lbl_input.setText("Input Video: None")

    def select_subtitle(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle", "", "SubRip Subtitle (*.srt)"
        )
        if file:
            self.subtitle_file = file
            self.lbl_sub.setText(f"Subtitle File: {file}")

    def clear_subtitle(self):
        self.subtitle_file = ""
        self.lbl_sub.setText("Subtitle File: None (Will use built-in if left blank)")

    def select_output(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Video As", "", "Matroska (*.mkv)"
        )
        if file:
            self.output_file = file
            self.lbl_output.setText(f"Output File: {file}")

    def append_log(self, text):
        self.log_console.append(text)
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_encoding(self):
        if not self.input_file or not self.output_file:
            QMessageBox.warning(
                self,
                "Error",
                "Please select at least a video input and an output file.",
            )
            return

        bitrate = self.input_bitrate.text().strip()

        cmd = ["ffmpeg", "-i", self.input_file]

        if self.subtitle_file:
            cmd.extend(["-i", self.subtitle_file])
            cmd.extend(
                ["-map", "0:v", "-map", "0:a", "-map", "1:s", "-map_metadata", "0"]
            )
            sub_flags = [
                "-c:s",
                "srt",
                "-metadata:s:s:0",
                "language=eng",
                "-disposition:s:0",
                "default",
            ]
        else:
            cmd.extend(["-map", "0", "-map_metadata", "0"])
            sub_flags = ["-c:s", "copy"]

        # Hardware/CPU Selection Logic
        if self.radio_nvenc.isChecked():
            cmd.extend(["-c:v", "hevc_nvenc", "-preset", "slow", "-b:v", bitrate])
        elif self.radio_amf.isChecked():
            cmd.extend(["-c:v", "hevc_amf", "-b:v", bitrate, "-quality", "quality"])
        else:
            cmd.extend(
                ["-c:v", "libx265", "-crf", "28", "-preset", "fast", "-threads", "4"]
            )

        cmd.extend(["-c:a", "copy"])
        cmd.extend(sub_flags)
        cmd.extend(["-y", self.output_file])

        self.log_console.clear()
        self.btn_run.setEnabled(False)
        self.btn_input.setEnabled(False)
        self.btn_clear_input.setEnabled(False)
        self.btn_sub.setEnabled(False)
        self.btn_clear_sub.setEnabled(False)
        self.btn_output.setEnabled(False)
        self.radio_nvenc.setEnabled(False)
        self.radio_amf.setEnabled(False)
        self.radio_cpu.setEnabled(False)

        self.append_log(f"Executing: {' '.join(cmd)}\n" + ("=" * 50))

        self.worker = EncodeWorker(cmd)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.encoding_finished)
        self.worker.start()

    def encoding_finished(self, return_code):
        # Restore UI
        self.btn_run.setEnabled(True)
        self.btn_input.setEnabled(True)
        self.btn_clear_input.setEnabled(True)
        self.btn_sub.setEnabled(True)
        self.btn_clear_sub.setEnabled(True)
        self.btn_output.setEnabled(True)
        self.radio_nvenc.setEnabled(True)
        self.radio_amf.setEnabled(True)
        self.radio_cpu.setEnabled(True)

        # Save Log to File
        log_text = self.log_console.toPlainText()
        base_path = os.path.splitext(self.output_file)[0]
        log_file_path = f"{base_path}_encode_log.txt"

        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write(log_text)
            self.append_log(f"\n[INFO] Log file saved to: {log_file_path}")
        except Exception as e:
            self.append_log(f"\n[WARNING] Could not save log file: {e}")

        if return_code == 0:
            self.append_log("\n[SUCCESS] Encoding completed successfully.")
            QMessageBox.information(self, "Success", "Encoding Complete!")
        else:
            self.append_log(f"\n[ERROR] FFmpeg process exited with code {return_code}.")
            QMessageBox.critical(
                self, "Error", "Encoding failed. Check log for details."
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EncoderApp()
    window.show()
    sys.exit(app.exec())
