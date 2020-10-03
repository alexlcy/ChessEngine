#!/Users/alexlo/anaconda3/bin/python

from state import State
import torch
from train import Net
import chess.svg
import time

class Valuator(object):
    def __init__(self):
        vals = torch.load("nets/value.pth", map_location = lambda storage, loc:storage)
        self.model = Net()
        self.model.load_state_dict(vals)

    def __call__(self, s):
        brd = s.serialize()[None]
        output = self.model(torch.tensor(brd).float())
        return float(output.data[0][0])


def explore_leaves(s,v):
    ret = []
    for e in s.edges():
        s.board.push(e)
        ret.append((v(s), e))
        s.board.pop()
    return ret



v = Valuator()
s = State()

from flask import Flask, Response, request
app = Flask(__name__)

@app.route("/")
def hello():
    ret =  '<html>'
    ret += '<head><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'
    ret += '<style>input {font-size:30px;} button {font-size:30px;}</style>'
    ret += '</head><body>'
    ret += '<img width=500 height=500 src="/board.svg?%f"></img><br/>' % time.time()
    ret += '<form action = "/move"><input name="move" type="text"></input><input type="submit" value="Human Move"></form><br/>'
    return ret

@app.route("/board.svg")
def board():
    return Response(chess.svg.board(board = s.board), mimetype = 'image/svg+xml')

def computer_move():
    move = sorted(explore_leaves(s,v), key = lambda x:x[0], reverse = s.board.turn)[0]
    print(move)
    s.board.push(move[1])

@app.route("/move")
def move():
    if not s.board.is_game_over():
        move = request.args.get('move',default = "")
        if move is not None and move != "":
            print("human move", move)
            s.board.push_san(move)
            computer_move()
    else:
        print("GAME IS OVER")
    return hello()


if __name__ == "__main__":
    app.run(debug = True)
