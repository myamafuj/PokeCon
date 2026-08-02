from time import time

import cv2

from pokecon.command import ImageProcPythonCommand
from pokecon.logger import get_logger
from pokecon.pad import Button, Direction, Stick


logger = get_logger(__name__)


# Pokémon LEGENDS Z-A 異次元ミアレのシャトルラン周回
# 【開始条件】ワープ装置前（周回の開始地点）で実行を開始すること
# 【ループ】右斜め前へBダッシュで走る → ＋ボタンでマップ → A連打でワープ → フィールド復帰確認
# 【終了】左上のエナジーが1000kcal未満（=3桁以下）になったらHOMEメニューに退避して停止
class ZAShuttleRun(ImageProcPythonCommand):
    NAME = "[Z-A] シャトルラン周回"

    # 移動（右=0度・前=90度）: Bダッシュで区間1→区間2と続けて走る
    RUN_DIRECTION_1 = Direction.UP  # 区間1: 正面
    RUN_DURATION_1 = 0.5
    RUN_DIRECTION_2 = Direction.custom(Stick.LEFT, 50, "UP_RIGHT_50")  # 区間2: 右斜め前50度
    RUN_DURATION_2 = 3.0
    # マップを開いてからのA連打回数（ワープ先選択＋確認を押し切る想定）
    MASH_A_COUNT = 8
    # ワープ後のフィールド復帰確認のタイムアウト [s]
    TIMEOUT_WARP = 60
    # kcal数字の領域 [x_min, x_max, y_min, y_max] と数字1桁の高さ範囲 [px]
    # 実測: 数字の高さ43-44 / 「kcal」の文字15-21 → 高さで数字だけ数える
    # 左端84はリングの縁（x60-82に弧の断片が数字と同じ高さで出る）を除外するための値
    KCAL_AREA = (84, 280, 120, 200)
    DIGIT_HEIGHT = (35, 60)
    # 続行に必要なエナジーの桁数（4桁 = 1000kcal以上）
    KCAL_MIN_DIGITS = 4

    def __init__(self, cap):
        super().__init__(cap)

    def do(self):
        logger.info("ワープ装置前（周回開始地点）から開始してください")
        count = 0
        while True:
            count += 1
            logger.info(f"--- {count}周目 ---")

            # 1. Bダッシュで正面へ走った後、向きを切り替えて走り続ける
            #    ホールド中のスティックは後続press時に上書き合成されるため、
            #    向きの変更は一度hold_endしてから次をholdする
            self.hold(self.RUN_DIRECTION_1, wait=0.1)
            self.press(Button.B, wait=self.RUN_DURATION_1)
            self.hold_end(self.RUN_DIRECTION_1)
            self.hold(self.RUN_DIRECTION_2, wait=self.RUN_DURATION_2)
            self.hold_end(self.RUN_DIRECTION_2)
            self.wait(0.3)

            # 2. マップを開いてA連打でワープ
            self.press(Button.PLUS, wait=1.5)
            for _ in range(self.MASH_A_COUNT):
                self.press(Button.A, duration=0.05, wait=0.35)

            # 3. フィールド復帰（kcal表示の再出現）を待つ
            #    到着地点に「A 調べる」があるため、復帰待ちの間はボタンを押さない
            if not self.wait_field():
                logger.error("ワープ後のフィールド復帰を確認できませんでした。停止します")
                self.stop_in_home_menu()
            self.wait(0.5)

            # 4. エナジー残量チェック（桁数で判定）
            digits = self.count_kcal_digits()
            if digits < self.KCAL_MIN_DIGITS:
                logger.warning(
                    f"エナジーが1000kcal未満になりました（{digits}桁）。HOMEに退避して停止します"
                )
                self.stop_in_home_menu()
            logger.info(f"エナジー残量は{digits}桁。周回を続けます")

    # kcal数字が確認できるまで待つ（=フィールドに復帰した）
    def wait_field(self):
        start = time()
        while time() - start < self.TIMEOUT_WARP:
            if self.count_kcal_digits() >= 3:
                return True
            self.wait(0.5)
        return False

    # 左上のkcal数字の桁数を数える
    # 白い数字を2値化し、数字の高さに合う連結成分の個数を返す（OCR不要の1000以上判定）
    def count_kcal_digits(self):
        x_min, x_max, y_min, y_max = self.KCAL_AREA
        frame = self.get_frame()
        gray = cv2.cvtColor(frame[y_min:y_max, x_min:x_max], cv2.COLOR_BGR2GRAY)
        th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        n, _, stats, _ = cv2.connectedComponentsWithStats(th)
        h_min, h_max = self.DIGIT_HEIGHT
        return sum(
            1
            for i in range(1, n)
            if h_min <= stats[i, cv2.CC_STAT_HEIGHT] <= h_max
            and stats[i, cv2.CC_STAT_AREA] >= 80
        )

    # スクリーンショットを保存し、HOMEメニューに退避してゲーム内時間を止めてから停止する
    def stop_in_home_menu(self):
        self.screenshot()
        self.press(Button.HOME, wait=1.0)
        self.finish()
