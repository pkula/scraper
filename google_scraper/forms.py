from django import forms



class ScraperForm(forms.Form):
    quest = forms.CharField(label='Wpisz szkukane słowo',)