# PokeCon

## 概要
コントローラー部分は[こちらのPoke-Controller](https://github.com/KawaSwitch/Poke-Controller)を参考にPython3.10+PySide2で動作するよう作り直しています


<img width="655" alt="Untitled" src="https://github.com/myamafuj/PokeCon/assets/24750772/fb1b281e-b27b-4bc3-9c96-45a9e9e42346">

## UIと機能
先ずは動くものを目指し、サポート範囲を絞っています

### Poke-Controllerとの違い
- OSサポートはWindowsのみ
- Mcuコマンドの削除
- GUIのベースをTkinterからPySide2に変更
- UIレイアウトの変更
- Lower camel caseからSnake caseに変更

また、Joystick.hexに関してはPoke-Controllerの派生先である[Poke-Controller-Modified](https://github.com/Moi-poke/Poke-Controller-Modified)のもので動作するようになっています

### 既知の問題
開発開始時はPython3.11+PySide6で開発を進めていましたが、自分の環境では4Kモニター2枚scale150%の状態で

1. PySide6でのモニターのプライマリー・セカンダリーの認識がおかしい
2. キャプチャー動画のスケールが1.5倍になる

という2点の問題が発生したことからPySide2に変更をしました

PySide2がPython3.10にまでしか対応していないためPython3.11も変更になりました

2.については仕様かもしれませんが、1.の方はPyQt6でも同じ現象が起きたため、Qt6の問題と思われます

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

キャプチャーデバイスとシリアルポートは読み込みが成功した1番目のものをデフォルトで使うようにしています

将来的には設定ファイルに保存・読込ができるようにする予定です



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
