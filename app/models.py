from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Player(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True)
    discordID = models.CharField(max_length=50)
    isActivated = models.BooleanField(default=False)
    inDiscord = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    sid = models.CharField(max_length=100)
    pp = models.FloatField(default=0)
    borderPP = models.FloatField(default=0)
    message = models.CharField(default='', max_length=50, blank=True)
    isAbstein = models.BooleanField(default=False)
    isStaff = models.BooleanField(default=False)
    rival = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True)
    twitter = models.CharField(default='', max_length=50, blank=True)
    twitch = models.CharField(default='', max_length=50, blank=True)
    booth = models.CharField(default='', max_length=50, blank=True)
    imageURL = models.CharField(default='', max_length=100)
    hmd = models.CharField(default='', max_length=50)
    isSupporter = models.BooleanField(default=False)
    userColor = models.CharField(default='firebrick', max_length=100)
    bgColor = models.CharField(default='#000000', max_length=100)
    isShadow = models.BooleanField(default=False)
    yurufuwa = models.IntegerField(default=0)
    mapper = models.IntegerField(default=0)
    mapper_name = models.CharField(default='',max_length=100,blank=True)
    accPP = models.FloatField(default=0)
    techPP = models.FloatField(default=0)
    passPP = models.FloatField(default=0)

    def __str__(self):
        return str(self.name)


class Song(models.Model):
    title = models.CharField(default='', max_length=200)
    author = models.CharField(default='', max_length=100)
    diff = models.CharField(default='', max_length=20)
    char = models.CharField(default='', max_length=50)
    notes = models.IntegerField(default=0)
    bsr = models.CharField(default='', max_length=10)
    hash = models.CharField(default='', max_length=100)
    lid = models.CharField(default='', max_length=10, blank=True ,null=True)
    color = models.CharField(default='white', max_length=20)
    imageURL = models.CharField(default='', max_length=100)
    bid = models.CharField(default='', max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.title} ({self.diff}) by {self.author}'


class JPMap(models.Model):
    uploader = models.ForeignKey(Player, on_delete=models.CASCADE, default=None)
    name = models.CharField(default='', max_length=2000)
    bsr = models.CharField(default='', max_length=10)
    hash = models.CharField(default='', max_length=100)
    char = models.CharField(default='', max_length=50)
    diff = models.CharField(default='', max_length=20)
    nps = models.FloatField(default=0)
    createdAt = models.DateTimeField()

    def __str__(self):
        return f'{self.name}-{self.diff}-{self.char} by {self.uploader.name}'


class Playlist(models.Model):
    title = models.CharField(default='', max_length=100)
    editor = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True)
    image = models.CharField(default='', max_length=400000)
    songs = models.ManyToManyField(Song, blank=True)
    recommend = models.ManyToManyField(
        Song, related_name='recommend', blank=True)
    description = models.CharField(default='', max_length=200, blank=True)
    isEditable = models.BooleanField(default=False)
    CoEditor = models.ManyToManyField(
        Player, related_name='CoEditor', blank=True)
    isHidden = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class SongInfo(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    genre = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return f'{self.playlist} {self.song} {self.order}'


class League(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, related_name='owner')
    description = models.CharField(default='', max_length=100, blank=True)
    color = models.CharField(default='', max_length=30)
    player = models.ManyToManyField(Player, blank=True, related_name='league')
    max_valid = models.IntegerField(default=0)
    limit = models.FloatField(default=2000)
    end = models.DateTimeField(default=None, blank=True)
    isPermanent = models.BooleanField(default=False)
    isOpen = models.BooleanField(default=False)
    isPublic = models.BooleanField(default=True)
    isLive = models.BooleanField(default=True)
    invite = models.ManyToManyField(Player, blank=True, related_name='invite')
    virtual = models.ManyToManyField(
        Player, blank=True, related_name='virtual')
    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, null=True, blank=True)
    first = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='first')
    second = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='second')
    third = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='third')
    isOfficial = models.BooleanField(default=False)
    ownerComment = models.CharField(default='', max_length=1000, blank=True)
    border_line = models.IntegerField(default=8)
    prohibited_leagues = models.ManyToManyField('self', blank=True, symmetrical=True, related_name='prohibited')

    def __str__(self):
        return str(self.name)


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    song = models.ForeignKey(
        Song, on_delete=models.CASCADE, related_name='score')
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    acc = models.FloatField(default=0)
    rawPP = models.FloatField(default=0)
    miss = models.IntegerField(default=0)
    comment = models.CharField(default='', max_length=50, blank=True)
    rank = models.IntegerField(default=0)
    pos = models.IntegerField(default=0)
    weight_acc = models.FloatField(default=0)
    decorate = models.CharField(max_length=100, blank=True)
    valid = models.BooleanField(default=False)
    beatleader = models.CharField(default='', max_length=100, blank=True)

    def __str__(self):
        name = self.player.name
        title = self.song.title
        league = self.league
        return f'{name} > {title} ({league})'


class Participant(models.Model):
    message = models.CharField(default='', max_length=50, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    rank = models.IntegerField(default=0)
    count_pos = models.IntegerField(default=0)
    count_weight_acc = models.IntegerField(default=0)
    theoretical = models.FloatField(default=0)
    valid_count = models.IntegerField(default=0)
    count_acc = models.FloatField(default=0)
    tooltip_pos = models.CharField(default='', max_length=2000)
    tooltip_weight_acc = models.CharField(default='', max_length=2000)
    tooltip_valid = models.CharField(default='', max_length=2000)
    tooltip_acc = models.CharField(default='', max_length=2000)
    decorate = models.CharField(default='', max_length=100, blank=True)

    def __str__(self):
        return f'{self.player} in {self.league}'


class Headline(models.Model):
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(default='', max_length=200)
    time = models.DateTimeField()
    score = models.ForeignKey(
        Score, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{str(self.player)} -> {str(self.text)}'


class Badge(models.Model):
    name = models.CharField(max_length=50)
    image_name = models.CharField(max_length=50)
    player = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='badges')

    def __str__(self):
        return str(self.name)


class Match(models.Model):
    title = models.CharField(max_length=50)
    player1 = models.ForeignKey(Player,on_delete=models.SET_NULL, null=True,related_name='player1')
    retry1 = models.BooleanField()
    result1 = models.IntegerField(default=0)
    player2 = models.ForeignKey(Player,on_delete=models.SET_NULL, null=True, related_name='player2')
    retry2 = models.BooleanField()
    result2 = models.IntegerField(default=0)
    now_playing = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True)
    map_info = models.CharField(max_length=1000)
    highest_acc = models.FloatField(default=0)
    state = models.IntegerField(default=0)
    editor = models.ManyToManyField(Player)
    playlist = models.ForeignKey(Playlist,on_delete=models.SET_NULL, null=True)
    league = models.ForeignKey(League,on_delete=models.SET_NULL, null=True)


class DGA(models.Model):
    beatleader = models.CharField(default='', max_length=100, blank=True)
    dance = models.FloatField()
    gorilla = models.FloatField()
    song_mapper = models.CharField(max_length=1000)
    player_name = models.CharField(max_length=100, default='')
    sid = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.player_name} {self.song_mapper}'