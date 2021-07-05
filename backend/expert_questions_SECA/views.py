from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from SECAAlgo.models import Sessions
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from .models import Question
import ast


# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class QuestionsAndAnswers(View):
    """
    The QuestionsAndAnswers View implements three endpoints (DELETE, GET, and POST) that allow the user
    to delete questions, request questions, and finally update questions with answers. 
    """

    def delete(self, request):
        """
        The DELETE endpoint is responsible to delete the requested Question object/entry in the database.

        :param request: The HTTP request object, with query parameters session_id and question.
            session_id being the session_id and the question being the question string literal.
        :return JsonResponse: A JsonResponse object is returned if the deletion is sucessful. If the session isn't found
            then an 404 error is returned.
        """
        data = request.GET
        session_id = data.get('session_id')
        question = data.get('question')

        session = get_object_or_404(Sessions, id=session_id)

        questions = Question.objects.filter(prediction=session, question=question)[0]
        questions.delete()

        return JsonResponse({"questions":"deleted"})
    
    def get(self, request):
        """
        The GET endpoint is responsible for fetching a list of questions for the given session.

        :param request: The HTTP request object, with query parameter session_id.
        :return JsonResponse: A JsonResponse with all the Question objects are returned for the given
            session. If the given session is invalid, a 404 error is returned. 
        """
        session_id = int(request.GET.get("session_id", -1))
        session = get_object_or_404(Sessions, id=session_id)
        questions = Question.objects.filter(prediction=session)
        data = []
        for i in questions:
            obj = {}
            obj['question'] = i.question
            obj['answer'] = i.answer
            data.append(obj)
        return JsonResponse({"questions":data})
    
    def post(self, request):
        """
        The POST endpoint is responsible for adding an answer to a question.

        :param request:  The HTTP request object, with body being a JSON dictionary with three 
            key value pairs. The keys are session_id, question and answer.
            session_id key has value of the appropriate session_id
            question key has the string literal of the question that is being answered
            answer key has the string value of the answer that is to be added. 
        :return JsonResponse: A Jsonresponse is returned on success. 
        """
        byte_str = request.body
        dict_str = byte_str.decode("UTF-8")
        data = dict(ast.literal_eval(dict_str))
        if len(data['answer']) == 0:
            prediction = get_object_or_404(Sessions, id=data['session_id'])
            question = Question(question=data['question'], answer=data['answer'], prediction=prediction)
        else:
            question = Question.objects.filter(question=data['question'])[0]
            question.answer = data['answer']
        question.save()
        return JsonResponse({"questions":"success"})
