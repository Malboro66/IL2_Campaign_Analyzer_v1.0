import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTabWidget

class IL2CampaignAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('IL-2 Sturmovik Campaign Analyzer')
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.path_label = QLabel('Nenhum caminho selecionado')
        self.layout.addWidget(self.path_label)

        self.select_path_button = QPushButton('Selecionar Pasta PWCGFC')
        self.select_path_button.clicked.connect(self.select_pwcgfc_folder)
        self.layout.addWidget(self.select_path_button)

        self.tabs = QTabWidget()
        self.tab_pilot_profile = QWidget()
        self.tab_squad = QWidget()
        self.tab_aces = QWidget()
        self.tab_missions = QWidget()

        self.tabs.addTab(self.tab_pilot_profile, 'Pilot Profile')
        self.tabs.addTab(self.tab_squad, 'Squad')
        self.tabs.addTab(self.tab_aces, 'Aces')
        self.tabs.addTab(self.tab_missions, 'Missions')

        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

    def select_pwcgfc_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta PWCGFC')
        if folder_path:
            self.path_label.setText(f'Caminho selecionado: {folder_path}')
            # TODO: Salvar o caminho para consultas posteriores

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IL2CampaignAnalyzer()
    ex.show()
    sys.exit(app.exec_())


