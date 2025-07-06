from django import forms

class CommentForm(forms.Form):  # 评论功能表单
    text = forms.CharField(
        label="评论内容",
        widget=forms.Textarea(attrs={
            "rows": 3, 
            "class": "form-control",
            "placeholder": "请输入您的评论..."
        }),
        max_length=500,
        help_text="最多500个字符"
    )
    
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text:
            text = text.strip()
            if len(text) < 1:
                raise forms.ValidationError("评论内容不能为空")
            if len(text) > 500:
                raise forms.ValidationError("评论内容不能超过500个字符")
        return text

class SearchForm(forms.Form):   # 搜索功能表单
    q = forms.CharField(    # 搜索框
        label="搜索",
        max_length=50,  # 增加最大长度
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "请输入关键字",
            "class": "form-control",
        }),
    )
    mode = forms.ChoiceField(   # 搜索模式选择
        choices=[("song", "歌曲"), ("artist", "歌手")],
        widget=forms.Select(attrs={"class": "form-select"}),  # 改用下拉框
        initial="song",
        required=False,
    )