from django import forms

class CommentForm(forms.Form):  # 评论功能表单
    text = forms.CharField(
        label="评论",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),  # 支持多行文本输入
        max_length=500,
    )

class SearchForm(forms.Form):   # 搜索功能表单
    q = forms.CharField(    # 搜索框
        label="搜索",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={   # 渲染为单行文本框
            "placeholder": "请输入关键字",
            "class": "form-control",
        }),
    )
    mode = forms.ChoiceField(   # 搜索模式选择
        choices=[("song", "歌曲"), ("artist", "歌手")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="song",
    )