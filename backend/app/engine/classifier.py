import re
from app.engine.transformer import TrainingTransformer

class SceneClassifier:
    """Classifies segmented topics and slide chunks into specific scene archetypes."""
    
    @staticmethod
    def classify_type(slide_data, topic_index, total_topics):
        title = slide_data["title"]
        bullets = slide_data.get("bullets", [])
        content_str = " ".join(bullets)
        
        # 1. Intro (Only if it's the start AND has very little content)
        # This prevents "Title-less" PDFs from hiding their first section's content.
        if topic_index == 0:
            if not bullets and not slide_data.get("tables"):
                return "IntroScene"
            # Fallback to ConceptScene if there's actual content to show
        
        # 2. Critical/Warning
        warning_keywords = [r"critical", r"warning", r"important", r"danger", r"hazard", r"must", r"do not"]
        if any(re.search(kw, content_str, re.I) for kw in warning_keywords) or any(re.search(kw, title, re.I) for kw in warning_keywords):
            return "WarningScene"
            
        # 3. Table (Only if substantial and No Bullets)
        if slide_data.get("tables") and not bullets:
            return "TableScene"
            
        # 4. Summary
        if topic_index == total_topics - 1:
            return "SummaryScene"
            
        # 5. Standard Concept
        return "ConceptScene"

    @staticmethod
    def to_ir(topics):
        """Converts raw topics into a sequence of training-ready slides (SIR)."""
        scene_list = []
        transformer = TrainingTransformer()
        total_topics = len(topics)
        
        global_idx = 0
        for t_idx, topic in enumerate(topics):
            # Transform raw topic into 1 or more slide chunks
            slide_chunks = transformer.transform_to_slides(topic)
            
            for chunk in slide_chunks:
                stype = SceneClassifier.classify_type(chunk, t_idx, total_topics)
                
                # Narration for this specific slide chunk
                narration = SceneClassifier._prepare_narration(chunk)
                
                scene_list.append({
                    "id": global_idx,
                    "title": chunk["title"],
                    "type": stype,
                    "bullets": chunk["bullets"],
                    "tables": chunk["tables"],
                    "narration": narration
                })
                global_idx += 1
                
        return scene_list

    @staticmethod
    def _prepare_narration(slide_chunk):
        """Generates narration text for a specific slide chunk."""
        title = slide_chunk["title"]
        bullets = slide_chunk["bullets"]
        
        if not bullets:
            return f"Now let's look at {title}."
            
        narration = f"{title}. "
        for b in bullets:
            # Re-read bullets naturally
            narration += f"{b}. "
            
        return narration.strip()
