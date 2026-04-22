import logging

logger = logging.getLogger(__name__)

class TopicSegmenter:
    """Segments a list of elements into logical Topics based on headings and content."""
    
    def __init__(self, elements, tables):
        self.elements = elements
        self.tables = tables

    def segment(self):
        topics = []
        current_topic = {
            "title": "Introduction",
            "content": [],
            "tables": []
        }

        # Index tables by page for easy lookup
        tables_by_page = {}
        for t in self.tables:
            page = t["page"]
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(t["data"])

        for el in self.elements:
            # Topic boundary trigger: Hard headings
            if el["type"] in ["title", "heading"] and len(current_topic["content"]) > 0:
                topics.append(current_topic)
                current_topic = {
                    "title": el["text"],
                    "content": [],
                    "tables": []
                }
                # Add tables from this page if not added already
                if el["page"] in tables_by_page:
                    current_topic["tables"].extend(tables_by_page[el["page"]])
                    del tables_by_page[el["page"]] # Avoid duplicates
            else:
                if el["type"] in ["title", "heading"]:
                    current_topic["title"] = el["text"]
                else:
                    current_topic["content"].append(el["text"])
                    # Check for tables on this page
                    if el["page"] in tables_by_page:
                        current_topic["tables"].extend(tables_by_page[el["page"]])
                        del tables_by_page[el["page"]]

        if current_topic["content"] or current_topic["tables"]:
            topics.append(current_topic)

        # Merge tiny topics (e.g. just a heading with no content)
        return self._clean_topics(topics)

    def _clean_topics(self, topics):
        cleaned = []
        for t in topics:
            # If a topic is mostly empty, merge it with previous if it's just a heading
            if not t["content"] and not t["tables"]:
                if cleaned:
                    cleaned[-1]["title"] += " - " + t["title"]
                else:
                    cleaned.append(t)
            else:
                cleaned.append(t)
        return cleaned
