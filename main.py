from bot.chat import user_query
from flask import Flask, request, jsonify
from crawling.crawl import crawl_website as crawler
from embeddings.generate_embeddings import create_embeddings_per_file
from chroma.storage import save_context

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Q&A ChatBot API!"


@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    saved_files=crawler(url=url)
    if saved_files is None:
        return jsonify({"error": "Crawling failed"}), 500
    vector=create_embeddings_per_file(saved_files)
    embeddings, chunks, metadata = vector
    success = save_context(embeddings=embeddings, chunks=chunks, metadata=metadata)
    if(success):
        return jsonify({"message": "Crawling and embedding completed successfully"}), 200
    else:
        return jsonify({"error": "Failed to save context"}), 500


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    response, all_source = user_query(prompt)

    json_response = jsonify({"response": response, "source": all_source})
    print(f"json response: \n{json_response.get_json()}")
    return json_response


