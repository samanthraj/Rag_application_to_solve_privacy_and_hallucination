from groq import Groq

client = Groq(api_key="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")

models = client.models.list()

for m in models.data:
    print(m.id)