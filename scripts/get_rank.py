import asyncio
from pathlib import Path
import sys

sys.path.append(str(Path(".").resolve()))

from src.logic.worker import Worker
from src.state import ScoreBoard, FirstBloodBoard
from src import utils

N_TOP = 10
N_THRESHOLD = 10

if __name__ == "__main__":
    utils.fix_zmq_asyncio_windows()

    worker = Worker("worker-test")
    asyncio.run(worker._before_run())

    sc = worker.game.boards["score_all"]
    sn = worker.game.boards["score_newbie"]
    print(worker.game.boards)
    assert isinstance(sn, ScoreBoard)
    for item in sn.board[:10]:
        print(
            "{} : {}".format(item[0]._store.profile.nickname_or_null, item[1])
        )
