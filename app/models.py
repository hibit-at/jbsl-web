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
    bgColor = models.CharField(default='#000000',max_length=100)
    isShadow = models.BooleanField(default=False)

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
    lid = models.CharField(default='', max_length=10)
    color = models.CharField(default='white', max_length=20)
    imageURL = models.CharField(default='', max_length=100)

    def __str__(self):
        return f'{self.title} ({self.diff}) by {self.author}'


class Playlist(models.Model):
    title = models.CharField(default='', max_length=100)
    editor = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True)
    image = models.CharField(default='', max_length=400000)
    songs = models.ManyToManyField(Song)
    recommend = models.ManyToManyField(
        Song, related_name='recommend', blank=True)
    description = models.CharField(default='', max_length=200)
    isEditable = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class SongInfo(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.playlist} {self.song} {self.order}'

class League(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, related_name='owner')
    description = models.CharField(default='', max_length=100, blank=True)
    color = models.CharField(default='', max_length=20)
    player = models.ManyToManyField(Player, blank=True, related_name='league')
    method = models.IntegerField(default=0)
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
    ownerComment = models.CharField(default='', max_length=1000)

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

    def __str__(self):
        name = self.player.name
        title = self.song.title
        return name + ' > ' + title


class LeagueComment(models.Model):
    message = models.CharField(default='', max_length=50, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.message)


class Headline(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(default='', max_length=200)
    time = models.DateTimeField()

    def __str__(self):
        return f'{str(self.player)} -> {str(self.text)}'


class Badge(models.Model):
    name = models.CharField(max_length=50)
    image_name = models.CharField(max_length=50)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.name)