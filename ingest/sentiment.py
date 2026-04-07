#Utility that scores headline sentiment using TextBlob

from textblob import TextBlob

def analyze_sentiment(text):
    """This function takes a headline string and returns a dictionary
       with the score and label"""
    
    blob = TextBlob(text)
    score = round(blob.sentiment.polarity, 4)

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {"score" : score, "label": label}