# tasks.py
import json
from .myutils import get_context, google_search_image, request_OpenRouter, topics_query
from celery import shared_task

@shared_task
def generate_notes_task(user_query:str) -> dict:
    try:
        # Step 1: Generate topics/keywords for RAG (using the complex prompt)
        step1_prompt = user_query + topics_query
        response_1 = request_OpenRouter(step1_prompt)
        
        # Attempt to extract JSON, fallback if fails
        try:
            start = response_1.find("```json")
            if start != -1:
                start += len("```json")
                end = response_1.find("```", start)
                json_str = response_1[start:end].strip()
                fresponse = json.loads(json_str)
                namespace = fresponse.get('namespace', 'game_mechanics')
                topics = fresponse.get('topics', user_query)
            else:
                # Try to find raw JSON object
                start = response_1.find("{")
                end = response_1.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response_1[start:end].strip()
                    fresponse = json.loads(json_str)
                    namespace = fresponse.get('namespace', 'game_mechanics')
                    topics = fresponse.get('topics', user_query)
                else:
                    raise ValueError("No JSON found")
        except Exception:
            # Fallback if JSON parsing fails
            namespace = 'game_mechanics'
            topics = user_query
        
        # Step 2: Retrieve context
        context = get_context(user_query, namespace=namespace)

        # Step 3: Generate final response (using ONLY the user's original query)
        prompt_2:str= f"""
        Role: You are an expert Challenger-rank Teamfight Tactics (Golden Spatula) coach and assistant.
        
        User Input: "{user_query}"
        
        Context (from knowledge base): {context}
        
        Instructions:
        1. Respond to the User Input directly and conversationally.
        2. If the user asks for a guide, strategy, or specific game details, use the Context to provide a comprehensive answer.
        3. If the User Input is simple (e.g., "1", "hi", "hello"), respond politely and ask how you can help with Teamfight Tactics.
        4. Do NOT generate a full strategic guide unless the user explicitly asks for one.
        5. You can use Markdown for formatting (bold, lists, headers) to make the response readable.
        6. To include images, write &&&image:(description of image)&&&. Use this only if relevant to explain a visual concept (like positioning).
        7. Keep the response language consistent with the user's input (Chinese if Chinese, English if English).
        """
        
        notes = request_OpenRouter(prompt_2)
        
        start = notes.find("```markdown")
        if start != -1:
            start += len("```markdown")
            end = notes.find("```", start)
            if end != -1:
                notes = notes[start:end].strip()
            else:
                notes = notes[start:].strip()
        else:
            notes = notes.strip()

        arr = notes.split("&&&")
        processed_notes = []
        for line in arr:
            if line.startswith("image:"):
                image_query = line.split("image:", 1)[1].strip()
                image_url = google_search_image(image_query)
                processed_notes.append(f"![{image_query}]({image_url})")
            else:
                processed_notes.append(line)

        return {"success": True, "notes": "".join(processed_notes)}
    except Exception as e:
        return {"success": False, "error": str(e)}
