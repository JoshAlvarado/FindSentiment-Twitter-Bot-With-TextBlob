#Joshua Alvarado
#Josh.Alvarado0328@gmail.com

#Import the libraries
import tweepy
from textblob import TextBlob
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import re
import time
import matplotlib.pyplot as plt
import mysql.connector
mydb = mysql.connector.connect(
    host = "findsentiment.c2osmvmqtule.us-east-1.rds.amazonaws.com",
    user = "admin",
    passwd = "ofwgkta1",
    database = "twitterdb",
)
my_cursor = mydb.cursor()
sqlinsert= "INSERT INTO uses (user, mention, hashtag) VALUES (%s, %s, %s)"

# Twitter Api Credentials
Consumer_Key = "aFtN4QfJdqjk0GmxxRSiNtGhN"
Consumer_Secret_Key = "4xwCeig9D0tuDSyTo3goeYwqryQhHIelZPbBmcn3N6aKyb38Nn"
Access_Token = "1218311228344242176-D346wVdG6DWFI3vrg3F12pypWNj9ST"
Access_Token_Secret = "y3IB5zWGIJ5Yyy6XRSJVRTZmIDkj5A578n2TSEadfPDss"
#uthenticating Keys
auth = tweepy.OAuthHandler(Consumer_Key,Consumer_Secret_Key)
auth.set_access_token(Access_Token,Access_Token_Secret)
api = tweepy.API(auth, wait_on_rate_limit= True)

#Target term which is the the bot @name
target_term="@FindSentiment"

def create_visuals(mentioned):
    #Extract 100 tweets from user
    print("Now Creating Visuals")
    if "#" in mentioned:
      print("Hashtag")
      tweets = tweepy.Cursor(api.search,
              q=mentioned + "-filter:retweets",
              lang="en", result_type="recent").items(100)

      # Iterate and print tweets
      posts = [[tweet.text] for tweet in tweets]

      for tweet in tweets:
          print(tweet.text)
      [tweet.text for tweet in tweets]
      df = pd.DataFrame(data=posts, 
                    columns=['tweets'])
      df    
    else:
      try:
        print("Does not include a hashtag")
        posts = api.user_timeline(screen_name=mentioned, count=100, lang= "en",tweet_mode="extended")
        print("Got the user tweets")
        df = pd.DataFrame( [tweet.full_text for tweet in posts], columns=['tweets'])
        df.head()
        df
      except Exception:
        print("Something went wrong with pulling tweets")


    #Clean the text
    #Create a function to clean the tweets
    def cleanTxt(text):
      text = re.sub(r'@[\w:]+', '', text) #removes @mentions
      text = re.sub(r'#','',text) #removing # symbol
      text = re.sub(r'RT[\s]+','',text) #removes retweets
      text = re.sub(r'https?:\/\/\S+','', text) #remove hyperlinks
      return text

    df['tweets'] = df['tweets'].apply(cleanTxt)

    #Show the cleaned text
    df

    # Create a function to get the subjectivity
    def getSubjectivity(text):
      return TextBlob(text).sentiment.subjectivity

    # Create a function to get the polarity
    def getPolarity(text):
      return TextBlob(text).sentiment.polarity

    # Create two new columns
    df['Subjectivity'] = df['tweets'].apply(getSubjectivity)
    df['Polarity'] = df['tweets'].apply(getPolarity)

    # Show the new dataframe with the new columns



    #Create a function to compute the negative, neutral and positive analysis
    def getAnalysis(score):
      if score < 0:
        return 'Negative'
      elif score == 0:
        return 'Neutral'
      else:
        return 'Positive'

    df['Analysis'] = df['Polarity'].apply(getAnalysis)

    df

    # Plot the polarity and subjectivity 
    plt.figure(figsize=(8,6))
    for i in range(0, df.shape[0]):
      plt.scatter(df['Polarity'][i],df['Subjectivity'][i], color='blue')
      
    plt.title('Sentiment Analysis for ' + mentioned)

    plt.xlabel('Polarity')
    plt.ylabel('Subjectivity')
    plt.savefig('plot.png',bbox_inches='tight',dpi=600)
    plt.close()

    # show the value counts

    df['Analysis'].value_counts()

    # plot and visualize the counts

    plt.title('Sentiment Analysis for ' + mentioned)

    plt.xlabel('Sentiment')
    plt.ylabel('Counts')

    df['Analysis'].value_counts().plot(kind='bar')
    plt.savefig('graph.png',bbox_inches='tight',dpi=600)
    plt.close()


    def forhashtags(text):

      remove = re.sub(r'#','',mentioned) #removing # symbol from mentioned
      clean = re.compile(remove,flags=re.IGNORECASE)
      text = clean.sub('', text,)
      return text

        # Plot the Word Cloud
    df['tweets'] = df['tweets'].apply(forhashtags)
    df
    
    allWords = ' '.join([twts for twts in df ['tweets']])
    wordCloud = WordCloud(width = 500, height = 300, random_state = 21, max_font_size=119,).generate(allWords)

    plt.imshow(wordCloud, interpolation = "bilinear")
    plt.axis('off')
    plt.title('Most common words for ' + mentioned)
    plt.savefig('wordcloud.png',bbox_inches='tight',dpi=600)
    plt.close()

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        global tweet_id
        global handle
        global text
        global reply
        print(status.text)
        print(status.in_reply_to_status_id)
        reply = status.in_reply_to_status_id 
        if reply == None:
            print("not a reply")
            text = status.text
            text = re.sub(r'@findsentiment','',text.lower())
            reply = status.in_reply_to_status_id
            tweet_id = status.id
            handle = status.user.screen_name
            status_id = status.id
            print(status.text)
            print(text)
            print(handle)
            print(tweet_id)
            start(handle,text,tweet_id)      
        else:
            reply = status.in_reply_to_status_id
            reply = api.get_status(reply)
            replyUser = reply.user.screen_name 
            print(replyUser)
            if replyUser == "FindSentiment":
                print("This tweet is a reply, skipping")
            else:
                print("Not a reply")
                text = status.text
                text = re.sub(r'@findsentiment','',text.lower()) 
                reply = status.in_reply_to_status_id
                tweet_id = status.id
                handle = status.user.screen_name 
                status_id = status.id
                print(status.text)
                print(text)
                print(handle)
                print(tweet_id)
                start(handle,text,tweet_id)


