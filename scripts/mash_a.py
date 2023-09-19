from pokecon.command import PythonCommand
from pokecon.pad import Button


# Mash a button A
# A連打
class MashA(PythonCommand):
	NAME = 'A連打'

	def __init__(self):
		super().__init__()

	def do(self):
		while True:
			self.wait(0.5)
			self.press(Button.A)
