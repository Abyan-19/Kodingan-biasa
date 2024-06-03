import sys
import random
import json
import pygame
import math
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QRadioButton, QVBoxLayout, QWidget, QTextBrowser,
                             QMessageBox, QComboBox)
from datetime import datetime

pygame.mixer.init()


class MathQuiz(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kuis Matematika")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        background_image_path = "GUI(3)/background.png"
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url('{background_image_path}');
                background-repeat: no-repeat;
                background-position: center;
            }}
        """)

        font = QFont()
        font.setPointSize(18)

        self.start_button = QPushButton("Mulai Kuis")
        self.start_button.setFont(font)
        self.start_button.setStyleSheet("background-color: white;")
        self.start_button.clicked.connect(self.show_difficulty_selection_window)
        self.layout.addWidget(self.start_button)

        self.history_button = QPushButton("Lihat Riwayat")
        self.history_button.setFont(font)
        self.history_button.setStyleSheet("background-color: white;")
        self.history_button.clicked.connect(self.show_history)
        self.layout.addWidget(self.history_button)

        self.quit_button = QPushButton("Keluar")
        self.quit_button.setFont(font)
        self.quit_button.setStyleSheet("background-color: white;")
        self.quit_button.clicked.connect(self.close)
        self.layout.addWidget(self.quit_button)

        self.music_file = "GUI(3)/gameBGM.mp3"
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(-1)
            self.music_volume = 1
            pygame.mixer.music.set_volume(self.music_volume)
        except pygame.error as e:
            print(f"Error loading music file: {e}")
            QMessageBox.critical(self, "Error", f"Tidak dapat memutar file musik: {e}")

        self.history_file = "history.json"
        self.correct_answers = 0
        self.total_questions = 0

        self.difficulty_selection_window = DifficultySelectionWindow()
        self.difficulty_selection_window.difficulty_selected.connect(self.start_quiz)

    def show_difficulty_selection_window(self):
        self.difficulty_selection_window.show()

    def start_quiz(self, difficulty):
        self.questions, self.answers = generate_question(difficulty)
        if not self.questions or not self.answers:
            return

        self.current_difficulty = difficulty
        self.question_windows = []
        for i in range(0, len(self.questions), 5):
            question_number = i // 5 + 1
            question = self.questions[i]
            choices = self.questions[i + 1:i + 5]
            answer = self.answers[i // 5]
            question_window = QuestionWindow(question, choices, answer)
            question_window.setWindowTitle(f"Soal {question_number}")
            question_window.finished.connect(self.next_question)
            self.question_windows.append(question_window)

        self.current_question = 0
        self.show_current_question()

    def show_current_question(self):
        if self.current_question < len(self.question_windows):
            self.question_windows[self.current_question].resize(400, 400)
            self.question_windows[self.current_question].show()
            self.question_windows[self.current_question].activateWindow()

    def next_question(self):
        if self.current_question < len(self.question_windows):
            self.question_windows[self.current_question].close()

        self.current_question += 1
        if self.current_question < len(self.question_windows):
            self.show_current_question()
        else:
            self.show_result()

    def show_result(self, difficulty=None):
        if difficulty is None:
            difficulty = self.current_difficulty
            correct_answers = 0
            result_details = []

            for window in self.question_windows:
                if window.chosen_answer == window.answer:
                    correct_answers += 1
                result_details.append((window.question_label.text(), window.answer, window.chosen_answer))

            result_text = f"Anda berhasil menjawab {correct_answers} dari {len(self.question_windows)} soal dengan benar.\n\n"
            self.correct_answers += correct_answers
            self.total_questions += len(self.question_windows)

            history_entry = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "correct": correct_answers,
                "total": len(self.question_windows),
                "difficulty": self.current_difficulty,
                "details": [{"question": self.remove_bold_tags(q), "answer": a, "user_answer": u} for q, a, u in
                            result_details]
            }

            history_entries = []
            try:
                with open(self.history_file, "r", encoding='utf-8') as file:
                    content = file.read()
                    invalid_tags = ['<b>', '</b>', '<', '>', 'b', '/']
                    for invalid_tag in invalid_tags:
                        content = content.replace(invalid_tag, '')
                    content = content.replace('&u', 'ü')
                    history_entries = json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            history_entries.append(history_entry)

            if len(history_entries) > 20:
                history_entries = history_entries[-20:]

            with open(self.history_file, "w", encoding='utf-8') as file:
                json.dump(history_entries, file, indent=4)

            self.result_window = ResultWindow(result_text, result_details)
            self.result_window.show()

    def remove_bold_tags(self, text):
        return text.replace("<b>", "").replace("</b>", "")

    def show_history(self):
        self.history_window = HistoryWindow(self.history_file)
        self.history_window.load_history()
        self.history_window.show()


class DifficultySelectionWindow(QWidget):
    difficulty_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        self.setWindowTitle("Pilih Tingkat Kesulitan")

        font = QFont()
        font.setPointSize(18)

        label = QLabel("Pilih Tingkat Kesulitan Yang Diinginkan:")
        label.setFont(font)
        layout.addWidget(label)

        self.difficulty_combobox = QComboBox()
        self.difficulty_combobox.setFont(font)
        self.difficulty_combobox.addItems(["SD", "SMP"])
        self.difficulty_combobox.setStyleSheet("text-align: center;")
        layout.addWidget(self.difficulty_combobox)

        start_button = QPushButton("Mulai!")
        start_button.setFont(font)
        start_button.clicked.connect(self.start_quiz)
        layout.addWidget(start_button)

    def start_quiz(self):
        selected_difficulty = self.difficulty_combobox.currentText()
        self.difficulty_selected.emit(selected_difficulty)
        self.close()


class QuestionWindow(QWidget):
    finished = pyqtSignal()

    def __init__(self, question, choices, answer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kuis Matematika")
        self.chosen_answer = None

        layout = QVBoxLayout(self)

        font = QFont()
        font.setPointSize(18)

        self.question_label = QLabel()
        self.question_label.setFont(font)
        self.question_label.setTextFormat(Qt.RichText)
        self.set_bold_numbers(question)
        layout.addWidget(self.question_label)

        self.choice_buttons = []
        self.answer = answer

        for choice_text in choices:
            choice_button = QRadioButton(choice_text)
            choice_button.setFont(font)
            choice_button.toggled.connect(self.set_chosen_answer)
            layout.addWidget(choice_button)
            self.choice_buttons.append(choice_button)

        self.submit_button = QPushButton("Berikutnya")
        self.submit_button.setFont(font)
        self.submit_button.clicked.connect(self.submit_answer)
        layout.addWidget(self.submit_button)

    def set_bold_numbers(self, question):
        formatted_question = "".join(f"<b>{char}</b>" if char.isdigit() else char for char in question)
        self.question_label.setText(formatted_question)

    def set_chosen_answer(self):
        for button in self.choice_buttons:
            if button.isChecked():
                self.chosen_answer = button.text().split(".")[0].upper()
                return

    def submit_answer(self):
        if self.chosen_answer is None:
            QMessageBox.warning(self, "Peringatan", "Anda belum memilih jawaban.")
            return
        self.finished.emit()


class ResultWindow(QWidget):
    def __init__(self, result_text, result_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hasil Kuis")

        layout = QVBoxLayout(self)

        font = QFont()
        font.setPointSize(18)

        self.result_label = QLabel(result_text)
        self.result_label.setFont(font)
        layout.addWidget(self.result_label)

        for question, answer, user_answer in result_details:
            detail_label = QLabel(f"{question}\nJawaban Benar: {answer}, Jawaban Anda: {user_answer}\n")
            detail_label.setFont(font)
            layout.addWidget(detail_label)

        self.close_button = QPushButton("Tutup")
        self.close_button.setFont(font)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)


class HistoryWindow(QWidget):
    def __init__(self, history_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Riwayat Kuis")
        self.resize(400, 400)

        self.history_file = history_file
        layout = QVBoxLayout(self)

        font = QFont()
        font.setPointSize(14)

        self.history_text_browser = QTextBrowser()
        self.history_text_browser.setFont(font)
        self.history_text_browser.setReadOnly(True)
        layout.addWidget(self.history_text_browser)

    def load_history(self):
        try:
            with open(self.history_file, "r") as file:
                history_entries = json.load(file)
                if not history_entries:
                    self.history_text_browser.setPlainText("Belum ada riwayat kuis.")
                    return

                formatted_history = ""
                for i, entry in enumerate(history_entries):
                    timestamp = entry.get("timestamp", "")
                    correct = entry.get("correct", 0)
                    total = entry.get("total", 0)
                    difficulty = entry.get("difficulty",
                                           "")
                    result_details = entry.get("details", [])

                    formatted_history += f"Percobaan {i + 1}:\n"
                    formatted_history += f"Waktu: {timestamp}\n"
                    formatted_history += f"Tingkat Kesulitan: {difficulty}\n"
                    formatted_history += f"Jawaban Benar: {correct} dari {total}\n"

                    for detail in result_details:
                        question = detail.get('question', '')
                        answer = detail.get('answer', '')
                        user_answer = detail.get('user_answer', '')

                        formatted_history += f"Pertanyaan: {question}\n"
                        formatted_history += f"Angka Jawaban: {answer}\n"
                        formatted_history += f"Jawaban Anda: {user_answer}\n"
                    formatted_history += "\n"

                self.history_text_browser.setPlainText(formatted_history)
        except FileNotFoundError:
            self.history_text_browser.setPlainText("Belum ada riwayat kuis.")


def generate_question(difficulty):
    global answer, question
    questions = []
    answers = []

    if difficulty == "SD":
        for _ in range(10):
            num1 = random.randint(1, 15)
            num2 = random.randint(1, 5)
            if num1 < num2:
                num1, num2 = num2, num1

            operator = random.choice(["+", "-", "x", ":"])
            if operator == "+":
                answer = num1 + num2
            elif operator == "-":
                answer = num1 - num2
            elif operator == "x":
                answer = num1 * num2
            elif operator == ":":
                while num1 % num2 != 0:
                    num1 = random.randint(1, 15)
                    num2 = random.randint(1, 5)
                    if num1 < num2:
                        num1, num2 = num2, num1
                answer = num1 // num2

            correct_choice = random.choice(["A", "B", "C", "D"])

            choices = [answer]
            while len(choices) < 4:
                incorrect_answer = answer + random.randint(1, 5)
                if incorrect_answer not in choices:
                    choices.append(incorrect_answer)
            random.shuffle(choices)

            question = f"{num1} {operator} {num2} = ?"
            questions.append(question)
            for i, choice in enumerate(choices):
                questions.append(f"{chr(65 + i)}. {choice}")
                if choice == answer:
                    answers.append(chr(65 + i))

    elif difficulty == "SMP":
        for _ in range(15):
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 20)
            operator = random.choice(["+", "-", "x", ":", "^2", "√"])
            if operator == "+":
                answer = num1 + num2
                question = f"{num1} + {num2} = ?"
            elif operator == "-":
                answer = num1 - num2
                question = f"{num1} - {num2} = ?"
            elif operator == "x":
                answer = num1 * num2
                question = f"{num1} x {num2} = ?"
            elif operator == ":":
                num1 = random.randint(1, 30)
                num2 = random.randint(1, 10)
                if num1 < num2:
                    num1, num2 = num2, num1
                answer = num1 / num2
                question = f"{num1} : {num2} = ?"
            elif operator == "^2":
                answer = num1 ** 2
                question = f"{num1}^2 = ?"
            elif operator == "√":
                num1 = random.choice([i ** 2 for i in range(1, 21)])
                answer = int(math.sqrt(num1))
                question = f"√{num1} = ?"

            choices = [answer]
            while len(choices) < 4:
                incorrect_answer = answer + random.randint(1, 5)
                if incorrect_answer not in choices:
                    choices.append(incorrect_answer)
            random.shuffle(choices)

            questions.append(question)
            for i, choice in enumerate(choices):
                questions.append(f"{chr(65 + i)}. {choice}")
                if choice == answer:
                    answers.append(chr(65 + i))

    return questions, answers


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MathQuiz()
    main_window.setGeometry(800, 800, 800, 800)
    main_window.show()
    sys.exit(app.exec_())