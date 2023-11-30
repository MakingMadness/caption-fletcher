import torch
from lavis.models import load_model_and_preprocess
from PIL import Image
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTextEdit, QProgressBar, QSizePolicy
from PyQt5.QtGui import QPixmap, QKeySequence, QResizeEvent
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
import send2trash


class ImageCaptionEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.vis_processors, _ = load_model_and_preprocess(name="blip_caption", model_type="base_coco", is_eval=True, device=self.device)
        self.pasted_images = {}

        # Window setup
        self.setWindowTitle("Caption Fletcher")
        self.setGeometry(100, 100, 1000, 800)
        self.setWindowIcon(QIcon('images/logo.png'))

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setMaximumHeight(100)

        self.logo_label = QLabel(self)
        logo_pixmap = QPixmap('images/logo.png')
        self.logo_label.setPixmap(logo_pixmap.scaledToWidth(80, Qt.SmoothTransformation))
        self.logo_label.margin = 0
        header_layout.addWidget(self.logo_label)
        
        self.text_label = QLabel("Caption Fletcher", self)
        font = QFont()
        font.setPointSize(18)
        self.text_label.setFont(font)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.text_label)

        main_layout.addWidget(header_widget)
        main_layout.addLayout(header_layout)
        
        # Container
        container = QWidget()
        container.setLayout(main_layout)
        container.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(container)

        # Image display
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        # Caption box
        self.caption_box = QTextEdit(self)
        self.caption_box.setMaximumHeight(100)
        main_layout.addWidget(self.caption_box)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        main_layout.addWidget(self.progress_bar)

        # Button Layout
        button_layout = QHBoxLayout()

        # Load Folder Button
        self.load_folder_button = QPushButton("Load Folder", self)
        self.load_folder_button.clicked.connect(self.load_folder)
        self.load_folder_button.setIcon(QIcon('images/logo.png'))
        self.load_folder_button.setIconSize(QSize(24, 24))
        button_layout.addWidget(self.load_folder_button)

        # Previous Button
        self.prev_button = QPushButton("Previous <PgUp>", self)
        self.prev_button.clicked.connect(self.prev_image)
        button_layout.addWidget(self.prev_button)

        # Next Button
        self.next_button = QPushButton("Next <PgDn>", self)
        self.next_button.clicked.connect(self.next_image)
        button_layout.addWidget(self.next_button)

        # Save Button
        self.save_button = QPushButton("Save All <Ctrl+S>", self)
        self.save_button.clicked.connect(self.save_all_captions)
        button_layout.addWidget(self.save_button)

        # Delete Button
        self.delete_button = QPushButton("Delete <Del>", self)
        self.delete_button.clicked.connect(self.delete_image)
        button_layout.addWidget(self.delete_button)

        main_layout.addLayout(button_layout)
        
        main_layout.addWidget(container)

        # Data
        self.image_files = []
        self.captions = {}
        self.current_image_index = 0

        # Disable caption box and buttons
        self.caption_box.setDisabled(True)
        self.prev_button.setDisabled(True)
        self.next_button.setDisabled(True)
        self.save_button.setDisabled(True)
        self.progress_bar.setDisabled(True)
        self.delete_button.setDisabled(True)

        # Keyboard Shortcuts
        self.next_button.setShortcut(QKeySequence("PgDown"))
        self.prev_button.setShortcut(QKeySequence("PgUp"))
        self.save_button.setShortcut("Ctrl+S")
        self.delete_button.setShortcut("Delete")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.copy_image_to_clipboard()
        elif event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.paste_image_from_clipboard()
        else:
            super().keyPressEvent(event)

    def create_caption(self, raw_image):
        image = self.vis_processors["eval"](raw_image).unsqueeze(0).to(self.device)
        caption = self.model.generate({"image": image})
        return caption[0]

    def load_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.progress_bar.setDisabled(False)
            self.image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
            self.image_files.sort()
            self.load_captions(folder)
            self.current_image_index = 0
            self.display_image_and_caption()
            self.caption_box.setDisabled(False)
            self.prev_button.setDisabled(False)
            self.next_button.setDisabled(False)
            self.save_button.setDisabled(False)
            self.delete_button.setDisabled(False)
            self.progress_bar.setFormat("Manual captioning: %v/%m")
            self.progress_bar.setValue(1)
            self.progress_bar.textVisible = True

    def load_captions(self, folder):
        self.progress_bar.setMaximum(len(self.image_files))
        self.progress_bar.setFormat("Auto captioning images with BLIP: %p%")
        for i, file_name in enumerate(self.image_files):
            caption_file_name = file_name.rsplit(".", 1)[0] + ".txt"
            if os.path.exists(caption_file_name):
                with open(caption_file_name, "r") as f:
                    caption = f.read()
            else:
                caption = self.create_caption(Image.open(file_name).convert("RGB"))
            self.captions[file_name] = caption
            self.progress_bar.setValue(i + 1)

    def update_current_caption(self):
        current_file = self.image_files[self.current_image_index]
        self.captions[current_file] = self.caption_box.toPlainText()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        output = super().resizeEvent(a0)
        if len(self.image_files):
            file_name = self.image_files[self.current_image_index]
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        return output

    def display_image_and_caption(self):
        if self.current_image_index in self.pasted_images:
            # Display pasted image if present
            pixmap = self.pasted_images[self.current_image_index]
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        elif self.current_image_index < len(self.image_files) and self.image_files[
            self.current_image_index] is not None:
            # Normal behavior for displaying images from file
            file_name = self.image_files[self.current_image_index]
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
            self.caption_box.setText(self.captions[file_name])

    def next_image(self):
        if self.current_image_index + 1 < len(self.image_files):
            self.update_current_caption()
            self.current_image_index += 1
            self.display_image_and_caption()
            self.progress_bar.setValue(self.current_image_index + 1)

    def prev_image(self):
        if self.current_image_index > 0:
            self.update_current_caption()
            self.current_image_index -= 1
            self.display_image_and_caption()
            self.progress_bar.setValue(self.current_image_index + 1)

    def copy_image_to_clipboard(self):
        if self.current_image_index < len(self.image_files):
            clipboard = QApplication.clipboard()
            current_file = self.image_files[self.current_image_index]
            image = QPixmap(current_file)
            clipboard.setPixmap(image)

    def paste_image_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()

        if mimeData.hasImage():
            image = clipboard.image()
            pixmap = QPixmap.fromImage(image)
            self.pasted_images[self.current_image_index] = pixmap
            self.display_image_and_caption()

    def save_all_captions(self):
        self.update_current_caption()
        for i, file_name in enumerate(self.image_files):
            if file_name is not None:
                caption_file_name = file_name.rsplit(".", 1)[0] + ".txt"
                with open(caption_file_name, "w") as f:
                    f.write(self.captions[file_name])

                if i in self.pasted_images:
                    # Save pasted image
                    self.pasted_images[i].save(file_name)

    def delete_image(self):
        self.update_current_caption()
        current_file = self.image_files[self.current_image_index]
        try:
            send2trash.send2trash(current_file)
            send2trash.send2trash(current_file.rsplit(".", 1)[0] + ".txt")
        except OSError:
            pass
        self.image_files.pop(self.current_image_index)
        self.captions.pop(current_file)
        self.progress_bar.setMaximum(len(self.image_files))
        self.progress_bar.setValue(self.current_image_index + 1)
        if self.current_image_index >= len(self.image_files):
            self.current_image_index = len(self.image_files) - 1
        self.display_image_and_caption()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = ImageCaptionEditor()
    mainWin.show()
    sys.exit(app.exec_())
