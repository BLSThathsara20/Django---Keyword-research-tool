import requests
from django.shortcuts import render
from bs4 import BeautifulSoup
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import re
import string
from summa import keywords as textrank_keywords
from django.http import HttpResponse, HttpResponseBadRequest
import csv

def get_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None


def preprocess_text(text):
    # Remove HTML tags
    text = BeautifulSoup(text, 'html.parser').get_text()

    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    return text


def analyze(url):
    html = get_html(url)
    if html is None:
        return [], [], [], [], {}, []

    text = preprocess_text(html)

    # Tokenize the text into words
    words = word_tokenize(text.lower())

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # Perform stemming on the words
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]

    # Count repeatable words
    repeatable_words = [word for word, count in Counter(words).items() if count > 1]

    # Extract bi-grams
    bigrams = [words[i] + ' ' + words[i + 1] for i in range(len(words) - 1)]

    # Extract keywords using TextRank
    textrank_keywords_list = textrank_keywords.keywords(text).split('\n')
    keywords = Counter(textrank_keywords_list)

    # Extract titles
    titles = [tag.text for tag in BeautifulSoup(html, 'html.parser').find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]

    # Extract header links
    header_links = [link['href'] for header in BeautifulSoup(html, 'html.parser').find_all('header')
                    for link in header.find_all('a', href=True)]

    # Count the occurrences of each keyword in the original text
    keyword_counts = {keyword: words.count(keyword) for keyword in keywords}

    # Sort the keywords by count in descending order
    sorted_keywords = [(keyword, count) for keyword, count in keyword_counts.items()]
    sorted_keywords.sort(key=lambda x: x[1], reverse=True)

    return sorted_keywords, repeatable_words, bigrams, titles, keyword_counts, header_links


def analyze_website(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        keywords, repeatable_words, bigrams, titles, keyword_counts, header_links = analyze(url)

        # Extract the top keywords and their counts
        top_keywords = [(keyword, count) for keyword, count in keywords[:10]]  # Change the number as per your requirement

        # Extract the TextRank keywords and their counts
        textrank_keywords = [(keyword, count) for keyword, count in keyword_counts.items()]

        # Retrieve the list of previously searched URLs from the cookie
        url_list = request.COOKIES.get('url_list', '').split(',')

        # Check if the URL is already in the list
        if url not in url_list:
            # Add the current URL to the list
            url_list.append(url)

        # Limit the list to 10 most recent URLs
        url_list = url_list[-10:]

        # Save the updated URL list in the cookie
        response = render(request, 'playground/analysis_result.html', {
            'url': url,
            'repeatable_words': repeatable_words,
            'bigrams': bigrams,
            'keywords': keywords,
            'top_keywords': top_keywords,
            'textrank_keywords': textrank_keywords,
            'titles': titles,
            'keyword_counts': keyword_counts,
            'header_links': header_links,
            'url_list': url_list,
        })
        response.set_cookie('url_list', ','.join(url_list))

        return response
    else:
        # Retrieve the list of previously searched URLs from the cookie
        url_list = request.COOKIES.get('url_list', '').split(',')

        return render(request, 'playground/analyze_website.html', {
            'url_list': url_list,
        })


def download_keywords(request):
    keywords = request.session.get('keywords', [])  # Retrieve the keyword data from the session
    titles = request.session.get('titles', [])
    top_keywords = request.session.get('top_keywords', [])
    header_links = request.session.get('header_links', [])
    all_keywords = request.session.get('all_keywords', [])
    repeatable_words = request.session.get('repeatable_words', [])
    bigrams = request.session.get('bigrams', [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="keywords.csv"'

    writer = csv.writer(response)
    writer.writerow(['Titles', 'Top Keywords', 'Header Links', 'All Keywords', 'Repeatable Words', 'Bi-grams'])

    # Get the maximum number of rows among all the keyword lists
    max_rows = max(len(keywords), len(titles), len(top_keywords), len(header_links), len(all_keywords),
                   len(repeatable_words), len(bigrams))

    for i in range(max_rows):
        row = [titles[i] if i < len(titles) else '',
               top_keywords[i][0] if i < len(top_keywords) else '',
               header_links[i] if i < len(header_links) else '',
               all_keywords[i] if i < len(all_keywords) else '',
               repeatable_words[i] if i < len(repeatable_words) else '',
               bigrams[i] if i < len(bigrams) else '']
        writer.writerow(row)

    return response


def subpage_analysis_result(request):
    if request.method == 'GET':
        link = request.GET.get('link')

        # Perform analysis for the subpage link
        keywords, repeatable_words, bigrams, titles, keyword_counts, header_links = analyze(link)

        # Create the context for rendering the template
        context = {
            'url': link,
            'repeatable_words': repeatable_words,
            'bigrams': bigrams,
            'keywords': keywords,
            'titles': titles,
            'keyword_counts': keyword_counts,
            'header_links': header_links,
        }

        return render(request, 'playground/subpage_analysis_result.html', context)
    else:
        return HttpResponseBadRequest("Invalid request method.")
