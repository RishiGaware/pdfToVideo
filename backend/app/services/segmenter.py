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
            "title": None,
            "content": [],
            "tables": [],
            "heading_page": 0
        }

        # Phase 1: Build topics from text elements only (no table assignment yet)
        for el in self.elements:
            if el["type"] in ["title", "heading"]:
                # Trigger topic boundary if we already have a title or we have content
                if current_topic["title"] is not None or len(current_topic["content"]) > 0:
                    topics.append(current_topic)
                    current_topic = {
                        "title": None,
                        "content": [],
                        "tables": [],
                        "heading_page": el["page"],
                        "heading_y": el.get("bbox", [0, 0])[1]  # Store y-pos
                    }
                current_topic["title"] = el["text"]
                current_topic["heading_page"] = el["page"]
                current_topic["heading_y"] = el.get("bbox", [0, 0])[1]
            elif el["type"] == "subheading":
                current_topic["content"].append(f"▸ {el['text']}:")
            else:
                current_topic["content"].append(el["text"])

        if current_topic["content"] or current_topic["title"]:
            topics.append(current_topic)

        # Phase 2: Assign each table to its closest preceding topic
        sorted_tables = sorted(self.tables, key=lambda t: (t["page"], t["bbox"][1]))
        
        for table in sorted_tables:
            t_page = table["page"]
            t_y = table["bbox"][1]
            
            best_idx = 0
            for i, topic in enumerate(topics):
                if topic["heading_page"] < t_page:
                    best_idx = i
                elif topic["heading_page"] == t_page and topic.get("heading_y", 0) <= t_y:
                    best_idx = i
                elif topic["heading_page"] > t_page:
                    break
            
            topics[best_idx]["tables"].append(table["data"])

        # Clean up the tracking fields
        for t in topics:
            t.pop("heading_page", None)
            t.pop("heading_y", None)

        # Merge tiny topics (e.g. just a heading with no content)
        return self._clean_topics(topics)

    def _clean_topics(self, topics):
        cleaned = []
        for t in topics:
            if not t["title"]:
                # If it's the very first topic and has no real title/content, ignore it
                if not cleaned and not t["content"] and not t["tables"]:
                    continue
                t["title"] = "Executive Summary" if not cleaned else "General Details"

            # If a topic is mostly empty, merge it with previous or discard
            if not t["content"] and not t["tables"]:
                if cleaned:
                    cleaned[-1]["title"] += " - " + t["title"]
                # Else: just discard an empty first topic
            else:
                cleaned.append(t)
        return cleaned
