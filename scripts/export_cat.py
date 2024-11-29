####
import asyncio
from pathlib import Path
import sys
from collections import Counter
import os

sys.path.append(str(Path('.').resolve()))
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)

from src.state import ScoreBoard
from src.logic.worker import Worker
from src import utils

if __name__=='__main__':
    utils.fix_zmq_asyncio_windows()

    worker = Worker('worker-test')
    asyncio.run(worker._before_run())
    # for u in worker.game.users.list:
    #     if u._store.group=='UESTC':
    #         # for passchall in u.passed_challs:
    #         #     print(passchall)
    #         for passflag in u.passed_flags:
    #             print(passflag.challenge._store.title)
    #             print(u.tot_score)
    #             print(u._store.profile.nickname_or_null)
    #             print(passflag.name)
    b = worker.game.boards["score_newbie"]
    d = worker.game.boards["first_newbie"]
    e = worker.game.boards["first_all"]
    print(worker.game.boards)
    assert isinstance(b, ScoreBoard)
    num = 1
    with open('catoutput.md', 'w') as file:
        for useritem in b.board[:35]:
            u = useritem[0]
            file.write(f'## [{num}] **{u._store.profile.nickname_or_null}**\n')
            file.write(f'#### 总分: **{u.tot_score}**\n')
            chall_dict = {}     # 选手解出chall
            for passflag in u.passed_flags:
                title = passflag.challenge._store.title
                name = passflag.name
                if title not in chall_dict:
                    chall_dict[title] = []
                chall_dict[title].append(name)
            for item in chall_dict.items():
                flag_list = '\n- '.join(item[1])
                if item[1] == ['']:
                    file.write(f'`{item[0]}`\n\n\n\n')
                else:
                    file.write(f'`{item[0]}`\n- {flag_list}\n\n')
            num += 1

                        
    file.close()
       
