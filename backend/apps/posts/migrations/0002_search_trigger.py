# 📁 Location: backend/apps/posts/migrations/0002_search_trigger.py
#
# This migration installs a PostgreSQL trigger that automatically keeps
# the search_vector column in sync whenever a post's content is saved.
#
# Without this trigger, full-text search (used in the /posts/search/ endpoint)
# returns zero results because search_vector is never populated.
#
# How it works:
#   1. A PostgreSQL function reads the post's content field
#   2. It converts that text to a tsvector (tokenised, stemmed, weighted)
#   3. A trigger fires that function BEFORE every INSERT or UPDATE on posts_post
#   4. Django's search_vector field is kept in sync transparently
#
# To reverse this migration:  uv run manage.py migrate posts 0001
# To re-apply:                uv run manage.py migrate posts 0002

from django.db import migrations

FORWARD_SQL = """
CREATE OR REPLACE FUNCTION posts_post_search_vector_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.content, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_post_search_vector_trigger
BEFORE INSERT OR UPDATE ON posts_post
FOR EACH ROW EXECUTE FUNCTION posts_post_search_vector_update();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS posts_post_search_vector_trigger ON posts_post;
DROP FUNCTION IF EXISTS posts_post_search_vector_update();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]