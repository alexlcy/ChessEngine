#!/Users/alexlo/anaconda3/bin/python

from state import State
import torch
from train import Net
import chess.svg
import time
import base64
import os
import traceback

MAXVAL =10000

class Valuator(object):
    def __init__(self):
        vals = torch.load("nets/value.pth", map_location = lambda storage, loc:storage)
        self.model = Net()
        self.model.load_state_dict(vals)

    def __call__(self, s):
        brd = s.serialize()[None]
        output = self.model(torch.tensor(brd).float())
        return float(output.data[0][0])

class ClassicValuator(object):
    values = {chess.PAWN:1,
              chess.KNIGHT:3,
              chess.BISHOP:3,
              chess.ROOK:5,
              chess.QUEEN:9,
              chess.KING:0}

    def __init__(self):
        pass

    def __call__(self, s):
        if s.board.is_variant_win():
            if s.turn == chess.WHITE:
                return self.MAXVAL
            else:
                return -1 * self.MAXVAL
        if s.board.is_variant_loss():
            if s.turn == chess.WHITE:
                return -1 * self.MAXVAL
            else:
                return self.MAXVAL
        pm = s.board.piece_map()
        val = 0
        for x in pm:
            tval = self.values[pm[x].piece_type]
            if pm[x].color == chess.WHITE:
                val += tval
            else:
                val -= tval
        return val

#v = Valuator()
s = State()
v = ClassicValuator()

def to_svg(s):
    return base64.b64encode(chess.svg.board(board = s.board).encode('utf-8')).decode('utf-8')


from flask import Flask, Response, request
app = Flask(__name__)



def computer_minimax(s,v,depth=2):
    if depth == 0 or s.board.is_game_over():
        return v(s)

    turn = s.board.turn
    # WHITE is maxmizing player
    if turn == chess.WHITE:
        ret = -MAXVAL
    else:
        ret = MAXVAL

    for e in s.edges():
        s.board.push(e)
        tval = computer_minimax(s,v,depth-1)
        if turn == chess.WHITE:
            ret = max(ret, tval)
        else:
            ret = min(ret, tval)
        s.board.pop()
    return ret

def explore_leaves(s,v):
    ret = []
    for e in s.edges():
        s.board.push(e)
        #ret.append((v(s), e))
        ret.append((computer_minimax(s,v),e))
        s.board.pop()
    return ret

def computer_move(s,v):
    move = sorted(explore_leaves(s,v), key = lambda x:x[0], reverse = s.board.turn)
    print("top 3:")
    for i, m in enumerate(move[0:3]):
        print("  ", m)
    s.board.push(move[0][1])

@app.route("/selfplay")
def selfplay():
    s = State()
    ret = '<html><body>'
    while not s.board.is_game_over():
        computer_move(s,v)
        ret += '<img width=500 height=500 src="data:image/svg+xml;base64,%s"></img><br/>' % to_svg(s)
    print(s.board.result())
    return ret


#@app.route("/")
#def hello():
#    board_svg = to_svg(s)
#    ret =  '<html>'
#    ret += '<head><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'
#    ret += '<style>input {font-size:30px;} button {font-size:30px;}</style>'
#    ret += '</head><body>'
#    ret += '<img width=500 height=500 src="data:image/svg+xml;base64,%s"></img><br/>' % board_svg
#    ret += '<form action = "/move"><input name="move" type="text"></input><input type="submit" value="Human Move"></form><br/>'
#    return ret

#@app.route("/move")
#def move():
#    if not s.board.is_game_over():
#        move = request.args.get('move',default = "")
#        if move is not None and move != "":
#            print("human move", move)
#            s.board.push_san(move)
#            computer_move(s,v)
#    else:
#        print("GAME IS OVER")
#    return hello()


@app.route("/")
def hello():
  ret = open("index.html").read()
  return ret.replace('start', s.board.fen())

# move given in algebraic notation
@app.route("/move")
def move():
  if not s.board.is_game_over():
    move = request.args.get('move',default="")
    if move is not None and move != "":
      print("human moves", move)
      try:
        s.board.push_san(move)
        computer_move(s, v)
      except Exception:
        traceback.print_exc()
      response = app.response_class(
        response=s.board.fen(),
        status=200
      )
      return response
  else:
    print("GAME IS OVER")
    response = app.response_class(
      response="game over",
      status=200
    )
    return response
  print("hello ran")
  return hello()

# moves given as coordinates of piece moved
@app.route("/move_coordinates")
def move_coordinates():
  if not s.board.is_game_over():
    source = int(request.args.get('from', default=''))
    target = int(request.args.get('to', default=''))
    promotion = True if request.args.get('promotion', default='') == 'true' else False

    move = s.board.san(chess.Move(source, target, promotion=chess.QUEEN if promotion else None))

    if move is not None and move != "":
      print("human moves", move)
      try:
        s.board.push_san(move)
        computer_move(s, v)
      except Exception:
        traceback.print_exc()
    response = app.response_class(
      response=s.board.fen(),
      status=200
    )
    return response

  print("GAME IS OVER")
  response = app.response_class(
    response="game over",
    status=200
  )
  return response

@app.route("/newgame")
def newgame():
  s.board.reset()
  response = app.response_class(
    response=s.board.fen(),
    status=200
  )
  return response



if __name__ == "__main__":
    if os.getenv("SELFPLAY") is not None:
        s = State()
        while not s.board.is_game_over():
            print(s.board)
            computer_move(s,v)
    else:
        app.run(debug = True)
