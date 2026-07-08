import os
import shutil

from bot.chat import user_query
from flask import Flask, request, jsonify, render_template
from crawling.crawl import crawl_website as crawler, reset_state, request_cancel
from embeddings.generate_embeddings import create_embeddings_per_file
from chroma.storage import save_context, clear_context

app = Flask(__name__)

SCRAPED_DIR = "scraped_content"


@app.route('/')
def index():
    """Landing page linking to crawler and chat UIs."""
    return render_template('index.html')


@app.route('/home', methods=['GET'])
def home_page():
    """UI page with a text box for URL that calls POST /crawl via JS."""
    return render_template('home.html')


@app.route('/chat', methods=['GET'])
def chat_page():
    """Chat UI page that talks to POST /ask via JS."""
    return render_template('chat.html')


@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    # Each crawl should start from a clean slate: clear previous files and context
    reset_state()

    # Delete previously scraped content
    if os.path.exists(SCRAPED_DIR):
        shutil.rmtree(SCRAPED_DIR)

    # Clear any previously stored embeddings/context
    clear_context()

    # Start a fresh crawl
    saved_files = crawler(url=url)

    # Handle cases where nothing useful was scraped
    if not saved_files:
        return jsonify({
            "error": "No suitable content found to crawl for this URL. The pages may be too short or inaccessible."
        }), 400

    vector = create_embeddings_per_file(saved_files)
    embeddings, chunks, metadata = vector

    success = save_context(embeddings=embeddings, chunks=chunks, metadata=metadata)
    if success:
        return jsonify({"message": "Crawling and embedding completed successfully"}), 200
    else:
        return jsonify({"error": "Failed to save context"}), 500


@app.route('/crawl/cancel', methods=['POST'])
def cancel_crawl():
    """Cancel an in-progress crawl and remove any partially created data."""
    # Signal the crawler to stop at the next opportunity
    request_cancel()

    # Remove any scraped files and embeddings to roll back state
    if os.path.exists(SCRAPED_DIR):
        shutil.rmtree(SCRAPED_DIR)

    clear_context()
    reset_state()

    return jsonify({"message": "Crawling cancelled and previous data cleared."}), 200


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

if __name__ == "__main__":
    app.run()
