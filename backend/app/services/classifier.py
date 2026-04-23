import re
from app.services.transformer import TrainingTransformer

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
        
        # 2. Table (Only if substantial and No Bullets)
        if slide_data.get("tables") and not bullets:
            return "TableScene"
            
        # 3. Summary/Ending (Reserved but currently same as Concept)
        if topic_index == total_topics - 1:
            return "ConceptScene"
            
        # 4. Standard Concept
        return "ConceptScene"

    @staticmethod
    def to_ir(topics):
        """Converts raw topics into a sequence of training-ready slides with atomic steps."""
        scene_list = []
        transformer = TrainingTransformer()
        total_topics = len(topics)
        
        global_idx = 0
        for t_idx, topic in enumerate(topics):
            # Transform raw topic into 1 or more slide chunks
            slide_chunks = transformer.transform_to_slides(topic)
            
            for chunk in slide_chunks:
                stype = SceneClassifier.classify_type(chunk, t_idx, total_topics)
                
                # Each slide chunk is broken into atomic visual/audio steps
                steps = []
                bullets = chunk.get("bullets", [])
                
                # Step 0: Introduce the slide title
                steps.append({
                    "id": f"{global_idx}_0",
                    "narration": f"{chunk['title']}.",
                    "bullets_to_show": [],
                    "has_tables": chunk.get("has_tables", False),
                    "tables": chunk.get("tables", [])
                })
                
                # Steps 1-N: Narrate each bullet as it appears
                for b_idx, bullet in enumerate(bullets):
                    steps.append({
                        "id": f"{global_idx}_{b_idx+1}",
                        "narration": f"{bullet}.",
                        "bullets_to_show": bullets[:b_idx+1],
                        "has_tables": chunk.get("has_tables", False),
                        "tables": chunk.get("tables", [])
                    })
                
                scene_list.append({
                    "id": global_idx,
                    "title": chunk["title"],
                    "type": stype,
                    "steps": steps
                })
                global_idx += 1
                
        return scene_list
