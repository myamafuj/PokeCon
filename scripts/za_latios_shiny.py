from datetime import datetime
from time import time

import cv2
import numpy as np

from pokecon.command import ImageProcPythonCommand
from pokecon.logger import get_logger
from pokecon.pad import Button, Direction


logger = get_logger(__name__)


# Pokémon LEGENDS Z-A 異次元ミアレのラティオス色違い厳選
# 【開始条件】ゲーム内（異次元ミアレのセーブ地点で保存済み）で実行を開始すること
# 【ループ】ソフト終了 → 再起動 → セーブロード → A（エレベーター）→ 色判定 → 通常色ならリセット
# 【判定】飛んでいるラティオスの体色をHSVブロブ解析で判定
#         通常色は青、色違いは「青以外の鮮やかな大きい塊」として色相非依存で検出する
# 【検出時】スクリーンショットを保存してスクリプトを停止する（捕獲は手動）
class ZALatiosShiny(ImageProcPythonCommand):
    NAME = "[Z-A] ラティオス色違い厳選"

    # 判定領域 [x_min, x_max, y_min, y_max]
    # 左上のkcalリング・下部のHUD・画面上端のオーロラ帯（誤検知実績あり）を除外
    JUDGE_AREA = (300, 1920, 150, 800)
    # 判定領域内でさらに除外する矩形 [(x_min, x_max, y_min, y_max), ...]
    # カメラ位置が毎回同じことを利用し、青色（H110前後）の固定構造物を通常色誤判定から外す
    JUDGE_EXCLUDE = (
        (1400, 1560, 640, 800),  # エレベーター右の光柱（実測最大約2800px）
        (1770, 1920, 150, 330),  # スポーン視点右端の構造物（実測最大約2100px）
    )
    # 検出条件（OpenCVのHは0-179）
    # 通常色（青）は実測ベースの色相範囲。色違いは実物の色が未確認のため
    # 「青以外の鮮やかな大きい塊」として色相非依存で検出する（何色でも拾える）
    # 通常色（青）の色相範囲。下限92は実測に基づく: 本体はH96以上（88未満はゼロ）で、
    # 色違い（青緑・推定H82前後）が照明で青側にずれても巻き込まないよう間を取った値
    HUE_NORMAL = (92, 115)
    # 通常色の彩度下限150は実測に基づく: フェンスの反射（S中央値98、照明次第で6000px超の
    # 青ブロブになり通常色誤判定の実績あり）を除外しつつ、本体（9割が159以上）は通す値
    S_MIN_NORMAL = 150
    V_MIN_NORMAL = 80  # 通常色の明度下限
    # 色違い側の下限はノイズ源の実測に基づく:
    #   彩度150: エレベーター到着演出の半透明の四角（S最大110）を除外。本体は9割が159以上
    #   明度150: オーロラ（V中央値117・9割が145以下）を除外。本体は9割が153以上
    S_MIN_SHINY = 150
    V_MIN_SHINY = 150
    # 色違いは一過性の演出と区別するため連続Nサンプルのしきい値超えで候補とし、
    # さらに数秒置いて再度連続検出できた場合のみ確定する（出現演出の光は消えるが本体は残る）
    SHINY_CONSEC = 2
    SHINY_RECHECK_WAIT = 2.0
    # ブロブ面積しきい値 [px]
    # 実測（彩度下限150適用後）: ラティオス本体 約2900〜5100 / 柵などの青ノイズ最大約800 /
    # 青以外ノイズ最大約350
    # 色違い側を低めにしているのは、色違い（青緑）の色相が照明で青範囲をまたいだ場合でも
    # 緑側に残った部分で色違い候補と認識し、通常色への誤判定（=取り逃し）を防ぐため
    BLOB_NORMAL = 2500
    BLOB_SHINY = 1000
    # タイムアウト [s]
    TIMEOUT_TITLE = 60
    TIMEOUT_FIELD = 90
    TIMEOUT_JUDGE = 40
    # エレベーター乗車時間 [s]（A押下から到着までの目安。到着後にカメラ操作を行う）
    ELEVATOR_RIDE_WAIT = 1.0
    # 到着後に右スティック上でカメラを見下ろし角度へ傾ける時間 [s]
    # デフォルト角度だとラティオスがプレイヤーの陰に隠れたままタイムアウトすることがあるため
    CAMERA_TILT_DURATION = 0.25
    # 監査用に保持する「通常色」判定フレームの数（古いものから自動削除）
    AUDIT_KEEP = 5000

    def __init__(self, cap):
        super().__init__(cap)

    def do(self):
        logger.info("ゲーム内から開始してください（HOMEボタンでソフト終了できる状態）")
        count = 0
        while True:
            count += 1
            logger.info(f"--- {count}周目 ---")
            self.restart_game()
            self.load_save()

            # スポーン地点でAを押すとエレベーターが起動しラティオスの見える場所へ到達する
            # 1回目が操作受付前に落ちた場合の保険として2秒後にもう一度押す（乗車中のA入力は無害）
            self.press(Button.A, wait=2.0)
            self.press(Button.A, wait=1.0)

            # 到着を待ってからカメラを上から見下ろす角度に傾け、ラティオスを視界に入れる
            self.wait(self.ELEVATOR_RIDE_WAIT)
            self.press(Direction.R_DOWN, duration=self.CAMERA_TILT_DURATION)

            result = self.judge_shiny()
            if result == "shiny":
                logger.info(f"色違いを検出しました！（{count}周目）")
                self.stop_in_home_menu()
            elif result == "timeout":
                logger.warning("判定がタイムアウトしました。目視確認のため停止します")
                self.stop_in_home_menu()
            else:
                logger.info("通常色でした。リセットします")

    # スクリーンショットを保存し、HOMEメニューに退避してゲーム内時間を止めてから停止する
    def stop_in_home_menu(self):
        self.screenshot()
        self.press(Button.HOME, wait=1.0)
        self.finish()

    # ソフトを終了して再起動し、タイトル画面が表示されるまで待つ
    def restart_game(self):
        self.press(Button.HOME, wait=1.0)
        self.press(Button.X, wait=1.0)  # ソフトをおわる
        self.press(Button.A, wait=3.5)  # 「終了する」（ダイアログの初期選択）
        self.press(Button.A, wait=1.0)  # ソフトを起動
        if not self.wait_template("za/title_press_a.png", self.TIMEOUT_TITLE):
            logger.error("タイトル画面を検出できませんでした。停止します")
            self.screenshot()
            self.finish()

    # タイトルでAを押し、フィールド復帰（右上の調査ゲージアイコン表示）を待つ
    def load_save(self):
        # タイトル表示直後は入力を受け付けないことがあるため、
        # タイトル画面が消えた（＝Aが効いた）ことを確認するまで押し直す
        self.wait(1.0)
        start = time()
        while True:
            self.press(Button.A, wait=2.0)
            if not self.is_title_visible():
                break
            if time() - start > self.TIMEOUT_TITLE:
                logger.error("タイトル画面から先に進めませんでした。停止します")
                self.screenshot()
                self.finish()
        if not self.wait_template(
            "za/field_hud.png", self.TIMEOUT_FIELD, threshold=0.75, use_gray=False
        ):
            logger.error("フィールド画面を検出できませんでした。停止します")
            self.screenshot()
            self.finish()
        # 「異次元ミアレ」の表示が消えて操作可能になるまで少し待つ
        self.wait(2.0)

    # タイトル画面が表示中か判定する
    # 「PRESS A BUTTON」は点滅するため、点滅周期をカバーする複数サンプルで確認する
    def is_title_visible(self):
        for _ in range(4):
            if self.is_contain_template("za/title_press_a.png", show_value=True):
                return True
            self.wait(0.4)
        return False

    # テンプレートが検出されるまでポーリングする
    def wait_template(
        self, template_path, timeout, threshold=0.7, use_gray=True, interval=0.5
    ):
        start = time()
        while time() - start < timeout:
            if self.is_contain_template(
                template_path, threshold=threshold, use_gray=use_gray, show_value=True
            ):
                return True
            self.wait(interval)
        return False

    # ラティオスの体色を判定する
    # 'shiny': 緑ブロブ検出 / 'normal': 青ブロブ検出 / 'timeout': どちらも未検出
    def judge_shiny(self):
        x_min, x_max, y_min, y_max = self.JUDGE_AREA
        shiny_streak = 0
        rechecked = False
        start = time()
        while time() - start < self.TIMEOUT_JUDGE:
            frame = self.get_frame()
            hsv = cv2.cvtColor(frame[y_min:y_max, x_min:x_max], cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            is_blue = (h >= self.HUE_NORMAL[0]) & (h <= self.HUE_NORMAL[1])
            mask_shiny = (s >= self.S_MIN_SHINY) & (v >= self.V_MIN_SHINY) & ~is_blue
            mask_normal = (s >= self.S_MIN_NORMAL) & (v >= self.V_MIN_NORMAL) & is_blue
            for ex_min, ex_max, ey_min, ey_max in self.JUDGE_EXCLUDE:
                for mask in (mask_shiny, mask_normal):
                    mask[
                        max(ey_min - y_min, 0) : max(ey_max - y_min, 0),
                        max(ex_min - x_min, 0) : max(ex_max - x_min, 0),
                    ] = False
            shiny_area = self._max_blob_area(mask_shiny)
            normal_area = self._max_blob_area(mask_normal)
            logger.debug(f"blob area: normal={normal_area}, shiny={shiny_area}")
            if shiny_area >= self.BLOB_SHINY:
                shiny_streak += 1
                # 反応した実フレームを証拠として保存（誤検知の原因特定用）
                self.save_audit(frame, "shiny", f"s{shiny_area}")
                if shiny_streak >= self.SHINY_CONSEC:
                    if not rechecked:
                        logger.info(
                            "色違い候補を検出。出現演出の可能性を除くため再確認します"
                        )
                        rechecked = True
                        shiny_streak = 0
                        self.wait(self.SHINY_RECHECK_WAIT)
                        continue
                    return "shiny"
            else:
                shiny_streak = 0
            # 色違いが確定待ちの間は通常色判定を保留する（次サンプルで白黒つく）
            if normal_area >= self.BLOB_NORMAL and shiny_streak == 0:
                self.save_audit(frame, "normal", f"n{normal_area}_s{shiny_area}")
                return "normal"
            self.wait(0.3)
        return "timeout"

    # 判定の根拠フレームを監査用に保存する（プレフィックスごとに直近AUDIT_KEEP件のみ保持）
    # 判定履歴を後から目視で総ざらいし、取り逃し・誤検知の原因を検証できるようにする
    def save_audit(self, frame, prefix, suffix):
        try:
            audit_dir = self.cap.path_dir / "audit"
            audit_dir.mkdir(parents=True, exist_ok=True)
            name = f"{prefix}_{datetime.now():%Y%m%d%H%M%S%f}_{suffix}.png"
            cv2.imwrite(str(audit_dir / name), frame)
            for old in sorted(audit_dir.glob(f"{prefix}_*.png"))[: -self.AUDIT_KEEP]:
                old.unlink()
        except OSError as e:
            # 監査保存の失敗で厳選ループを止めない
            logger.warning(f"監査用スクリーンショットの保存に失敗しました: {e}")

    # 条件マスクから最大連結成分の面積を返す
    # オープニングで星などの点ノイズを除去した後、クロージングで近接した断片を連結する
    # （正面向きのラティオスは白い頭部で翼・胴体が分断され、単体では面積不足になるため。
    #   実測: 正面向きの青 2201→5149 / ノイズは連結しても最大約700で1000未満に収まる）
    @staticmethod
    def _max_blob_area(cond_mask):
        mask = cond_mask.astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask)
        return int(stats[1:, cv2.CC_STAT_AREA].max()) if n > 1 else 0
