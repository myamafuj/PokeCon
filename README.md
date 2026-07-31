# PokeCon

## 概要
コントローラー部分は[こちらのPoke-Controller](https://github.com/KawaSwitch/Poke-Controller)を参考にPython3.13+PySide6で動作するよう作り直しています


<img width="655" alt="Untitled" src="https://github.com/myamafuj/PokeCon/assets/24750772/fb1b281e-b27b-4bc3-9c96-45a9e9e42346">

## 環境構築と実行
プロジェクト管理には[uv](https://docs.astral.sh/uv/)を使用しています

```sh
# 依存関係のインストール(Python3.13も自動で用意されます)
uv sync

# アプリの起動
uv run main.py

# テストの実行
uv run pytest
```

## UIと機能
先ずは動くものを目指し、サポート範囲を絞っています

### Poke-Controllerとの違い
- OSサポートはWindowsのみ
- Mcuコマンドの削除
- GUIのベースをTkinterからPySide6に変更
- UIレイアウトの変更
- Lower camel caseからSnake caseに変更

また、Joystick.hexに関してはPoke-Controllerの派生先である[Poke-Controller-Modified](https://github.com/Moi-poke/Poke-Controller-Modified)のもので動作するようになっています

### 既知の問題
開発開始時はPython3.11+PySide6で開発を進めていましたが、自分の環境では4Kモニター2枚scale150%の状態で

1. PySide6でのモニターのプライマリー・セカンダリーの認識がおかしい
2. キャプチャー動画のスケールが1.5倍になる

という2点の問題が発生したことから一時PySide2(Python3.10)に変更していました

現在はPySide6のバージョンアップ(6.11系)に合わせてPython3.13+PySide6に再移行しています
上記の高DPI環境での問題が再発しないかは引き続き確認中です

また、自分のキャプチャーボードがswitchの画面も1980x1080 60fpsでしかチャプチャーしないため、
テンプレートマッチの画像も1980x1080に対応したものを自分で用意する必要がありました

今は自分しか使用していないのでキャプチャー時の設定をいじらず使用していますが
環境によっては色々変えられるようにしておいたほうが良さそうだと思っています

### 画面の説明
#### saveボタン
スクリーンショットを保存します

#### openボタン
保存したスクリーンショットの場所を開きます

#### コンボボックス
Pythonスクリプトが選択できます

#### reloadボタン
Pythonスクリプトを再読み込みします

#### start/stopボタン
Pythonスクリプトを実行・停止します
実行中は安全のために一部機能が停止します

#### ステータスバー
INFOレベル以上の最後のログが表示されます

また、開発者のためにコンソールにはDEBUG以上のログが表示されるようにしています

#### logボタン
PythonロガーのINFOレベル以上のログが表示されるウィンドウを新たに開きます

#### 歯車ボタン
設定画面がポップアップで出ます

- キャプチャーデバイス
- シリアルポート
- 画面解像度

が選択できます

キャプチャーデバイスとシリアルポートは設定画面から切り替えることができ、選択内容は`conf/pokecon.ini`に保存され次回起動時に読み込まれます



## 操作
### キーボード
キーボードをスイッチのコントローラとして使用することができます

[Stream版ライザのアトリエ](https://www.gamecity.ne.jp/manual/RyaT22JV/jp/2300.html)を参考にキーボードを割り当てています


| キーボード       |    Switchコントローラ |
|:------------|----------------:|
| 'l'         |        Button.A |
| 'k'         |        Button.B |
| 'j'         |        Button.X |
| 'i'         |        Button.Y |
| 'q'         |        Button.L |
| 'e'         |        Button.R |
| 'u'         |       Button.ZL |
| 'o'         |       Button.ZR |
| Key.shift_l |  Button.L_CLICK |
| Key.shift_r |  Button.R_CLICK |
| Key.ctrl_l  |    Button.MINUS |
| Key.ctrl_r  |     Button.PLUS |
| 'h'         |     Button.HOME |
| 'f'         |  Button.CAPTURE |
| 'w'         |    Direction.UP |
| 'd'         | Direction.RIGHT |
| 's'         |  Direction.DOWN |
| 'a'         |  Direction.LEFT |
| Key.up      |         Hat.TOP |
| Key.right   |       Hat.RIGHT |
| Key.down    |         Hat.BTM |
| Key.left    |        Hat.LEFT |


####  マウス
キャプチャー画面内にカーソルがある場合のみ入力を受け付けます

:::note alert
直感的にタッチ操作できる訳ではないので注意してください
:::

| マウス   | Switchコントローラ |
|:------|-------------:|
| 左クリック |     Button.A |
| 右クリック |     Button.B |
| 中クリック |     Button.X |
