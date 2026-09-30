import os
import pygame

from .round import Round


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)


class GameEngine:
    def __init__(
        self,
        width,
        height,
        rounds_total=5,
        min_wait_ms=1000,
        max_wait_ms=3000
    ):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

        self.reaction_times = []
        self.result_shown_at = None
        self.result_pause_ms = 800

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.game_over = False
        self.exit_game = False

        # ---------------------------------
        # TASK 3 - DIFFICULTIES
        # ---------------------------------

        self.difficulties = {
            "Easy": (1500, 4000, 5),
            "Medium": (1000, 3000, 5),
            "Hard": (500, 2000, 5)
        }

        # ---------------------------------
        # TASK 4 - SOUND
        # ---------------------------------

        self.sound_enabled = False

        self.go_sound = None
        self.false_start_sound = None
        self.game_over_sound = None

        self._load_sounds()

    # =================================
    # TASK 4 - LOAD SOUNDS SAFELY
    # =================================

    def _load_sounds(self):
        """
        Load the three local sound files.

        If the mixer or any sound file cannot be loaded,
        the game continues without sound.
        """

        try:
            # Initialize the mixer only if necessary.
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            sounds_folder = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                "sounds"
            )

            go_path = os.path.join(
                sounds_folder,
                "go.wav"
            )

            false_start_path = os.path.join(
                sounds_folder,
                "false_start.wav"
            )

            game_over_path = os.path.join(
                sounds_folder,
                "game_over.wav"
            )

            self.go_sound = pygame.mixer.Sound(go_path)
            self.false_start_sound = pygame.mixer.Sound(
                false_start_path
            )
            self.game_over_sound = pygame.mixer.Sound(
                game_over_path
            )

            self.sound_enabled = True

        except (pygame.error, OSError):
            # Audio is optional.
            # The game continues normally if sound fails.
            self.sound_enabled = False

            self.go_sound = None
            self.false_start_sound = None
            self.game_over_sound = None

    # =================================
    # TASK 4 - PLAY SOUND SAFELY
    # =================================

    def _play_sound(self, sound):
        """
        Play a sound without allowing audio errors
        to crash the game.
        """

        if not self.sound_enabled:
            return

        if sound is None:
            return

        try:
            sound.play()

        except pygame.error:
            # Ignore audio errors and keep the game running.
            pass

    # =================================
    # INPUT
    # =================================

    def handle_event(self, event):

        # ---------------------------------
        # GAME OVER / REPLAY MENU
        # ---------------------------------

        if self.game_over:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:
                    self.start_new_game("Easy")

                elif event.key == pygame.K_2:
                    self.start_new_game("Medium")

                elif event.key == pygame.K_3:
                    self.start_new_game("Hard")

                elif event.key == pygame.K_4:
                    self.exit_game = True

            return

        # ---------------------------------
        # NORMAL GAME INPUT
        # ---------------------------------

        is_click = (
            event.type == pygame.MOUSEBUTTONDOWN
        )

        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        if not (is_click or is_space):
            return

        # ---------------------------------
        # TASK 4 - FALSE START SOUND
        # ---------------------------------

        if self.round.state == "waiting":

            self._play_sound(
                self.false_start_sound
            )

            # Do not record this as a reaction.
            return

        # ---------------------------------
        # VALID REACTION
        # ---------------------------------

        if self.round.state == "go":

            reaction_ms = self.round.register_input()

            # Task 1 behavior remains unchanged:
            # only a genuine reaction is recorded.
            if reaction_ms is not None:

                self.reaction_times.append(
                    reaction_ms
                )

                self.result_shown_at = (
                    pygame.time.get_ticks()
                )

    def handle_input(self):
        pass

    # =================================
    # UPDATE
    # =================================

    def update(self):

        # Do nothing while showing results.
        if self.game_over:
            return

        previous_state = self.round.state

        self.round.update()

        # ---------------------------------
        # TASK 4 - GO SOUND
        # ---------------------------------

        # Detect the exact transition:
        #
        # waiting -> go
        #
        # This guarantees the sound happens once
        # when the screen turns green.

        if (
            previous_state == "waiting"
            and self.round.state == "go"
        ):
            self._play_sound(
                self.go_sound
            )

        # ---------------------------------
        # NEXT ROUND
        # ---------------------------------

        if self.round.state == "result":

            now = pygame.time.get_ticks()

            if (
                now - self.result_shown_at
                >= self.result_pause_ms
            ):
                self._start_next_round()

    # =================================
    # NEXT ROUND / GAME OVER
    # =================================

    def _start_next_round(self):

        # ---------------------------------
        # SESSION COMPLETE
        # ---------------------------------

        if len(self.reaction_times) >= self.rounds_total:

            self.game_over = True

            # ---------------------------------
            # TASK 4 - GAME OVER SOUND
            # ---------------------------------

            self._play_sound(
                self.game_over_sound
            )

            return

        # ---------------------------------
        # START NEXT ROUND
        # ---------------------------------

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # =================================
    # START NEW GAME
    # =================================

    def start_new_game(self, difficulty):

        # Get difficulty settings.
        min_wait, max_wait, rounds = (
            self.difficulties[difficulty]
        )

        self.min_wait_ms = min_wait
        self.max_wait_ms = max_wait
        self.rounds_total = rounds

        # Clear previous results.
        self.reaction_times = []

        # Reset game state.
        self.game_over = False
        self.exit_game = False
        self.result_shown_at = None

        # Start first round.
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms
        )

    # =================================
    # AVERAGE
    # =================================

    def average_reaction_ms(self):

        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times)
            / len(self.reaction_times)
        )

    # =================================
    # RENDER
    # =================================

    def render(self, screen):

        # ---------------------------------
        # GAME OVER / RESULTS SCREEN
        # ---------------------------------

        if self.game_over:

            screen.fill(BLACK)

            title = self.big_font.render(
                "Game Over!",
                True,
                WHITE
            )

            title_rect = title.get_rect(
                center=(
                    self.width // 2,
                    50
                )
            )

            screen.blit(
                title,
                title_rect
            )

            # Reaction times
            y = 110

            for i, reaction_time in enumerate(
                self.reaction_times
            ):

                result_text = self.font.render(
                    f"Round {i + 1}: "
                    f"{reaction_time} ms",
                    True,
                    WHITE
                )

                result_rect = result_text.get_rect(
                    center=(
                        self.width // 2,
                        y
                    )
                )

                screen.blit(
                    result_text,
                    result_rect
                )

                y += 40

            # Average
            average_text = self.font.render(
                f"Average: "
                f"{self.average_reaction_ms()} ms",
                True,
                WHITE
            )

            average_rect = average_text.get_rect(
                center=(
                    self.width // 2,
                    y + 10
                )
            )

            screen.blit(
                average_text,
                average_rect
            )

            # Replay menu
            menu_y = y + 80

            menu_title = self.font.render(
                "Play Again?",
                True,
                WHITE
            )

            menu_rect = menu_title.get_rect(
                center=(
                    self.width // 2,
                    menu_y
                )
            )

            screen.blit(
                menu_title,
                menu_rect
            )

            options = [
                "1 - Easy",
                "2 - Medium",
                "3 - Hard",
                "4 - Exit"
            ]

            option_y = menu_y + 45

            for option in options:

                option_text = self.small_font.render(
                    option,
                    True,
                    WHITE
                )

                option_rect = option_text.get_rect(
                    center=(
                        self.width // 2,
                        option_y
                    )
                )

                screen.blit(
                    option_text,
                    option_rect
                )

                option_y += 30

            return

        # ---------------------------------
        # NORMAL GAME SCREEN
        # ---------------------------------

        if self.round.state == "waiting":

            bg = GRAY
            message = "Wait for green..."

        elif self.round.state == "go":

            bg = GREEN
            message = "Click now!"

        else:

            bg = BLUE
            message = (
                f"{self.round.reaction_ms} ms"
            )

        screen.fill(bg)

        text_surf = self.big_font.render(
            message,
            True,
            WHITE
        )

        text_rect = text_surf.get_rect(
            center=(
                self.width // 2,
                self.height // 2
            )
        )

        screen.blit(
            text_surf,
            text_rect
        )

        # Round counter
        round_num = min(
            len(self.reaction_times) + 1,
            self.rounds_total
        )

        round_text = self.font.render(
            f"Round {round_num}/"
            f"{self.rounds_total}",
            True,
            WHITE
        )

        screen.blit(
            round_text,
            (10, 10)
        )

        # Running average
        avg_text = self.font.render(
            f"Avg: "
            f"{self.average_reaction_ms()} ms",
            True,
            WHITE
        )

        screen.blit(
            avg_text,
            (self.width - 190, 10)
        )