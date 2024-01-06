from django import forms

from .models import League, Player


class LeagueAdminForm(forms.ModelForm):
    class Meta:
        model = League
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(LeagueAdminForm, self).__init__(*args, **kwargs)
        # Player モデルのインスタンスを名前でソート
        self.fields["first"].queryset = Player.objects.order_by("name")
        self.fields["second"].queryset = Player.objects.order_by("name")
        self.fields["third"].queryset = Player.objects.order_by("name")
        self.fields["player"].queryset = Player.objects.order_by("name")
