import torch
from lavis.models import load_model_and_preprocess
from PIL import Image
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit, QProgressBar
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtCore import Qt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ImageCaptionEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.model, self.vis_processors, _ = load_model_and_preprocess(name="blip_caption", model_type="base_coco", is_eval=True, device=device)

        # Window setup
        self.setWindowTitle("Image Caption Editor")
        self.setGeometry(100, 100, 1000, 800)  # Adjusted window size

        # Main Layout
        main_layout = QVBoxLayout()

        # Image display
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)  # Minimum size for image display
        main_layout.addWidget(self.image_label)

        # Caption box
        self.caption_box = QTextEdit(self)
        self.caption_box.setMaximumHeight(100)  # Set maximum height for caption box
        main_layout.addWidget(self.caption_box)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        main_layout.addWidget(self.progress_bar)

        # Button Layout
        button_layout = QHBoxLayout()

        # Load Folder Button
        self.load_folder_button = QPushButton("Load Folder", self)
        self.load_folder_button.clicked.connect(self.load_folder)
        button_layout.addWidget(self.load_folder_button)

        # Previous Button
        self.prev_button = QPushButton("Previous Image", self)
        self.prev_button.clicked.connect(self.prev_image)
        button_layout.addWidget(self.prev_button)

        # Next Button
        self.next_button = QPushButton("Next Image", self)
        self.next_button.clicked.connect(self.next_image)
        button_layout.addWidget(self.next_button)

        # Save Button
        self.save_button = QPushButton("Save All Captions", self)
        self.save_button.clicked.connect(self.save_all_captions)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        # Container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Data
        self.image_files = []
        self.captions = {}
        self.current_image_index = 0

        # Keyboard Shortcuts
        self.next_button.setShortcut(QKeySequence("PgDown"))
        self.prev_button.setShortcut(QKeySequence("PgUp"))

    def create_caption(self, raw_image):
        image = self.vis_processors["eval"](raw_image).unsqueeze(0).to(device)
        caption = self.model.generate({"image": image})
        return caption[0]

    def load_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            self.load_captions(folder)
            self.current_image_index = 0
            self.display_image_and_caption()

    def load_captions(self, folder):
        self.progress_bar.setMaximum(len(self.image_files))
        for i, file_name in enumerate(self.image_files):
            caption_file_name = file_name.rsplit(".", 1)[0] + ".txt"
            if os.path.exists(caption_file_name):
                with open(caption_file_name, "r") as f:
                    caption = f.read()
            else:
                caption = self.create_caption(Image.open(file_name).convert("RGB"))
                with open(caption_file_name, "w") as f:
                    f.write(caption)
            self.captions[file_name] = caption
            self.progress_bar.setValue(i + 1)

    def update_current_caption(self):
        current_file = self.image_files[self.current_image_index]
        self.captions[current_file] = self.caption_box.toPlainText()

    def display_image_and_caption(self):
        if self.current_image_index < len(self.image_files):
            file_name = self.image_files[self.current_image_index]
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
            self.caption_box.setText(self.captions[file_name])

    def next_image(self):
        if self.current_image_index + 1 < len(self.image_files):
            self.update_current_caption()
            self.current_image_index += 1
            self.display_image_and_caption()

    def prev_image(self):
        if self.current_image_index > 0:
            self.update_current_caption()
            self.current_image_index -= 1
            self.display_image_and_caption()

    def save_all_captions(self):
        self.update_current_caption()
        for i, file_name in enumerate(self.image_files):
            caption_file_name = file_name.rsplit(".", 1)[0] + ".txt"
            with open(caption_file_name, "w") as f:
                f.write(self.captions[file_name])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = ImageCaptionEditor()
    mainWin.show()
    sys.exit(app.exec_())
