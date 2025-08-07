from flask import Flask, request, render_template, jsonify, redirect, url_for
import psycopg2, requests, os

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "goldbook")
DB_USER = os.getenv("DB_USER", "golduser")
DB_PASS = os.getenv("DB_PASS", "goldpass")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/new-comment")

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

# Création table
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            comment TEXT NOT NULL,
            summary TEXT,
            sentiment TEXT,
            keywords TEXT[]
        )
        """)
        conn.commit()

def fetch_and_store_steam_reviews(app_id: str, num_per_page: int):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page={num_per_page}&language=english"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        reviews = data.get("reviews", [])
        new_comments_count = 0

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for review in reviews:
                    steamid = review.get("author", {}).get("steamid", "unknown")
                    comment_text = review.get("review", "")

                    # Vérifier doublon sur le texte exact
                    cur.execute("SELECT id FROM comments WHERE comment = %s", (comment_text,))
                    if cur.fetchone():
                        continue

                    cur.execute(
                        "INSERT INTO comments (name, comment) VALUES (%s, %s) RETURNING id",
                        (steamid, comment_text)
                    )
                    comment_id = cur.fetchone()[0]
                    conn.commit()
                    new_comments_count += 1

                    requests.post(
                        N8N_WEBHOOK_URL,
                        json={"id": comment_id, "name": steamid, "comment": comment_text},
                        auth=('admin', 'admin')
                    )

        return new_comments_count

    except Exception as e:
        print("Erreur récupération Steam ou insertion DB:", e)
        return 0

@app.route("/", methods=["GET", "POST"])
def home():
    new_count = None
    app_id = ""
    num_per_page = 10

    if request.method == "POST":
        # Récupérer app_id et num_per_page du formulaire
        app_id = request.form.get("app_id", "").strip()
        try:
            num_per_page = int(request.form.get("num_per_page", "10"))
        except ValueError:
            num_per_page = 10

        if app_id:
            new_count = fetch_and_store_steam_reviews(app_id, num_per_page)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, comment, summary, sentiment, keywords FROM comments ORDER BY id DESC")
            comments = cur.fetchall()

    return render_template("index.html", comments=comments, new_count=new_count, app_id=app_id, num_per_page=num_per_page)

@app.route("/comments/<int:id>", methods=["PUT"])
def update_comment(id):
    data = request.get_json()

    summary = data.get("résumé")
    sentiment = data.get("sentiment")
    keywords = data.get("mots_clés")  # attend un array

    if not all([summary, sentiment, keywords]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE comments
                    SET summary = %s,
                        sentiment = %s,
                        keywords = %s
                    WHERE id = %s
                    RETURNING id, name, comment, summary, sentiment, keywords
                """, (summary, sentiment, keywords, id))
                updated = cur.fetchone()
                conn.commit()

                if updated is None:
                    return jsonify({"error": "Comment not found"}), 404

        updated_comment = {
            "id": updated[0],
            "name": updated[1],
            "comment": updated[2],
            "résumé": updated[3],
            "sentiment": updated[4],
            "mots_clés": updated[5]
        }
        return jsonify(updated_comment), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_comment", methods=["POST"])
def add_comment():
    name = request.form.get("name")
    comment = request.form.get("comment")

    if not name or not comment:
        return "Nom et commentaire obligatoires", 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO comments (name, comment) VALUES (%s, %s)", (name, comment))
                conn.commit()
        return redirect(url_for('home'))
    except Exception as e:
        return f"Erreur lors de l'insertion : {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
