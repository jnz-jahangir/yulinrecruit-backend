from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import validates
import re
from typing import Any, Optional, Tuple, Dict, List

from . import Table

class ChallengeStore(Table):
    __tablename__ = 'challenge'

    effective_after: int = Column(Integer, nullable=False)

    key: str = Column(String(32), nullable=False, unique=True)
    title: str = Column(String(64), nullable=False)
    category: str = Column(String(32), nullable=False)
    sorting_index: int = Column(Integer, nullable=False)
    desc_template: str = Column(Text, nullable=False)

    chall_metadata: Optional[Dict[str, Any]] = Column(JSON, nullable=False)
    actions: List[Dict[str, Any]] = Column(JSON, nullable=False)
    flags: List[Dict[str, Any]] = Column(JSON, nullable=False)

    VAL_FLAG = re.compile(r'^YulinSec{.{1,100}}$') # 0x7d is '}'
    MAX_FLAG_LEN = 110

    CAT_COLORS = {
        "Tutorial": "#177cb0",
        "Misc": "#ff9966",
        "Web": "#003472",
        "Binary": "#3b2e7e",
        "Algorithm": "#4a4266",
        "Crypto": "#a25768",
        "Reverse": "#003371",
        "Pwn": "#4c8dae",
        "IOT": "#3d3b4f",
        "SQLi": "#808080",
        "XSS": "#725e82",
        "LFI": "#549688",
        "RFI": "#2c4f54",
        "RCE": "#56564b",
        "CSRF": "#8c7042",
        "SSRF": "#897858",
        "Android": "#FFFACD",
        "Intranet": "#9f9847",
        "Penetration": "#9f9847",
        "Forensics": "#333300",
        "Stego": "#556B2F",
        "Recon": "#008B8B",
        "OSINT": "#00CED1",
        "Cloud": "#B0E0E6",
        "Blockchain": "#6495ED",
        "Reverse Engineering": "#6A5ACD",
        "Miscellaneous": "#483D8B",
        "DevOops": "#6a6ae1",
        "SRC": "#BA55D3",
        "SA": "#1a53ff",
        "Upload": "#458B74",
        "SignIn": "#8B3A3A",
        "Design": "#8B008B",
        "SSTI": "#FFC0CB",
        "SocialEngineer":"#FFBB0A"
    }
    FALLBACK_CAT_COLOR = '#000000'

    @validates('chall_metadata')
    def validate_chall_metadata(self, _key: str, chall_metadata: Any) -> Any:
        assert isinstance(chall_metadata, dict), 'metadata should be a dict'

        return chall_metadata

    METADATA_SNIPPET = '''{"author": "You", "first_blood_award_eligible": false, "score_deduction_eligible": true}'''

    @validates('flags')
    def validate_flags(self, _key: str, flags: Any) -> Any:
        assert isinstance(flags, list), 'flags should be list'
        assert len(flags)>0, 'flags should not be empty'

        for flag in flags:
            assert isinstance(flag, dict), 'flag should be dict'

            assert 'name' in flag, 'flag should have name'
            assert 'type' in flag, 'flag should have type'
            assert 'val' in flag, 'flag should have val'
            assert 'base_score' in flag, 'flag should have base_score'

            assert flag['type'] in ['static', 'leet', 'partitioned', 'dynamic'], 'unknown flag type'
            assert isinstance(flag['name'], str), 'flag name should be str'
            assert isinstance(flag['base_score'], int), 'flag base_score should be int'
            if flag['type']=='partitioned':
                assert isinstance(flag['val'], list) and all(isinstance(f, str) for f in flag['val']), 'flag val should be list of str'
                assert all((self.check_flag_format(f) is None) for f in flag['val']), f'{flag["name"]}不符合Flag格式'
            else:
                assert isinstance(flag['val'], str), 'flag val should be str'
                if flag['type'] in ['static', 'leet']:
                    assert self.check_flag_format(flag['val']) is None, f'{flag["name"]}不符合Flag格式'

        if len(flags)==1:
            assert flags[0]['name']=='', '单个Flag的name需要留空，因为不会显示'
        else:
            assert all(f['name']!='' for f in flags), '有多个Flag时需要填写name字段'

        return flags

    FLAG_SNIPPETS = {
        'static': '''{"name": "", "type": "static", "val" : "YulinSec{}", "base_score": 100}''',
        'leet': '''{"name": "", "type": "leet", "val" : "YulinSec{}", "salt": "", "base_score": 100}''',
        'partitioned': '''{"name": "", "type": "partitioned", "val" : ["YulinSec{}"], "base_score": 100}''',
        'dynamic': '''{"name": "", "type": "dynamic", "val" : "module_path", "base_score": 100}''',
    }

    @validates('actions')
    def validate_actions(self, _key: str, actions: Any) -> Any:
        assert isinstance(actions, list), 'actions should be list'
        attachment_filenames = set()

        for action in actions:
            assert isinstance(action, dict), 'action should be dict'

            assert 'name' in action, 'action should have name'
            assert 'type' in action, 'action should have type'
            assert 'effective_after' in action, 'action should have effective_after'
            assert action['name'] is None or isinstance(action['name'], str), 'action name should be Optional[str]'
            assert isinstance(action['type'], str), 'action type should be str'
            assert isinstance(action['effective_after'], int), 'effective_after type should be int'

            if action['type']=='webpage':
                assert 'url' in action, 'webpage action should have url'
                assert isinstance(action['url'], str), 'webpage action url should be str'

            if action['type']=='card':
                assert 'url' in action, 'card action should have url'
                assert isinstance(action['url'], str), 'card action url should be str'

            if action['type']=='webdocker':
                assert 'docker_id' in action, 'webdocker action should have docker_id'
                assert isinstance(action['docker_id'], str), 'webdocker action docker_id should be str'
                assert ':' not in action['docker_id'], 'webdocker action docker_id should not contain protocol or port'

            elif action['type']=='terminal':
                assert 'host' in action, 'terminal action should have host'
                assert 'port' in action, 'terminal action should have port'
                assert isinstance(action['host'], str), 'terminal action host should be str'
                assert isinstance(action['port'], int), 'terminal action port should be int'
                assert ':' not in action['host'], 'terminal action host should not contain protocol or port'

            elif action['type']=='attachment':
                assert 'filename' in action, 'attachment action should have filename'
                assert 'file_path' in action, 'attachment action should have file_path'
                assert isinstance(action['filename'], str), 'attachment action filename should be str'
                assert isinstance(action['file_path'], str), 'attachment action file_path should be str'
                assert action['filename'] not in attachment_filenames, 'attachment action filename should be unique'

                attachment_filenames.add(action['filename'])

            elif action['type']=='dyn_attachment':
                assert 'filename' in action, 'dyn_attachment action should have filename'
                assert 'module_path' in action, 'dyn_attachment action should have module_path'
                assert isinstance(action['filename'], str), 'dyn_attachment action filename should be str'
                assert isinstance(action['module_path'], str), 'dyn_attachment action module_path should be str'
                assert action['filename'] not in attachment_filenames, 'dyn_attachment action filename should be unique'
                assert not action['module_path'].startswith('/'), 'dyn_attachment action module_path must be relative (to ATTACHMENT_PATH)'

                attachment_filenames.add(action['filename'])

        return actions

    # pass to frontend
    def describe_actions(self, cur_tick: int) -> List[Dict[str, Any]]:
        ret = []
        for action in self.actions:
            if action['name'] is not None and cur_tick>=action['effective_after']:
                if action['type']=='attachment':
                    ret.append({
                        'type': 'attachment',
                        'name': action['name'],
                        'filename': action['filename'],
                    })
                elif action['type']=='dyn_attachment':
                    ret.append({
                        'type': 'attachment',
                        'name': action['name'],
                        'filename': action['filename'],
                    })
                else:
                    ret.append(action)
        return ret

    ACTION_SNIPPETS = {
        'webpage': '''{"name": "题目网页", "effective_after": 0, "type": "webpage", "url" : "http://prob00-xxx.recruit.yulinsec.cn/"}''',
        'webdocker': '''{"name": "环境管理", "effective_after": 0, "type": "webdocker", "desc": "", "docker_id": ""}''',
        'terminal': '''{"name": "题目", "effective_after": 0, "type": "terminal", "host": "probXX.geekgame.pku.edu.cn", "port" : 0}''',
        'attachment': '''{"name": "题目附件", "effective_after": 0, "type": "attachment", "filename" : "probXX.zip", "file_path": ""}''',
        'dyn_attachment': '''{"name": "题目附件", "effective_after": 0, "type": "dyn_attachment", "filename" : "probXX.zip", "module_path": ""}''',
        'card': '''{"name": "题目网页", "effective_after": 0, "type": "card", "desc": "", "url" : "https://prob00-xxx.recruit.yulinsec.cn/"}''',
        'pwndocker': '''{"name": "环境管理", "effective_after": 0, "type": "pwndocker", "desc": "", "docker_id": "", "host": "", "attachment": ""}''',
    }

    @classmethod
    def check_flag_format(cls, flag: str) -> Optional[Tuple[str, str]]:
        if len(flag)>cls.MAX_FLAG_LEN:
            return 'FLAG_LEN', 'Flag过长'
        elif cls.VAL_FLAG.match(flag) is None:
            return 'FLAG_PATTERN', 'Flag格式错误'
        return None

    def category_color(self) -> str:
        return self.CAT_COLORS.get(self.category, self.FALLBACK_CAT_COLOR)