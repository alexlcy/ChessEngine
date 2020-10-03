#!/Users/alexlo/anaconda3/bin/python
import numpy as np
import os
import chess.pgn
from state import State

# pgn file in this data folder

def get_dataset(num_samples=None):
	gn = 0
	X = []
	values = {"1/2-1/2":0, "0-1":-1, "1-0":1}
	Y = []
	for fn in os.listdir("data"):
		pgn = open(os.path.join("data", fn))
		while True:
			try:
				game = chess.pgn.read_game(pgn)
			except Exception:
				break
			
			res = game.headers['Result']
			if res not in values:
				continue
			value = values[res]

			board = game.board()
			for i, move in enumerate(game.mainline_moves()):
				board.push(move)
				ser = State(board).serialize()
				#print(value, ser)
				X.append(ser)
				Y.append(value)
			print(f"prasing game {gn} got {len(X)} examples")
			if num_samples is not None  and  len(X) > num_samples:
				return X,Y
			gn +=1
	return X,Y


if __name__ == "__main__":
	X, Y = get_dataset(5000000)
	np.savez('processed/dataset_5M.npz', X, Y)
