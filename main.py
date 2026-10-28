
import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

APP_DIR = Path(__file__).resolve().parent
SAVE_FILE = APP_DIR / "player_data.json"

BG = "#0B1020"
CARD = "#151D32"
FIELD = "#202B45"
PURPLE = "#8B5CF6"
CYAN = "#22D3EE"
WHITE = "#F8FAFC"
MUTED = "#94A3B8"
GREEN = "#34D399"
RED = "#FB7185"
GOLD = "#FBBF24"


class NumberQuest:
    MODES = {
        "Easy": {"maximum": 20, "attempts": 8, "seconds": 90},
        "Medium": {"maximum": 50, "attempts": 7, "seconds": 60},
        "Hard": {"maximum": 100, "attempts": 8, "seconds": 45},
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Number Quest | Crack the Code")
        self.root.geometry("720x790")
        self.root.minsize(560, 700)
        self.root.configure(bg=BG)

        self.data = self.load_data()
        self.mode = tk.StringVar(value="Medium")
        self.secret = 0
        self.attempts = 0
        self.remaining = 0
        self.seconds_left = 0
        self.hints_left = 2
        self.game_over = True
        self.round_id = 0
        self.history = []
        self.achievements = set(self.data.get("achievements", []))

        self.build_ui()
        self.new_game()

    def load_data(self):
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid save data")
            return data
        except (OSError, ValueError, TypeError):
            return {
                "best_score": 0,
                "total_wins": 0,
                "streak": 0,
                "achievements": []
            }

    def save_data(self):
        self.data["achievements"] = sorted(self.achievements)
        try:
            SAVE_FILE.write_text(
                json.dumps(self.data, indent=2),
                encoding="utf-8"
            )
        except OSError:
            self.set_message(
                "Your game works, but progress could not be saved.",
                GOLD
            )

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(20, 12))

        tk.Label(
            header, text="✦ NUMBER QUEST ✦",
            font=("Segoe UI", 25, "bold"),
            bg=BG, fg=WHITE
        ).pack()

        tk.Label(
            header, text="CRACK THE CODE • UNLOCK THE VAULT",
            font=("Segoe UI", 10, "bold"),
            bg=BG, fg=CYAN
        ).pack(pady=(5, 0))

        self.card = tk.Frame(
            self.root, bg=CARD, padx=25, pady=20
        )
        self.card.pack(fill="both", expand=True, padx=28, pady=8)

        top = tk.Frame(self.card, bg=CARD)
        top.pack(fill="x")

        tk.Label(
            top, text="DIFFICULTY",
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.mode_menu = tk.OptionMenu(
            top, self.mode, *self.MODES.keys(),
            command=lambda _: self.new_game()
        )
        self.mode_menu.config(
            bg=FIELD, fg=WHITE,
            activebackground=PURPLE,
            activeforeground=WHITE,
            relief="flat", highlightthickness=0,
            font=("Segoe UI", 10)
        )
        self.mode_menu["menu"].config(
            bg=FIELD, fg=WHITE,
            activebackground=PURPLE,
            activeforeground=WHITE
        )
        self.mode_menu.pack(side="right")

        self.vault = tk.Label(
            self.card, text="🔐",
            font=("Segoe UI Emoji", 43),
            bg=CARD, fg=GOLD
        )
        self.vault.pack(pady=(15, 0))

        tk.Label(
            self.card, text="A secret number is waiting...",
            bg=CARD, fg=WHITE,
            font=("Segoe UI", 15, "bold")
        ).pack(pady=(0, 4))

        self.range_label = tk.Label(
            self.card, text="Find the number from 1 to 50",
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 10)
        )
        self.range_label.pack()

        stats = tk.Frame(self.card, bg=CARD)
        stats.pack(fill="x", pady=18)

        self.attempt_stat = self.stat(stats, "ATTEMPTS", "0/7")
        self.timer_stat = self.stat(stats, "TIME LEFT", "60s")
        self.score_stat = self.stat(stats, "SCORE", "0")
        self.streak_stat = self.stat(stats, "WIN STREAK", "0")

        tk.Label(
            self.card, text="ENTER YOUR GUESS",
            bg=CARD, fg=CYAN,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(2, 8))

        self.entry = tk.Entry(
            self.card, font=("Segoe UI", 22, "bold"),
            justify="center", bg=FIELD, fg=WHITE,
            insertbackground=WHITE, relief="flat",
            highlightthickness=2,
            highlightbackground=FIELD,
            highlightcolor=PURPLE
        )
        self.entry.pack(fill="x", ipady=9)
        self.entry.bind("<Return>", self.check_guess)

        self.message = tk.Label(
            self.card,
            text="Your mission starts now. Good luck!",
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 11),
            wraplength=530, justify="center"
        )
        self.message.pack(pady=14)

        self.history_label = tk.Label(
            self.card, text="GUESS HISTORY: —",
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=530
        )
        self.history_label.pack(pady=(0, 10))

        self.progress = tk.Label(
            self.card, text="Attempts remaining: 7",
            bg=CARD, fg=WHITE,
            font=("Segoe UI", 10, "bold")
        )
        self.progress.pack(pady=(0, 10))

        self.guess_button = self.button(
            self.card, "⚡ CRACK THE CODE",
            self.check_guess, PURPLE
        )
        self.guess_button.pack(fill="x")

        actions = tk.Frame(self.card, bg=CARD)
        actions.pack(fill="x", pady=(9, 0))

        self.hint_button = self.button(
            actions, "💡 Hint (2)", self.show_hint, FIELD
        )
        self.hint_button.pack(
            side="left", expand=True, fill="x", padx=(0, 5)
        )

        self.new_button = self.button(
            actions, "↻ New Mission", self.new_game, FIELD
        )
        self.new_button.pack(
            side="left", expand=True, fill="x", padx=(5, 0)
        )

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=30, pady=(7, 16))

        self.best_label = tk.Label(
            footer, text="", bg=BG, fg=GOLD,
            font=("Segoe UI", 10, "bold")
        )
        self.best_label.pack()

        self.achievement_label = tk.Label(
            footer, text="", bg=BG, fg=MUTED,
            font=("Segoe UI", 9), wraplength=620
        )
        self.achievement_label.pack(pady=(5, 0))

        self.refresh_footer()

    def stat(self, parent, title, value):
        box = tk.Frame(parent, bg=FIELD, padx=4, pady=9)
        box.pack(side="left", expand=True, fill="x", padx=3)

        tk.Label(
            box, text=title, bg=FIELD, fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack()

        label = tk.Label(
            box, text=value, bg=FIELD, fg=WHITE,
            font=("Segoe UI", 14, "bold")
        )
        label.pack(pady=(3, 0))
        return label

    def button(self, parent, text, command, color):
        return tk.Button(
            parent, text=text, command=command,
            font=("Segoe UI", 10, "bold"),
            bg=color, fg=WHITE,
            activebackground=CYAN,
            activeforeground=BG,
            relief="flat", cursor="hand2",
            borderwidth=0, padx=8, pady=12
        )

    def set_message(self, text, color=MUTED):
        self.message.config(text=text, fg=color)

    def new_game(self):
        self.round_id += 1
        settings = self.MODES[self.mode.get()]

        self.secret = random.randint(1, settings["maximum"])
        self.attempts = 0
        self.remaining = settings["attempts"]
        self.seconds_left = settings["seconds"]
        self.hints_left = 2
        self.game_over = False
        self.history = []

        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.guess_button.config(state="normal")
        self.hint_button.config(state="normal", text="💡 Hint (2)")
        self.vault.config(text="🔐", fg=GOLD)

        self.range_label.config(
            text=f"Find the secret number from 1 to {settings['maximum']}"
        )
        self.history_label.config(text="GUESS HISTORY: —")
        self.progress.config(
            text=f"Attempts remaining: {self.remaining}"
        )
        self.set_message(
            "Mission briefing: crack the code before time runs out!",
            CYAN
        )

        self.update_stats()
        self.root.after(100, self.entry.focus_set)
        self.tick(self.round_id)

    def tick(self, current_id):
        if current_id != self.round_id or self.game_over:
            return

        self.timer_stat.config(text=f"{self.seconds_left}s")

        if self.seconds_left <= 0:
            self.finish_game(False, "Time is up!")
            return

        self.seconds_left -= 1
        self.root.after(1000, lambda: self.tick(current_id))

    def check_guess(self, event=None):
        if self.game_over:
            return

        raw = self.entry.get().strip()

        if not raw:
            self.set_message("Type a number first!", RED)
            return

        try:
            guess = int(raw)
        except ValueError:
            self.set_message("Numbers only, please!", RED)
            return

        maximum = self.MODES[self.mode.get()]["maximum"]
        if not 1 <= guess <= maximum:
            self.set_message(
                f"Choose a number between 1 and {maximum}.", RED
            )
            return

        self.entry.delete(0, tk.END)

        if guess in self.history:
            self.set_message("You already tried that number. Try another!", GOLD)
            return

        self.attempts += 1
        self.remaining -= 1
        self.history.append(guess)

        self.history_label.config(
            text="GUESS HISTORY: " + "  •  ".join(map(str, self.history))
        )

        if guess == self.secret:
            self.finish_game(True, "Vault unlocked!")
        elif self.remaining <= 0:
            self.finish_game(False, "You ran out of attempts!")
        elif guess < self.secret:
            self.set_message("📈 Too low! Go higher.", CYAN)
        else:
            self.set_message("📉 Too high! Go lower.", RED)

        self.update_stats()

    def show_hint(self):
        if self.game_over:
            return

        if self.hints_left <= 0:
            self.set_message("No hints left. Trust your logic!", GOLD)
            return

        self.hints_left -= 1
        maximum = self.MODES[self.mode.get()]["maximum"]
        clues = [
            "The number is " + ("even." if self.secret % 2 == 0 else "odd."),
            f"The number is in the "
            f"{'lower' if self.secret <= maximum // 2 else 'upper'} half.",
            f"The number is {'below' if self.secret < maximum * 0.75 else 'at or above'} "
            f"{int(maximum * 0.75)}."
        ]

        clue = clues[2] if self.hints_left == 0 else clues[self.attempts % 2]
        self.set_message("💡 INTEL: " + clue, GOLD)
        self.hint_button.config(text=f"💡 Hint ({self.hints_left})")

        if self.hints_left == 0:
            self.hint_button.config(state="disabled")

    def finish_game(self, won, reason):
        self.game_over = True
        self.round_id += 1
        self.entry.config(state="disabled")
        self.guess_button.config(state="disabled")
        self.hint_button.config(state="disabled")

        if won:
            self.vault.config(text="🔓", fg=GREEN)

            points = max(
                10,
                self.remaining * 15 + self.seconds_left // 2
            )
            self.data["total_wins"] = self.data.get("total_wins", 0) + 1
            self.data["streak"] = self.data.get("streak", 0) + 1
            self.data["best_score"] = max(
                self.data.get("best_score", 0), points
            )

            unlocked = []
            if "First Victory" not in self.achievements:
                self.achievements.add("First Victory")
                unlocked.append("🏆 First Victory")

            if self.attempts <= 3 and "Sharp Shooter" not in self.achievements:
                self.achievements.add("Sharp Shooter")
                unlocked.append("🎯 Sharp Shooter")

            if self.data["streak"] >= 3 and "On Fire" not in self.achievements:
                self.achievements.add("On Fire")
                unlocked.append("🔥 On Fire")

            self.set_message(
                f"🎉 {reason} Secret number: {self.secret}. +{points} points!",
                GREEN
            )

            self.progress.config(
                text=f"MISSION COMPLETE • {self.attempts} guesses"
            )
            self.save_data()
            self.refresh_footer()
            self.update_stats()

            extra = "\n".join(unlocked)
            messagebox.showinfo(
                "Vault Unlocked!",
                f"Mission successful!\n\n"
                f"Secret number: {self.secret}\n"
                f"Guesses: {self.attempts}\n"
                f"Points: {points}\n"
                f"Winning streak: {self.data['streak']}"
                + (f"\n\nNew achievements:\n{extra}" if extra else "")
            )
        else:
            self.vault.config(text="🔒", fg=RED)
            self.data["streak"] = 0
            self.set_message(
                f"Mission failed! {reason} Secret number: {self.secret}.",
                RED
            )
            self.progress.config(text="MISSION FAILED • Try again!")
            self.save_data()
            self.refresh_footer()
            self.update_stats()
            messagebox.showinfo(
                "Mission Failed",
                f"{reason}\nThe secret number was {self.secret}.\n\n"
                "A new mission is waiting. Try again!"
            )

    def update_stats(self):
        maximum_attempts = self.MODES[self.mode.get()]["attempts"]
        self.attempt_stat.config(
            text=f"{self.attempts}/{maximum_attempts}"
        )
        self.timer_stat.config(text=f"{self.seconds_left}s")
        self.score_stat.config(
            text=str(self.data.get("best_score", 0))
        )
        self.streak_stat.config(
            text=str(self.data.get("streak", 0))
        )

    def refresh_footer(self):
        self.best_label.config(
            text=f"🏆 BEST SCORE: {self.data.get('best_score', 0)}"
        )
        names = sorted(self.achievements)
        self.achievement_label.config(
            text="ACHIEVEMENTS: " + (
                " • ".join(names) if names else "No badges yet — win your first mission!"
            )
        )


if __name__ == "__main__":
    root = tk.Tk()
    game = NumberQuest(root)
    root.mainloop()
