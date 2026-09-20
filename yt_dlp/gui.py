import json
import os
from datetime import datetime
from pathlib import Path

import yt_dlp


VIDEO_FORMATS = {
    'Melhor qualidade': ('bv*+ba/b', None),
    'MP4 compatível': ('bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', 'mp4'),
    '720p': ('bv*[height<=720]+ba/b[height<=720]/b', 'mp4'),
    '480p': ('bv*[height<=480]+ba/b[height<=480]/b', 'mp4'),
}
AUDIO_FORMATS = ('mp3', 'm4a', 'opus', 'wav', 'flac')
AUDIO_QUALITIES = ('320K', '256K', '192K', '128K', '96K')


def history_path():
    config_dir = os.environ.get('XDG_CONFIG_HOME')
    if config_dir:
        return Path(config_dir) / 'yt-dlp-gui' / 'history.json'
    return Path.home() / '.config' / 'yt-dlp-gui' / 'history.json'


class DownloadHistory:
    def __init__(self, path=None):
        self.path = Path(path) if path else history_path()
        self.entries = self._load()

    def _load(self):
        try:
            with self.path.open(encoding='utf-8') as history_file:
                entries = json.load(history_file)
            return entries if isinstance(entries, list) else []
        except (OSError, ValueError):
            return []

    def add(self, *, title, url, location, media_type, format_name):
        entry = {
            'title': title or 'Sem título',
            'url': url,
            'location': str(location),
            'media_type': media_type,
            'format': format_name,
            'downloaded_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        }
        self.entries.insert(0, entry)
        self.entries = self.entries[:500]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as history_file:
            json.dump(self.entries, history_file, ensure_ascii=False, indent=2)
        return entry


class GuiLogger:
    def __init__(self, report):
        self.report = report

    def debug(self, message):
        if not message.startswith('[debug] '):
            self.info(message)

    def info(self, message):
        self.report(message)

    def warning(self, message):
        self.report(f'Aviso: {message}')

    def error(self, message):
        self.report(f'Erro: {message}')


def main():
    try:
        from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtWidgets import (
            QApplication, QComboBox, QFileDialog, QFormLayout, QGridLayout, QGroupBox,
            QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
            QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
        )
    except ImportError as error:
        raise SystemExit('Instale a interface com: pip install -e ".[gui]"') from error

    class DownloadWorker(QObject):
        progress = Signal(float)
        message = Signal(str)
        finished = Signal(str, str, object)
        failed = Signal(str)

        def __init__(self, url, options, destination):
            super().__init__()
            self.url, self.options, self.destination = url, options, destination
            self.files = []

        @Slot()
        def run(self):
            def report(message):
                self.message.emit(message)

            def hook(data):
                if data.get('status') == 'downloading':
                    total = data.get('total_bytes') or data.get('total_bytes_estimate')
                    self.progress.emit(data.get('downloaded_bytes', 0) / total * 100 if total else 0)
                elif data.get('status') == 'finished' and data.get('filename'):
                    self.files.append(data['filename'])
                    self.message.emit('Processando arquivo...')

            self.options['logger'] = GuiLogger(report)
            self.options['progress_hooks'] = [hook]
            try:
                with yt_dlp.YoutubeDL(self.options) as downloader:
                    result = downloader.download([self.url])
                if result:
                    raise RuntimeError(f'yt-dlp retornou o código {result}')
                self.finished.emit(self.url, str(self.destination), list(dict.fromkeys(self.files)))
            except Exception as error:  # noqa: BLE001
                self.failed.emit(str(error))

    class YTDlpGui(QMainWindow):
        def __init__(self):
            super().__init__()
            self.history = DownloadHistory()
            self.thread = None
            self.worker = None
            self.setWindowTitle('yt-dlp GUI - Feito por IA')
            self.resize(980, 650)
            self._build()
            self._refresh_history()

        def _build(self):
            central = QWidget()
            main = QVBoxLayout(central)
            form = QFormLayout()
            self.url = QLineEdit()
            self.url.setPlaceholderText('https://www.youtube.com/watch?v=...')
            self.output_dir = QLineEdit(str(Path.home() / 'Downloads' / 'yt-dlp'))
            choose = QPushButton('Escolher...')
            choose.clicked.connect(self._choose_output)
            output_row = QHBoxLayout()
            output_row.addWidget(self.output_dir)
            output_row.addWidget(choose)
            output_widget = QWidget()
            output_widget.setLayout(output_row)
            self.output_folder = QLineEdit()
            self.output_folder.setPlaceholderText('ex.: Música ou Cursos/2026')
            form.addRow('URL do vídeo ou playlist', self.url)
            form.addRow('Local de saída', output_widget)
            form.addRow('Subpasta', self.output_folder)
            main.addLayout(form)

            options_box = QGroupBox('Formato')
            options = QGridLayout(options_box)
            self.media_type = QComboBox()
            self.media_type.addItems(['Vídeo', 'Áudio'])
            self.media_type.currentTextChanged.connect(self._toggle_format_fields)
            self.video_format = QComboBox()
            self.video_format.addItems(VIDEO_FORMATS)
            self.audio_format = QComboBox()
            self.audio_format.addItems(AUDIO_FORMATS)
            self.audio_quality = QComboBox()
            self.audio_quality.addItems(AUDIO_QUALITIES)
            self.audio_quality.setCurrentText('192K')
            options.addWidget(QLabel('Tipo'), 0, 0)
            options.addWidget(QLabel('Formato de vídeo'), 0, 1)
            options.addWidget(QLabel('Formato de áudio'), 0, 2)
            options.addWidget(QLabel('Qualidade'), 0, 3)
            options.addWidget(self.media_type, 1, 0)
            options.addWidget(self.video_format, 1, 1)
            options.addWidget(self.audio_format, 1, 2)
            options.addWidget(self.audio_quality, 1, 3)
            main.addWidget(options_box)

            actions = QHBoxLayout()
            self.download_button = QPushButton('Baixar')
            self.download_button.clicked.connect(self._start_download)
            clear_button = QPushButton('Limpar histórico')
            clear_button.clicked.connect(self._clear_history)
            self.status = QLabel('Pronto')
            actions.addWidget(self.download_button)
            actions.addWidget(clear_button)
            actions.addStretch()
            actions.addWidget(self.status)
            main.addLayout(actions)
            self.progress = QProgressBar()
            main.addWidget(self.progress)

            self.history_view = QTableWidget(0, 4)
            self.history_view.setHorizontalHeaderLabels(['Título', 'Tipo', 'Localização', 'Baixado em'])
            self.history_view.horizontalHeader().setStretchLastSection(True)
            self.history_view.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.history_view.cellDoubleClicked.connect(self._open_history_location)
            main.addWidget(self.history_view, 1)
            self.setCentralWidget(central)
            self._toggle_format_fields('Vídeo')

        def _toggle_format_fields(self, media_type):
            is_audio = media_type == 'Áudio'
            self.video_format.setEnabled(not is_audio)
            self.audio_format.setEnabled(is_audio)
            self.audio_quality.setEnabled(is_audio)

        def _choose_output(self):
            selected = QFileDialog.getExistingDirectory(self, 'Escolher local de saída', self.output_dir.text())
            if selected:
                self.output_dir.setText(selected)

        def _make_options(self):
            base = Path(self.output_dir.text()).expanduser().resolve()
            folder = self.output_folder.text().strip().strip('/\\')
            folder_path = Path(folder)
            if folder_path.is_absolute() or '..' in folder_path.parts:
                raise ValueError('A subpasta deve ficar dentro do local de saída escolhido.')
            destination = base / folder_path
            destination.mkdir(parents=True, exist_ok=True)
            options = {'outtmpl': str(destination / '%(title)s [%(id)s].%(ext)s'), 'quiet': True}
            if self.media_type.currentText() == 'Áudio':
                options.update(format='bestaudio/best', postprocessors=[{
                    'key': 'FFmpegExtractAudio', 'preferredcodec': self.audio_format.currentText(),
                    'preferredquality': self.audio_quality.currentText().rstrip('K')}])
            else:
                format_spec, merge_format = VIDEO_FORMATS[self.video_format.currentText()]
                options['format'] = format_spec
                if merge_format:
                    options['merge_output_format'] = merge_format
            return options, destination

        def _start_download(self):
            if not self.url.text().strip():
                QMessageBox.warning(self, 'URL ausente', 'Informe uma URL para iniciar o download.')
                return
            if self.thread and self.thread.isRunning():
                return
            try:
                options, destination = self._make_options()
            except ValueError as error:
                QMessageBox.warning(self, 'Subpasta inválida', str(error))
                return
            self.download_button.setEnabled(False)
            self.progress.setValue(0)
            self.status.setText('Iniciando...')
            self.thread = QThread(self)
            self.worker = DownloadWorker(self.url.text().strip(), options, destination)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(lambda value: self.progress.setValue(round(value)))
            self.worker.message.connect(lambda message: self.status.setText(message[-100:]))
            self.worker.finished.connect(self._download_finished)
            self.worker.failed.connect(self._download_failed)
            self.worker.finished.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)
            self.thread.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

        @Slot(str, str, object)
        def _download_finished(self, url, destination, files):
            format_name = self.audio_format.currentText() if self.media_type.currentText() == 'Áudio' else self.video_format.currentText()
            for downloaded_file in files or [destination]:
                path = Path(downloaded_file)
                if self.media_type.currentText() == 'Áudio' and path != Path(destination):
                    path = path.with_suffix(f'.{self.audio_format.currentText()}')
                self.history.add(title=path.stem if path != Path(destination) else url, url=url, location=path,
                                 media_type=self.media_type.currentText(), format_name=format_name)
            self._refresh_history()
            self.progress.setValue(100)
            self.status.setText('Download concluído')
            self.download_button.setEnabled(True)

        def _download_failed(self, error):
            self.status.setText('Falha no download')
            self.download_button.setEnabled(True)
            QMessageBox.critical(self, 'Download não concluído', error)

        def _refresh_history(self):
            self.history_view.setRowCount(0)
            for entry in self.history.entries:
                row = self.history_view.rowCount()
                self.history_view.insertRow(row)
                values = (entry.get('title'), entry.get('media_type'), entry.get('location'), entry.get('downloaded_at', '').replace('T', ' '))
                for column, value in enumerate(values):
                    self.history_view.setItem(row, column, QTableWidgetItem(str(value)))

        def _clear_history(self):
            if QMessageBox.question(self, 'Limpar histórico', 'Remover todos os registros do histórico?') == QMessageBox.StandardButton.Yes:
                self.history.entries = []
                self.history.path.unlink(missing_ok=True)
                self._refresh_history()

        def _open_history_location(self, row, _column):
            location = Path(self.history_view.item(row, 2).text())
            if location.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(location.parent if location.is_file() else location)))

    app = QApplication.instance() or QApplication([])
    window = YTDlpGui()
    window.show()
    return app.exec()


if __name__ == '__main__':
    main()