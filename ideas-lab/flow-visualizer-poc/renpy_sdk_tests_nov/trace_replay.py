import pathlib
import inspect_label_node as iln
sdk_path = pathlib.Path('C:/Users/juanc/PycharmProjects/TPT3/ThePlotThickens/app/renpy-source-api/renpy_sdk/renpy-8.4.0-sdk')
game_path = pathlib.Path('T:/AG/InnerGrowth-1.8-pc')
iln.inspect_label(game_path, 'replay0020', sdk_path=sdk_path, max_statements=0)
import renpy.game
node = renpy.game.script.lookup('replay0020')
stmt = node.next
for idx in range(40):
    if stmt is None:
        print(idx, 'None')
        break
    print(idx, type(stmt).__name__, getattr(stmt, 'linenumber', None))
    stmt = getattr(stmt, 'next', None)
