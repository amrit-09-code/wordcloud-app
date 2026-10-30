import streamlit as st
import pandas as pd
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import PyPDF2
from docx import Document
import plotly.express as px
import base64
from io import BytesIO

def read_txt(file):
    return file.getvalue().decode("utf-8")

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    return " ".join([para.text for para in doc.paragraphs])

def filter_stopwords(text, additional_stopwords=[]):
    words = text.split()
    all_stopwords = STOPWORDS.union(set(additional_stopwords))
    filtered_words = [word for word in words if word.lower() not in all_stopwords]
    return " ".join(filtered_words)

def get_image_download_link(buffered, format_):
    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return f'<a href="data:image/{format_};base64,{image_base64}" download="WordCloud.{format_}">Download WordCloud as {format_}</a>'

st.title("Word Cloud Generator")
st.subheader("upload a pdf,docx or text file to generate a wordcloud")
uploaded_file = st.file_uploader("choose a file", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        text = read_txt(uploaded_file)
    elif uploaded_file.type == "application/pdf":
        text = read_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = read_docx(uploaded_file)
    else:
        st.error("file type not supported. please upload a txt, pdf or docx")
        st.stop()

    words = text.split()
    words_count = pd.DataFrame({'word': words}).groupby('word').size().reset_index(name='count').sort_values(by='count', ascending=False)
    
    use_standard_stopwords = st.sidebar.checkbox("use standard stopwords?", True)
    top_words = words_count['word'].head(50).tolist()
    additional_stopwords = st.sidebar.multiselect("additional stopwords:", sorted(top_words))

    if use_standard_stopwords:
        all_stopwords = STOPWORDS.union(set(additional_stopwords))
    else:
        all_stopwords = set(additional_stopwords)
 
    text = filter_stopwords(text, all_stopwords)

    if text:
        width = st.sidebar.slider("select word cloud width", 400, 2000, 1200, 50)
        height = st.sidebar.slider("select word cloud height", 200, 2000, 800, 50)

        st.subheader("Generated word cloud")
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        WordCloud_img = WordCloud(width=width, height=height, background_color='white', max_words=200).generate(text)
        ax.imshow(WordCloud_img, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

        # Download part
        format_ = st.selectbox("select file format to save the plot", ["png", "jpeg", "svg", "pdf"])
        resolution = st.slider("select resolution", 100, 500, 300, 50)
        
        buffered = BytesIO()
        WordCloud_img.to_image().save(buffered, format=format_.upper() if format_ != "svg" else "PNG")
        st.markdown(get_image_download_link(buffered, format_), unsafe_allow_html=True)

        st.subheader("word count table")
        words = text.split()
        words_count = pd.DataFrame({'word': words}).groupby('word').size().reset_index(name='count').sort_values(by='count', ascending=False)
        st.dataframe(words_count.head(100), use_container_width=True)

        fig2 = px.bar(words_count.head(20), x='word', y='count', title="Top 20 Words")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No text left after filtering")