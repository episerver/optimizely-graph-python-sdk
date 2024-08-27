import os

from groq import Groq


AUTH_TOKEN = os.getenv(
    'AUTH_TOKEN', "<TOKEN>")

client = Groq(
    api_key=os.environ.get(AUTH_TOKEN),
)

post_prompt = "Do not explain your answer. Do not change adverbs, such as \"when\" to \"what\".  Don't give information not mentioned in the CONTEXT INFORMATION."
chats = []
chats.insert(0, {"role": "system", "content": "You only rewrite the question when there is an ambiguous pronoun in the Question, or else just return the Question without any changes. You do not know anything about movies or actors. Return one Question with only coreference resolution based on the Context. Example, replace \"he\" with \"Steven\"."})
# chats.append({"role": "user", "content": f"Context: Who is james cameron?\n\nQuestion: What other movies did he direct?"})
# chats.append({"role": "user", "content": f"What other movies did James Cameron direct, besides Titanic and Avatar?\n\nWhat else did he direct?"})
# chats.append({"role": "user", "content": f"Context: What other movies did James Cameron direct, besides Titanic and Avatar?\n\Question: Who were cast in the first movie?" + post_prompt})
# chats.append({"role": "user", "content": f"Context: movies about mobsters?\n\Question: who acted in the godfather?"})
# chats.append({"role": "user", "content": f"Context: who acted in the godfather?\n\Question: what else did brando act in?" + post_prompt})
# chats.append({"role": "user", "content": f"Context: who is steven spielberg?\n\Question: what is the summary of jurassic park?" + post_prompt})
# chats.append({"role": "user", "content": f"Context: who is steven spielberg?\n\Question: tell me more about aliens?" + post_prompt})
chats.append({"role": "user", "content": f"Context: who is steven spielberg?\n\Question: in what year was aliens released?" + post_prompt})
# chats.append({"role": "user", "content": f"Context: What other movies did James Cameron direct, besides Titanic and Avatar?\n\Question: Who were cast in the last movie?" + post_prompt})

chat_completion = client.chat.completions.create(
    messages=chats,
    model="llama3-8b-8192",
    temperature=0.1,
)

print(chat_completion.choices[0].message.content)