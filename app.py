import streamlit as st
import pickle
import pandas as pd
from io import StringIO
import pysrt
import re
import spacy

# Welcome text
st.title('Movie CEFR level.')
st.write('This app helps English learners to determine the CEFR level in a movie by its subtitles.')
st.write('---')

# Model
def load_model():
    with open ('model.pcl', 'rb') as fid:
        return pickle.load(fid)

model = load_model()

uploaded_file = st.file_uploader(label='Choose a file with subtitles in English', type=['txt','srt'])
st.write('---')


# Text processing
## Regular expressions
HTML = re.compile('<[^>]*>')                    # html тэги меняем на пробел
COMMENTS = re.compile('[\(\[][A-Za-z ]+[\)\]]') # комменты в скобках меняем на пробел
UPPER = re.compile('[[A-Za-z ]+[\:\]]')         # указания на того кто говорит (BOBBY:)
LETTERS = re.compile('[^a-zA-Z\'.,!? ]')        # все что не буквы меняем на пробел 
DOTS = re.compile('[\.]+')                      # многоточие меняем на точку
SPACES = re.compile('\s{2,}')                   # два или более пробельных символа подряд
SYMB = re.compile("[^\w\d'\s]")                 # знаки препинания кроме апострофа

## Data cleaning
def data_cleaning(text):
    text = HTML.sub(' ', text)                     # html тэги меняем на пробел
    text = UPPER.sub(' ', text)                    # указания на того кто говорит (BOBBY:)
    text = COMMENTS.sub(' ', text)                 # комменты в скобках меняем на пробел
    text = LETTERS.sub(' ', text)                  # все что не буквы меняем на пробел
    text = DOTS.sub(r'.', text)                    # многоточие меняем на точку
    text = SYMB.sub('', text)                      # знаки препинания кроме апострофа на пустую строку
    text = SPACES.sub(' ', text)                   # повторяющиеся пробелы меняем на один пробел
    text = re.sub('www', '', text)                 # кое-где остаётся www, то же меняем на пустую строку
    text = text.lstrip()                           # обрезка пробелов слева
    text = text.encode('ascii', 'ignore').decode() # удаляем все что не ascii символы   
    text = text.lower()                            # текст в нижний регистр
    return text

## SpaCy-lemmatization
def spacy_lemmatization(text):
    # Initialize spacy 'en_core_web_sm' model
    nlp = spacy.load('en_core_web_sm')
    # Lemmatization
    text = ' '.join([token.lemma_ for token in nlp(text)])
    return text

# Processing user's data
## Uploading file
if uploaded_file is not None:
    try:
        subs = StringIO(uploaded_file.getvalue().decode('utf-8')).read()
    except UnicodeDecodeError:
        try:
            subs = StringIO(uploaded_file.getvalue().decode('iso-8859-1')).read()
        except:
            pass

    data = pd.DataFrame(data={'subtitles':[subs]})
    
    ## Applying text processing functions
    data['subtitles'] = data['subtitles'].apply(lambda x: data_cleaning(x))
    data['subtitles'] = data['subtitles'].apply(lambda x: spacy_lemmatization(x))
    
    ## Forecast for data entered from the screen
    data['english_level'] = model.predict(data)
    level = data.loc[0, 'english_level']
    
    if level[0] == 'A':
        value_color = 'green'
    elif level[0] == 'B':
        value_color = 'blue'
    elif level[0] == 'C':
        value_color = 'red'
    
    style = "<h6 style='text-align: center; font-size: 26px;'>"
    style_end = "</h6>"
    text = f"{style}CEFR level of your subtitles: <span style='color:{value_color};'>{level}</span>{style_end}"
    st.markdown(text, unsafe_allow_html=True)