def start(handle,text,tweet_id): 
    global mentioned
    if "#" in text:
      print("it has a hashtag")
      text = re.findall('[@#:][^\s]+', text)[0]
      mentioned = text
      record1 = (handle, "", mentioned)
      my_cursor.execute(sqlinsert, record1)
      mydb.commit()
      print(mentioned)
      tweetit()
    elif '@' in text:
      print("It has a mention")
      if len(''.join([l for l in text.split('@') if l != '']))+1 == len(text):
         print('It has 1 @mention')
         text = re.findall('[@#:][^\s]+', text)[0]
         mentioned = text
         record1 = (handle, mentioned, "")
         my_cursor.execute(sqlinsert, record1)
         mydb.commit()
         print("this is mentioned")
         print(mentioned)
         tweetit()
      else:
         print('More than 1 @mention')
         print('skipping this tweet')
    else:
      print("it has nothing")
    #   handle = handle
      mentioned = handle
      record1 = (handle, handle, "")
      my_cursor.execute(sqlinsert, record1)
      mydb.commit()
      tweetit()


def tweetit():
  try:
    create_visuals(mentioned)
    images = ('wordcloud.png', 'graph.png','plot.png')
    test = [api.media_upload(i) for i in images]
    media_ids = [api.media_upload(i).media_id_string for i in images]
    print("Images Uploaded")
    api.update_status(
                      "@%s thank you for using FindSentiment! Here's your data!" %
                      handle, media_ids=media_ids,
                      in_reply_to_status_id=tweet_id)
    print("WE DID IT SUCCESS!")
  except Exception:
    print("something went wrong")
    raise


if __name__ == "__main__":
  print("Starting now :D")
  myStreamListener = MyStreamListener(api)
  myStream = tweepy.Stream(auth = api.auth, listener = myStreamListener)






  myStream.filter(track = ["@FindSentiment"])

  