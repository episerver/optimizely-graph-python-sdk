import json
import os
import gql
import nltk

from groq import Groq

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from flask import Flask, render_template, request

app = Flask(__name__)

AUTH_TOKEN = os.getenv(
    'AUTH_TOKEN', "<TOKEN>")

GROQ_CLIENT = Groq(
    api_key=os.environ.get(AUTH_TOKEN),
)

OG_ENDPOINT = "https://cg.optimizely.com/content/v2?auth=<PUBLIC_KEY>"

QUESTION = os.getenv('QUESTION', "Who am I?")
CHAT_HISTORY_FILE = "chat_history.txt"

POST_PROMPT = "Don't explain your answers. Don't give information not mentioned in the CONTEXT INFORMATION."
PRONOUNS = ["he", "she", "it", "this", "that", "his", "her", "last", "first"]

nltk.download('stopwords')
nltk.download('punkt')
STOP_WORDS = set(stopwords.words('english'))
STOP_WORDS.add("movies")
STOP_WORDS.add("?")

transport = AIOHTTPTransport(
    url=OG_ENDPOINT)
gql_client = Client(transport=transport, fetch_schema_from_transport=True)


def query_with_gql(query):
    return gql(
        """
{
  Movie(
    locale: ALL
    where: {
      _or: [
        { cast: { match: \"""" + query + """\", boost: 5 } }
        { director: { match: \"""" + query + """\", boost: 2 } }
        { title: { match: \"""" + query + """\", boost: 10 } }
        { _fulltext: { match: \"""" + query + """\" } }
      ]
    }
    orderBy: { _ranking: SEMANTIC }
    limit: 10
  ) {
    items {
      cast
      director
      overview
      title
      genre
      year
    }
  }
}
        """
    )


def rewrite_question(question, previous):
    chats = []
    if previous:
        chats.insert(0, {"role": "system", "content": "You only rewrite the question. Do not change the question type. Do not explain. You do not know anything about movies or actors. Return one Question with only coreference resolution based on the Context. Example, replace \"he\" with a name. If you cannot apply coreference resolution, then just return the original Question without any changes."})
        chats.append(
            {"role": "user", "content": f"Context: {previous}\n\nQuestion: {question}" + POST_PROMPT})
        rewritten_question = get_chat_completion(chats=chats)
        return rewritten_question
    return question


def save_chat_history(contents):
    with open(CHAT_HISTORY_FILE, 'a') as history_file:
        history_file.write(json.dumps(contents) + "\n")
    entries = sum(1 for _ in open(CHAT_HISTORY_FILE))
    if entries > 5:
        with open(CHAT_HISTORY_FILE, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(CHAT_HISTORY_FILE, 'w') as fout:
            fout.writelines(data[1:])


def get_chat_history():
    contents = []
    try:
        with open(CHAT_HISTORY_FILE) as f:
            try:
                while line := f.readline():
                    contents.append(json.loads(line))
            except:
                return contents
    except FileNotFoundError:
        return contents
    return contents


def get_chat_completion(chats):
    chat_completion = GROQ_CLIENT.chat.completions.create(
        messages=chats,
        model="llama3-8b-8192",
        temperature=0.2,
    )
    return chat_completion.choices[0].message.content


def get_rag_answer(question):
    print("Original question: {}".format(question))
    chats = get_chat_history()
    previous_question = None
    if len(chats) > 0:
        previous_question = chats[-1]["content"].split("\n")[-1]
    new_question = question
    if previous_question and any(word in question.removesuffix('?').split() for word in PRONOUNS):
        new_question = rewrite_question(
            question=question, previous=previous_question.removesuffix(POST_PROMPT))
        print("Rewritten question by AI: {}".format(new_question))
    search_phrase = " ".join([w for w in word_tokenize(
        new_question) if not w.lower() in STOP_WORDS])
    gql_result = gql_client.execute(query_with_gql(search_phrase))
    latest_prompt = {
        "role": "user", "content": f"Context: {gql_result}\n\nQuestion: {new_question} {POST_PROMPT}"}
    chats.insert(0, {"role": "system", "content": "You are a movie expert. You return answers as full sentences. If there is an enumeration, return a list with numbers. If the question can't be answered based on the context, say \"I don't know\". Do not return an empty answer. Do not start answer with: \"based on the context\". Do not refer to the \"given context\". Do not refer to \"the dictionary\". You learn and try to answer from contexts related to previous question."})
    chats.append(latest_prompt)
    answer = get_chat_completion(chats=chats)
    save_chat_history(latest_prompt)
    return answer


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    response = get_rag_answer(userText)
    return response


if __name__ == "__main__":
    app.run()
