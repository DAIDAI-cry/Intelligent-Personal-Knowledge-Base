from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from typing import Dict
from .myutils import request_OpenRouter,google_search_image,get_context,topics_query,new_image
from requests.exceptions import RequestException
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status, generics, permissions
import json
from .tasks import generate_notes_task
from celery.result import AsyncResult
from NoteCraft_backend.celery import app
from .ai_module import query_ai
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class HelloWorldView(APIView):
    def get(self, request:Request)->Response:
        return Response({"message": "Hello, world!"})

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(conversation_id=conversation_id, conversation__user=self.request.user).order_by('created_at')

class AskAIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        query = request.data.get("query", "")
        conversation_id = request.data.get("conversation_id")

        if not query:
            return Response({"error": "Query is required"}, status=400)
        
        user = request.user
        
        # Handle Conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                return Response({"error": "Conversation not found"}, status=404)
        else:
            # Create new conversation with the first query as title (truncated)
            title = query[:30] + "..." if len(query) > 30 else query
            conversation = Conversation.objects.create(user=user, title=title)

        # Save User Message
        Message.objects.create(conversation=conversation, role='user', content=query)
        
        try:
            result = query_ai(query)
            
            ai_content = result.get('answer', '') if isinstance(result, dict) else str(result)
            
            # Save AI Message
            Message.objects.create(conversation=conversation, role='assistant', content=ai_content)
            
            response_data = {
                "answer": ai_content,
                "conversation_id": conversation.id,
                "sources": result.get('sources', [])
            }
            return Response(response_data)
        except Exception as e:
            # Even if AI fails, return the conversation_id so the frontend can update the list
            return Response({
                "error": str(e),
                "conversation_id": conversation.id,
                "answer": "抱歉，我现在无法连接到大脑，请稍后再试。"
            }, status=500)

class GenerateNoteView(APIView):
    def post(self, request:Request) -> Response:
        params = request.data.get("params", {}) # type: ignore
        query = params.get("query", "") # type: ignore
        if not query:
            return Response({"error": "query parameter is required"}, status=400)

        prompt_1 = query + topics_query

        task = generate_notes_task.delay(prompt_1)
        return Response({"message": "Note generation started", "task_id": task.id})

class TaskStatusView(APIView):
    def get(self, request:Request, task_id):
        result = AsyncResult(task_id)
        return Response({
            "task_id": task_id,
            "state": result.state,
            "result": result.result if result.ready() else None
        })


class ModifyTextView(APIView):
    def post(self,request:Request)->Response:
        change_text:str=request.data.get("text") # type: ignore
        print(change_text)
        try:
            response:str=request_OpenRouter(change_text+"rework this part of text to get more clarity and elaborate the ouput should be in ```text box the new content should not be more than 3 times original lenght")
            start:int = response.find("```text") + len("```text")
            end:int = response.find("```", start)
            new_text:str = response[start:end].strip()
            return Response({"message": "Text modified successfully","modifiedContent": new_text})
        except (TypeError,RequestException) as e:
            return Response({"message": "Error in response from OpenRouter","error": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModifyImageView(APIView):
    def post(self,request:Request)->Response:
        change_image:str=request.data.get("imgText") # type: ignore
        try:
            new_image_url:str=new_image(change_image)
            return Response({"message": "Image modified successfully","modifiedContent": f"![{change_image}]({new_image_url})"})
        except (TypeError,RequestException) as e:
            return Response({"message": "Error in response from OpenRouter","error": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class ProxyImageView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the image URL from the query parameters
        image_url = request.query_params.get('url', None)
        if not image_url:
            return Response({"error": "Image URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the image from the external URL
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            # Set CORS headers
            http_response = HttpResponse(
                response.raw,
                content_type=response.headers.get('Content-Type')
            )
            http_response['Access-Control-Allow-Origin'] = '*'

            return http_response

        except requests.RequestException as e:
            return Response({"error": f"Failed to fetch image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 修改

class CancelTaskView(APIView):
    def post(self, request: Request):
        task_id = request.data.get("task_id")  # type: ignore
        if not task_id:
            return Response({"error": "Missing task_id"}, status=400)
        app.control.revoke(task_id, terminate=True)  
        return Response({"message": "Task cancelled successfully"}, status=200)
