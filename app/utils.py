class ComparedScore:

    my_acc = 0
    rival_acc = 0

    def __init__(self) -> None:
        pass

    def set_my_acc(self, acc: float):
        self.my_acc = max(self.my_acc, acc)

    def set_rival_acc(self, acc: float):
        self.rival_acc = max(self.rival_acc, acc)

    def win(self) -> bool:
        return self.my_acc >= self.rival_acc

    def dif(self) -> int:
        return self.my_acc - self.rival_acc

    def __repr__(self) -> str:
        return f'{self.my_acc} vs {self.rival_acc}'

class Result:

    def __init__(self, text, link) -> None:
        self.text = text
        self.link = link

    def __str__(self) -> str:
        return str(self.text)

class Results:

    def __init__(self) -> None:
        self.results = []

    def append(self, text, link=None):
        append_res = Result(text, link)
        self.results.append(Result(text, link))

    def __str__(self) -> str:
        return ','.join(map(str, self.results))
    

diff_label = {
    1: 'Easy',
    3: 'Normal',
    5: 'Hard',
    7: 'Expert',
    9: 'ExpertPlus',
}

diff_label_inv = {
    'Easy': 1,
    'Normal': 3,
    'Hard': 5,
    'Expert': 7,
    'ExpertPlus': 9,
}

char_dict = {
    'SoloStandard': 'Standard',
    'SoloLawless': 'Lawless',
    'SoloOneSaber': 'OneSaber',
    'Solo90Degree': '90Degree',
    'Solo360Degree': '360Degree',
    'SoloNoArrows': 'NoArrows',
}

char_dict_inv = {
    'Standard': 'SoloStandard',
    'Lawless': 'SoloLawless',
    'OneSaber': 'SoloOneSaber',
    '90Degree': 'Solo90Degree',
    '360Degree': 'Solo360Degree',
    'NoArrows': 'SoloNoArrows',
}

col_dict = {
    1: 'rgba(130,211,255,.8)',
    3: 'rgba(128,255,128,.8)',
    5: 'rgba(255,128,60,.8)',
    7: 'rgba(255,128,128,.8)',
    9: 'rgba(220,130,250,.8)',
}

hmd_dict = {
    0: 'Unknown',
    1: 'Oculus Rift CV1',
    2: 'Vive',
    4: 'Vive Pro',
    8: 'Windows Mixed Reality',
    16: 'Rift S',
    32: 'Oculus Quest',
    61: 'Quest Pro',
    64: 'Valve Index',
    128: 'Vive Cosmos',
    256: 'Quest 2',
}

league_colors = [
    {'value': 'rgba(130,211,255,.8)', 'text': 'Blue'},
    {'value': 'rgba(128,255,128,.8)', 'text': 'Green'},
    {'value': 'rgba(255,128,60,.8)', 'text': 'Orange'},
    {'value': 'rgba(255,128,128,.8)', 'text': 'Red'},
    {'value': 'rgba(220,130,250,.8)', 'text': 'Purple'},
    {'value': 'rgba(255,255,128,.8)', 'text': 'Yellow'},
]

state_dict = {
    -2: 'RETRY PLAYER1 ADVANTAGE',
    -1: 'PLAYER1 WIN SUSPEND',
    0: 'STAND BY',
    1: 'PLAYER2 WIN SUSPEND',
    2: 'RETRY PLAYER2 ADVANTAGE',
}

genres = [
    "---",
    "Acc",
    "Tech",
    "Balanced",
    "FullRange",
    "Speed",
    "Stamina",
    "Concept",
]

join_comment = {
    -1: '',
    0: 'あなたはこのリーグに参加しています。',
    1: '終了したリーグに参加することはできません。',
    2: '非公開のリーグに参加することはできません。',
    3: 'あなたは実力が高すぎるため、このリーグには参加できません……。',
    4: '公式リーグでは、終了 48 時間前を過ぎると参加することはできません。',
    5: '同時参加不可能なリーグにすでに参加しているため、このリーグには参加できません。',
    6: '',
}

def get_decorate(acc: float) -> str:
    if acc < 50:
        return 'color:dimgray'
    if 95 <= acc < 96:
        return 'font-weight:bold;text-shadow: 1px 1px 0 deepskyblue'
    if 96 <= acc < 97:
        return 'font-weight:bold;text-shadow: 1px 1px 0 mediumseagreen'
    if 97 <= acc < 98:
        return 'font-weight:bold;text-shadow: 1px 1px 0 orange'
    if 98 <= acc < 99:
        return 'font-weight:bold;text-shadow: 1px 1px 0 tomato'
    if 99 <= acc <= 100:
        return 'font-weight:bold;text-shadow: 1px 1px 0 violet'
    return 'None'


def score_to_acc(score: float, notes: int) -> float:
    max_score = 0
    multiply_count = 1
    while notes > 0 and multiply_count > 0:
        max_score += 115
        notes -= 1
        multiply_count -= 1
    multiply_count = 4
    while notes > 0 and multiply_count > 0:
        max_score += 115*2
        notes -= 1
        multiply_count -= 1
    multiply_count = 8
    while notes > 0 and multiply_count > 0:
        max_score += 115*4
        notes -= 1
        multiply_count -= 1
    while notes > 0:
        max_score += 115*8
        notes -= 1
    if max_score == 0:
        return 0
    return score/max_score*100


def slope(n: int) -> int:
    if n == 1:
        return 0
    if n == 2:
        return -3
    return -(n+2)


def validation(s: str) -> str:
    ans = ''
    for c in s:
        if b'\xc2\x80' <= c.encode('utf-8') and c.encode('utf-8') <= b'\xd4\xbf':
            continue
        ans += c
    return ans

