from time import time

import cv2

from pokecon.command import ImageProcPythonCommand
from pokecon.logger import get_logger
from pokecon.pad import Button


logger = get_logger(__name__)


# Pokémon LEGENDS Z-A 異次元ミアレのワープ周回（移動なし）
# 【開始条件】ワープ装置前で実行を開始すること
# 【ループ】その場で＋ボタンでマップ → A連打でワープ → フィールド復帰確認
# 【終了】左上のエナジーが1000kcal未満（=3桁以下）になったらHOMEメニューに退避して停止
class ZAWarpLoop(ImageProcPythonCommand):
    NAME = "[Z-A] ワープ周回（移動なし）"

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
        logger.info("ワープ装置前から開始してください")
        count = 0
        while True:
            count += 1
            logger.info(f"--- {count}周目 ---")

            # 1. マップを開いてA連打でワープ
            self.press(Button.PLUS, wait=1.5)
            for _ in range(self.MASH_A_COUNT):
                self.press(Button.A, duration=0.05, wait=0.35)

            # 2. フィールド復帰（kcal表示の再出現）を待つ
            #    到着地点に「A 調べる」があるため、復帰待ちの間はボタンを押さない
            if not self.wait_field():
                logger.error("ワープ後のフィールド復帰を確認できませんでした。停止します")
                self.stop_in_home_menu()
            self.wait(0.5)

            # 3. エナジー残量チェック（桁数で判定）
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
