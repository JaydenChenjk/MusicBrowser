from django import forms

class CommentForm(forms.Form):
    text = forms.CharField(
        label="评论",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        max_length=500,
    )


# 搜索表单
class SearchForm(forms.Form):
    q = forms.CharField(
        label="搜索",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "请输入关键字",
            "class": "form-control",
        }),
    )
    mode = forms.ChoiceField(
        choices=[("song", "歌曲"), ("artist", "歌手")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="song",
    )