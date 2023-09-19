from pokecon.command import ImageProcPythonCommand
from pokecon.pad import Button, Direction


# auto release Pokémon
class AutoRelease(ImageProcPythonCommand):
	NAME = '自動リリース'

	def __init__(self, cap):
		super().__init__(cap)
		self.row = 5
		self.col = 6
		self.cap = cap

	def do(self):
		self.wait(0.5)

		for i in range(0, self.row):
			for j in range(0, self.col):
				if not self.cap.isOpened():
					self.release()
				else:
					# if shiny, then skip
					if not self.is_contain_template('shiny_mark.png', threshold=0.9):
						# Maybe this threshold works for only Japanese version.
						if self.is_contain_template('status.png', threshold=0.7):
							# Release a pokemon
							self.release()

				if not j == self.col - 1:
					if i % 2 == 0:
						self.press(Direction.RIGHT, wait=0.2)
					else:
						self.press(Direction.LEFT, wait=0.2)

			self.press(Direction.DOWN, wait=0.2)

		# Return from Pokémon box
		self.press(Button.B, wait=2)
		self.press(Button.B, wait=2)
		self.press(Button.B, wait=1.5)

	def release(self):
		self.press(Button.A, wait=0.5)
		self.press(Direction.UP, wait=0.2)
		self.press(Direction.UP, wait=0.2)
		self.press(Button.A, wait=1)
		self.press(Direction.UP, wait=0.2)
		self.press(Button.A, wait=1.5)
		self.press(Button.A, wait=0.3)
