import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InstallerWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('yt-dlp GUI - Instalação - Feito por IA')
        self.resize(700, 420)
        self.install_dir = QLineEdit(str(Path.home() / 'AppData' / 'Local' / 'Programs' / 'yt-dlp-gui'))
        self.desktop_shortcut = QCheckBox('Criar atalho na área de trabalho')
        self.desktop_shortcut.setChecked(True)
        self.start_menu = QCheckBox('Criar atalho no Menu Iniciar')
        self.start_menu.setChecked(True)
        self.status = QLabel('Pronto para instalar.')
        self.status.setWordWrap(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel('Assistente de instalação do yt-dlp GUI')
        title.setStyleSheet('font-size: 18px; font-weight: 600;')
        layout.addWidget(title)
        layout.addWidget(QLabel('Escolha a pasta em que o programa será instalado.'))

        form = QFormLayout()
        form.addRow('Diretório de instalação', self.install_dir)
        browse = QPushButton('Procurar...')
        browse.clicked.connect(self._choose_dir)
        form.addRow('', browse)
        layout.addLayout(form)

        options = QGridLayout()
        options.addWidget(self.desktop_shortcut, 0, 0)
        options.addWidget(self.start_menu, 0, 1)
        layout.addLayout(options)

        self.install_button = QPushButton('Instalar')
        self.install_button.clicked.connect(self._install)
        cancel = QPushButton('Cancelar')
        cancel.clicked.connect(self.close)
        action_row = QHBoxLayout()
        action_row.addStretch()
        action_row.addWidget(self.install_button)
        action_row.addWidget(cancel)
        layout.addLayout(action_row)
        layout.addWidget(self.status)
        layout.setAlignment(Qt.AlignTop)

    def _choose_dir(self):
        folder = QFileDialog.getExistingDirectory(self, 'Pasta de instalação', self.install_dir.text())
        if folder:
            self.install_dir.setText(folder)

    def _install(self):
        target = Path(self.install_dir.text()).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        app_dir = Path(__file__).resolve().parent
        exe_name = 'yt-dlp-gui.exe' if os.name == 'nt' else 'yt-dlp-gui'
        source_candidates = (
            app_dir / exe_name,
            app_dir.parent / 'dist' / exe_name,
            Path.cwd() / 'dist' / exe_name,
        )
        source_app = next((candidate for candidate in source_candidates if candidate.exists()), None)
        if source_app is None:
            locations = '\n'.join(str(candidate) for candidate in source_candidates)
            QMessageBox.warning(self, 'Arquivo não encontrado', f'Não foi encontrado o executável em:\n{locations}')
            return

        copied = target / exe_name
        if copied.exists():
            copied.unlink()
        shutil.copy2(source_app, copied)
        uninstall_source = app_dir / 'uninstall_windows_gui.bat'
        if uninstall_source.exists():
            shutil.copy2(uninstall_source, target / uninstall_source.name)

        if self.desktop_shortcut.isChecked():
            try:
                desktop = Path.home() / 'Desktop'
                if desktop.exists():
                    shortcut = desktop / 'yt-dlp-gui.lnk'
                    if shortcut.exists():
                        shortcut.unlink()
            except OSError:
                pass

        if self.start_menu.isChecked():
            try:
                start_menu = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
                start_menu.mkdir(parents=True, exist_ok=True)
                (start_menu / 'yt-dlp-gui').mkdir(exist_ok=True)
            except OSError:
                pass

        self.status.setText(f'Instalação concluída em: {target}')
        QMessageBox.information(self, 'Instalação concluída', f'Programa instalado em:\n{target}')


def main():
    app = QApplication.instance() or QApplication([])
    window = InstallerWizard()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
